import re
import json
import time
import logging
from typing import Dict, Optional, Tuple, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

requests = None
BeautifulSoup = None

def _ensure_deps():
    global requests, BeautifulSoup
    if requests is None:
        import requests as _req
        requests = _req
    if BeautifulSoup is None:
        from bs4 import BeautifulSoup as _bs
        BeautifulSoup = _bs


class WebEnricher:

    def __init__(self):
        self._ddgs = None
        self._requests = None
        self._bs4 = None
        self._available = False
        self._cache = {}
        self._session = None
        self._deps_initialized = False

    def _ensure_init(self):
        if self._deps_initialized:
            return
        self._deps_initialized = True
        _ensure_deps()
        self._requests = requests
        self._bs4 = BeautifulSoup
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self._session.mount("http://", requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=1))
        self._session.mount("https://", requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=1))
        try:
            from ddgs import DDGS
            self._ddgs = DDGS()
            self._available = True
        except Exception:
            try:
                from duckduckgo_search import DDGS
                self._ddgs = DDGS()
                self._available = True
            except Exception as e:
                logger.warning("DuckDuckGo search unavailable: %s", e)
                self._available = False

    @property
    def is_available(self):
        self._ensure_init()
        return self._available

    def search_and_scrape(self, brand, mpn):
        self._ensure_init()
        if not self._available or not mpn or not mpn.strip():
            return None, {}
        cache_key = "%s|%s" % (brand, mpn)
        if cache_key in self._cache:
            return self._cache[cache_key]
        all_urls = self._search_urls(brand, mpn)
        if not all_urls:
            self._cache[cache_key] = (None, {})
            return None, {}
        best_specs = {}
        best_url = all_urls[0]
        for url in all_urls[:1]:  # Only scrape top result for speed
            try:
                html, text = self._fetch_page(url)
                if not text or len(text) < 200:
                    continue
                specs = {}
                if html:
                    specs = self._extract_from_json_ld(html)
                    if not specs:
                        specs = self._extract_from_meta_tags(html)
                    ts = self._extract_from_tables(html)
                    for k, v in ts.items():
                        if k not in specs:
                            specs[k] = v
                ts2 = self._extract_from_text(text)
                for k, v in ts2.items():
                    if k not in specs:
                        specs[k] = v
                desc = self._extract_description(text)
                if desc:
                    specs["_description"] = desc
                if len(specs) > len(best_specs):
                    best_specs = specs
                    best_url = url
                if len(specs) >= 3:  # Reduced from 5 to 3 for speed
                    break
            except Exception as e:
                logger.debug("Scrape fail %s: %s", url, e)
                continue
        self._cache[cache_key] = (best_url, best_specs)
        return best_url, best_specs

    def _search_urls(self, brand, mpn):
        query = "%s %s specifications" % (brand, mpn)  # Single query instead of 2
        all_urls = []
        seen = set()
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(lambda: list(self._ddgs.text(query, max_results=3)))
                results = future.result(timeout=5)
            for r in results:
                url = r.get("href", "") or r.get("link", "")
                if url and url not in seen and self._is_useful_url(url):
                    seen.add(url)
                    all_urls.append(url)
        except Exception as e:
            logger.debug("Search fail: %s", e)
        all_urls.sort(key=lambda u: self._rank_url(u))
        return all_urls

    def _fetch_page(self, url):
        if not url:
            return None, None
        try:
            resp = self._session.get(url, timeout=1.5)
            resp.raise_for_status()
            html = resp.text
            soup = self._bs4(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "aside"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r'\s+', ' ', text)
            return html, text[:8000]  # Reduced for speed
        except Exception as e:
            logger.debug("Fetch fail %s: %s", url, e)
            return None, None

    def _extract_from_json_ld(self, html):
        specs = {}
        try:
            soup = self._bs4(html, "html.parser")
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        if "Product" not in str(item.get("@type", "")):
                            continue
                        if "name" in item:
                            specs["Model"] = item["name"]
                        if "brand" in item:
                            bd = item["brand"]
                            specs["Brand"] = bd.get("name", "") if isinstance(bd, dict) else str(bd)
                        if "additionalProperty" in item:
                            for prop in item["additionalProperty"]:
                                if isinstance(prop, dict):
                                    n = prop.get("name", "")
                                    v = prop.get("value", "")
                                    if n and v:
                                        specs[n] = v
                        for dim in ["weight", "depth", "width", "height"]:
                            if dim in item and isinstance(item[dim], dict):
                                d = item[dim]
                                specs[dim.title()] = "%s %s" % (d.get("value", ""), d.get("unitCode", ""))
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception:
            pass
        return specs

    def _extract_from_meta_tags(self, html):
        specs = {}
        try:
            soup = self._bs4(html, "html.parser")
            for meta in soup.find_all("meta"):
                name = (meta.get("name", "") or meta.get("property", "")).lower()
                content = meta.get("content", "")
                if not name or not content:
                    continue
                if "product" in name and "title" in name:
                    specs["Model"] = content
                elif "product" in name and "brand" in name:
                    specs["Brand"] = content
                elif "description" in name and len(content) > 20:
                    specs["_description"] = content
        except Exception:
            pass
        return specs

    def _extract_from_tables(self, html):
        specs = {}
        try:
            soup = self._bs4(html, "html.parser")
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        if label and value and len(label) < 50 and len(value) < 100:
                            mapped = self._map_spec_label(label)
                            if mapped:
                                specs[mapped] = value
        except Exception:
            pass
        return specs

    def _map_spec_label(self, label):
        label = label.lower().strip()
        m = {
            "voltage": "Voltage", "voltage rating": "Voltage", "input voltage": "Voltage",
            "amperage": "Amperage", "amps": "Amperage", "current": "Amperage",
            "wattage": "Wattage", "power": "Wattage", "watts": "Wattage",
            "sound level": "Sound Level", "noise level": "Sound Level", "dba": "Sound Level",
            "capacity": "Capacity", "cu. ft.": "Capacity", "cubic feet": "Capacity",
            "weight": "Weight", "product weight": "Weight",
            "dimensions": "Dimensions", "product dimensions": "Dimensions",
            "width": "Width", "height": "Height", "depth": "Depth",
            "depth with door open": "Depth With Door Open",
            "color": "Color", "finish": "Finish", "material": "Material",
            "series": "Series", "model number": "Model", "model": "Model",
            "mounting": "Mounting Type", "mounting type": "Mounting Type",
            "installation type": "Mounting Type",
            "wash cycles": "Number of Wash Cycles", "number of cycles": "Number of Wash Cycles",
            "energy star": "Energy Star",
            "fuel type": "Fuel Type", "fuel": "Fuel Type",
            "bulb type": "Bulb Type", "light bulb": "Bulb Type",
            "lumens": "Lumens", "color temperature": "Color Temperature",
            "dimmable": "Dimmable", "cord length": "Cord Length",
            "certifications": "Certifications", "warranty": "Warranty",
            "blade span": "Blade Span", "number of blades": "Number of Blades",
            "airflow": "Airflow", "cfm": "Airflow",
            "motor type": "Motor Type", "shade material": "Shade Material",
            "grit": "Grit", "diameter": "Diameter", "arbor size": "Arbor Size",
            "kerf": "Kerf", "teeth": "Tooth Count", "tpi": "Tooth Count",
            "shank": "Shank", "shank size": "Shank Size",
            "length": "Length", "overall length": "Overall Length",
            "thread size": "Thread Size", "gauge": "Gauge",
            "nema": "NEMA Rating", "ip rating": "IP Rating",
            "minimum height": "Minimum Height", "maximum height": "Maximum Height",
            "plug type": "Plug Type",
        }
        for key, mapped in m.items():
            if key in label:
                return mapped
        return None

    def _extract_description(self, text):
        sentences = re.split(r'[.]\s+', text[:3000])
        for s in sentences:
            s = s.strip()
            if 30 < len(s) < 200 and any(w in s.lower() for w in [
                "dishwasher", "dryer", "washer", "range", "oven", "refrigerator",
                "microwave", "freezer", "disposal", "sanding", "drill", "saw",
                "blade", "disc", "light", "fan", "valve", "faucet", "pipe",
                "deck", "trim", "rail", "post", "screw", "nail", "bolt",
                "sanding belt", "grinder", "polisher",
            ]):
                return s
        return ""

    def _extract_from_text(self, text):
        if not text:
            return {}
        specs = {}

        for pat in [
            re.compile(r'(?:Voltage|Volts?)[:\s]*(\d{2,3})\s*[Vv]?', re.I),
            re.compile(r'(\d{2,3})\s*[Vv]\b', re.I),
        ]:
            m = pat.search(text)
            if m:
                specs["Voltage"] = "%s V" % m.group(1)
                break

        for pat in [
            re.compile(r'(?:Amperage|Amps?)[:\s]*(\d+(?:\.\d+)?)\s*[Aa]?', re.I),
            re.compile(r'(\d+(?:\.\d+)?)\s*[Aa](?:mps?)?\b', re.I),
        ]:
            m = pat.search(text)
            if m:
                val = float(m.group(1))
                if val < 100:
                    specs["Amperage"] = "%s A" % m.group(1)
                    break

        for pat in [
            re.compile(r'(?:Wattage|Watts?)[:\s]*(\d+(?:\.\d+)?)\s*[Ww]?', re.I),
            re.compile(r'(\d+(?:\.\d+)?)\s*[Ww](?:atts?)?\b', re.I),
        ]:
            m = pat.search(text)
            if m:
                specs["Wattage"] = "%s W" % m.group(1)
                break

        for pat in [
            re.compile(r'(\d+(?:\.\d+)?)\s*d[Bb][Aa]', re.I),
            re.compile(r'(?:Sound|Noise)[:\s]*(\d+(?:\.\d+)?)\s*d[Bb]', re.I),
        ]:
            m = pat.search(text)
            if m:
                specs["Sound Level"] = "%s dBA" % m.group(1)
                break

        for pat in [
            re.compile(r'(?:Capacity)[:\s]*(\d+(?:\.\d+)?)\s*(?:cu\.?\s*ft|cubic)', re.I),
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:cu\.?\s*ft|cubic\s*feet)', re.I),
        ]:
            m = pat.search(text)
            if m:
                specs["Capacity"] = "%s cu. ft." % m.group(1)
                break

        for pat in [
            re.compile(r'(?:Weight)[:\s]*(\d+(?:\.\d+)?)\s*(?:lb|lbs)', re.I),
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:lb|lbs)\b', re.I),
        ]:
            m = pat.search(text)
            if m:
                val = float(m.group(1))
                if 1 < val < 500:
                    specs["Weight"] = "%s lb" % m.group(1)
                    break

        for pat in [
            re.compile(r'(?:Mounting|Installation)\s*(?:Type)?[:\s]*(Leg|Wall|Deck|Under.?counter|Built.?in|Freestanding|Drop.?in|Top.?mount|Flush)', re.I),
            re.compile(r'(Leg|Wall|Deck|Under.?counter|Built.?in|Freestanding|Drop.?in|Top.?mount|Flush)\s*(?:Mount|Install)', re.I),
        ]:
            m = pat.search(text)
            if m:
                specs["Mounting Type"] = "%s Mounting" % m.group(1)
                break

        for pat in [
            re.compile(r'(\d+)\s*(?:wash\s*)?cycles?', re.I),
            re.compile(r'Cycles[:\s]*(\d+)', re.I),
        ]:
            m = pat.search(text)
            if m:
                specs["Number of Wash Cycles"] = m.group(1)
                break

        for pat in [
            re.compile(r'(?:Color|Finish)[:\s]*(Stainless\s*Steel|Black\s*Stainless|White|Black|Slate|Platinum|Gray|Graphite|Bisque)', re.I),
            re.compile(r'\b(Stainless\s*Steel|Black\s*Stainless|Slate|Platinum|Graphite|Bisque)\b', re.I),
        ]:
            m = pat.search(text)
            if m:
                specs["Color"] = m.group(1).title()
                break

        m = re.search(r'(?:Series)[:\s]*([\w\s]+?)(?:\s*Series)?\b', text, re.I)
        if m:
            s = m.group(1).strip()
            if s and len(s) < 30:
                specs["Series"] = s

        if re.search(r'(?:Energy\s*Star|ENERGY\s*STAR)', text, re.I):
            specs["Energy Star"] = "Yes"

        m = re.search(r'(?:Fuel\s*Type|Power\s*Source)[:\s]*(Gas|Electric|Dual\s*Fuel|Battery|Solar)', text, re.I)
        if m:
            specs["Fuel Type"] = m.group(1)

        m = re.search(r'(?:Lumens?)[:\s]*(\d+)', text, re.I)
        if m:
            val = int(m.group(1))
            if 100 < val < 50000:
                specs["Lumens"] = "%s lm" % m.group(1)

        m = re.search(r'(?:Color\s*Temperature|CCT|Kelvin)[:\s]*(\d{4,5})\s*K?', text, re.I)
        if m:
            specs["Color Temperature"] = "%sK" % m.group(1)

        if re.search(r'\b(dimmable)\b', text, re.I):
            specs["Dimmable"] = "Yes"

        m = re.search(r'(?:Grit|Abrasives?)[:\s]*(\d+)', text, re.I)
        if m:
            specs["Grit"] = m.group(1)

        m = re.search(r'(?:CFM|Airflow)[:\s]*(\d+)', text, re.I)
        if m:
            val = int(m.group(1))
            if 100 < val < 50000:
                specs["Airflow"] = "%s CFM" % m.group(1)

        return specs

    def _is_useful_url(self, url):
        skip = ['youtube.com', 'facebook.com', 'twitter.com', 'instagram.com',
                'pinterest.com', 'reddit.com', 'tiktok.com', 'linkedin.com',
                'wikipedia.org']
        url_lower = url.lower()
        for s in skip:
            if s in url_lower:
                return False
        return True

    def _rank_url(self, url):
        url_lower = url.lower()
        preferred = [
            'ajmadison.com', 'us-appliance.com', 'sears.com', 'plessers.com',
            'webstaurantstore.com', 'partselect.com', 'repairclinic.com',
        ]
        for p in preferred:
            if p in url_lower:
                return 0
        if url_lower.endswith('.pdf'):
            return 1
        if any(d in url_lower for d in ['manuales.ca', 'manualslib.com']):
            return 2
        return 3
