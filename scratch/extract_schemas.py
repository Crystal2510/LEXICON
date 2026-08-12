"""
extract_schemas.py
Reads real manufacturer PDFs and writes validated schema JSON files.
Every min/max value is sourced from actual PDF content.
"""

import fitz  # PyMuPDF
import re
import json
import sys
from pathlib import Path

PDF_DIR = Path(r"C:\Hackathon\Unilog\data\raw\real_manufacturer")
SCHEMA_DIR = Path(r"C:\Hackathon\Unilog\data\schemas")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Return list of (page_number_1indexed, page_text) for every page."""
    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc, start=1):
        pages.append((i, page.get_text()))
    doc.close()
    return pages


def find_numbers_near_keyword(pages, keyword_pattern, context_chars=300):
    """
    Search every page for keyword_pattern; extract all floats within
    context_chars characters after each match.
    Returns list of (value_float, page_no, snippet).
    """
    results = []
    kw_re = re.compile(keyword_pattern, re.IGNORECASE)
    num_re = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")
    for page_no, text in pages:
        for m in kw_re.finditer(text):
            snippet = text[m.start(): m.start() + context_chars]
            for n in num_re.findall(snippet):
                val = float(n.replace(",", "."))
                results.append((val, page_no, snippet[:120].replace("\n", " ")))
    return results


def scan_table_column(pages, col_header_pattern, context_lines=2):
    """
    Find column headers and harvest numbers from surrounding lines.
    Returns list of (value_float, page_no, snippet).
    """
    results = []
    hdr_re = re.compile(col_header_pattern, re.IGNORECASE)
    num_re = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")
    for page_no, text in pages:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if hdr_re.search(line):
                start = max(0, i - context_lines)
                end   = min(len(lines), i + context_lines + 1)
                block = "\n".join(lines[start:end])
                for n in num_re.findall(block):
                    val = float(n.replace(",", "."))
                    results.append((val, page_no, block[:120].replace("\n", " ")))
    return results


def safe_minmax(values, lo_bound=None, hi_bound=None):
    """Filter to plausible range then return (min, max)."""
    filtered = [v for v in values
                if (lo_bound is None or v >= lo_bound)
                and (hi_bound is None or v <= hi_bound)]
    if not filtered:
        return None, None
    return min(filtered), max(filtered)


def record_source(tag, values_pages, lo=None, hi=None):
    """
    Given list of (val, page_no, snippet), filter and report the
    min/max with their source page.
    """
    filtered = [(v, p, s) for v, p, s in values_pages
                if (lo is None or v >= lo) and (hi is None or v <= hi)]
    if not filtered:
        return None, None, [], []
    mn = min(filtered, key=lambda x: x[0])
    mx = max(filtered, key=lambda x: x[0])
    return mn[0], mx[0], mn, mx


# ─────────────────────────────────────────────────────────────────────────────
# BALL BEARINGS
# ─────────────────────────────────────────────────────────────────────────────

BEARING_PDFS = [
    "SKF-Rolling-Bearings.pdf",
    "Timken-Deep-Groove-Ball-Bearings.pdf",
    "Timken-Cylindrical-Roller-Bearing-Catalog.pdf",
    "Timken-Tapered-Roller-Bearing-Catalog.pdf",
    "Timken-Corrosion-Resistant-Mounted-Ball-Bearings.pdf",
    "Timken-Miniature-Thin-Section-Bearings.pdf",
]

def extract_bearing_data():
    print("\n" + "="*70)
    print("BALL BEARINGS — extracting from PDFs …")
    print("="*70)

    all_bore, all_od, all_width = [], [], []
    all_dyn, all_stat = [], []
    materials_found = set()

    source_info = {}  # field -> (min_val, min_page, min_file, max_val, max_page, max_file)

    for fname in BEARING_PDFS:
        path = PDF_DIR / fname
        if not path.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        print(f"\n  Reading {fname} …")
        pages = extract_text_pages(path)
        print(f"    Pages: {len(pages)}")

        # ── Bore diameter (d, mm) ──────────────────────────────────────────
        # Column headers in bearing tables are usually "d", "d mm", or "Bore"
        bore_hits = []
        num_re = re.compile(r"\b(\d+(?:\.\d+)?)\b")
        bore_hdr = re.compile(r"\b(d\s*mm|bore\s*diameter|bore\s*dia|^d\b)", re.IGNORECASE | re.MULTILINE)
        for page_no, text in pages:
            lines = text.split("\n")
            in_table = False
            for i, line in enumerate(lines):
                if bore_hdr.search(line):
                    in_table = True
                if in_table:
                    nums = num_re.findall(line)
                    for n in nums:
                        v = float(n)
                        if 0.5 <= v <= 2000:   # plausible bore range
                            bore_hits.append((v, page_no, fname, line[:80]))
                    # stop after 10 lines of table body
                    if in_table and i > 0 and line.strip() == "":
                        in_table = False

        # Also grab numbers from lines that look like dimension rows
        # (Pattern: lines with 3–6 numbers separated by spaces — typical dim table row)
        dim_row = re.compile(r"^\s*(\d[\d.]*)\s+(\d[\d.]*)\s+(\d[\d.]*)")
        for page_no, text in pages:
            for line in text.split("\n"):
                m = dim_row.match(line)
                if m:
                    vals = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", line)]
                    if len(vals) >= 3:
                        # heuristic: first col = d (bore), second = D (OD), third = B (width)
                        d, D, B = vals[0], vals[1], vals[2]
                        if 0.5 <= d <= 2000 and d < D:
                            bore_hits.append((d, page_no, fname, line[:80]))
                            all_od.append((D, page_no, fname, line[:80]))
                            if 0.5 <= B <= 500:
                                all_width.append((B, page_no, fname, line[:80]))

        all_bore.extend(bore_hits)

        # ── Dynamic load rating (C, kN) ────────────────────────────────────
        c_hits = find_numbers_near_keyword(pages, r"\bC\s*=|\bdynamic\s+load\b|basic\s+dynamic", 200)
        # filter to plausible kN range
        for v, pg, snip in c_hits:
            if 0.01 <= v <= 100000:
                all_dyn.append((v, pg, fname, snip))

        # Also look for kN column headers
        kn_hdr = re.compile(r"\bkN\b", re.IGNORECASE)
        for page_no, text in pages:
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if kn_hdr.search(line):
                    # grab next 20 lines
                    block = lines[i:i+20]
                    for bl in block:
                        nums = re.findall(r"\b(\d+(?:\.\d+)?)\b", bl)
                        for n in nums:
                            v = float(n)
                            if 0.01 <= v <= 50000:
                                all_dyn.append((v, page_no, fname, bl[:80]))

        # ── Static load rating (C0, kN) ────────────────────────────────────
        c0_hits = find_numbers_near_keyword(pages, r"\bC0\b|\bstatic\s+load\b|basic\s+static", 200)
        for v, pg, snip in c0_hits:
            if 0.01 <= v <= 100000:
                all_stat.append((v, pg, fname, snip))

        # ── Materials ──────────────────────────────────────────────────────
        mat_patterns = {
            "chrome_steel":       r"chrome[\s\-]steel|chromium[\s\-]steel|52100",
            "stainless_steel":    r"stainless[\s\-]steel|AISI\s*440|corrosion[\s\-]resistant",
            "ceramic_hybrid":     r"ceramic|hybrid\s+bearing|Si3N4|silicon\s+nitride",
            "brass":              r"\bbrass\b",
            "polyamide":          r"polyamide|nylon|PA66",
            "carbon_chromium":    r"carbon[\s\-]chromium",
        }
        full_text = " ".join(t for _, t in pages)
        for mat, pat in mat_patterns.items():
            if re.search(pat, full_text, re.IGNORECASE):
                materials_found.add(mat)
                print(f"    Material found: {mat}")

    # ── Compute final min/max ──────────────────────────────────────────────
    print("\n  Computing ranges …")

    def best_range(data, lo, hi, label):
        filtered = [(v, pg, fn, s) for v, pg, fn, s in data if lo <= v <= hi]
        if not filtered:
            print(f"    [{label}] No values found in range [{lo}, {hi}]")
            return None, None, None, None, None, None
        mn = min(filtered, key=lambda x: x[0])
        mx = max(filtered, key=lambda x: x[0])
        print(f"    [{label}] min={mn[0]} (p.{mn[1]} {mn[2]})  max={mx[0]} (p.{mx[1]} {mx[2]})")
        return mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]

    bore_min, bore_min_pg, bore_min_f, bore_max, bore_max_pg, bore_max_f = \
        best_range(all_bore, 0.5, 2000, "bore_diameter")

    od_min, od_min_pg, od_min_f, od_max, od_max_pg, od_max_f = \
        best_range(all_od, 1.0, 4000, "outer_diameter")

    w_min, w_min_pg, w_min_f, w_max, w_max_pg, w_max_f = \
        best_range(all_width, 0.5, 500, "width")

    # Dynamic load: use tighter filter — values must be in kN, typical range 0.05–5000 kN
    dyn_min, dyn_min_pg, dyn_min_f, dyn_max, dyn_max_pg, dyn_max_f = \
        best_range(all_dyn, 0.05, 5000, "load_rating_dynamic")

    stat_min, stat_min_pg, stat_min_f, stat_max, stat_max_pg, stat_max_f = \
        best_range(all_stat, 0.01, 5000, "load_rating_static")

    summary = {
        "bore_diameter":        (bore_min, bore_min_pg, bore_min_f, bore_max, bore_max_pg, bore_max_f),
        "outer_diameter":       (od_min,   od_min_pg,   od_min_f,   od_max,   od_max_pg,   od_max_f),
        "width":                (w_min,    w_min_pg,    w_min_f,    w_max,    w_max_pg,    w_max_f),
        "load_rating_dynamic":  (dyn_min,  dyn_min_pg,  dyn_min_f,  dyn_max,  dyn_max_pg,  dyn_max_f),
        "load_rating_static":   (stat_min, stat_min_pg, stat_min_f, stat_max, stat_max_pg, stat_max_f),
    }
    return summary, sorted(materials_found)


# ─────────────────────────────────────────────────────────────────────────────
# CENTRIFUGAL PUMPS
# ─────────────────────────────────────────────────────────────────────────────

PUMP_PDFS = [
    "Grundfos-CR-CRI-CRN-Data-Booklet.pdf",
    "Grundfos-HS-Data-Booklet.pdf",
]

def extract_pump_data():
    print("\n" + "="*70)
    print("CENTRIFUGAL PUMPS — extracting from PDFs …")
    print("="*70)

    all_flow, all_head, all_power = [], [], []
    materials_found = set()

    for fname in PUMP_PDFS:
        path = PDF_DIR / fname
        if not path.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        print(f"\n  Reading {fname} …")
        pages = extract_text_pages(path)
        print(f"    Pages: {len(pages)}")

        full_text = " ".join(t for _, t in pages)

        # ── Flow rate (Q, m3/h) ────────────────────────────────────────────
        # Look for "m³/h" or "m3/h" patterns
        flow_re = re.compile(
            r"(\d+(?:[.,]\d+)?)\s*(?:m[³3]/h|m3/h)", re.IGNORECASE
        )
        for page_no, text in pages:
            for m in flow_re.finditer(text):
                v = float(m.group(1).replace(",", "."))
                if 0.01 <= v <= 5000:
                    all_flow.append((v, page_no, fname, m.group(0)[:60]))

        # Also look for Q= patterns
        q_re = re.compile(r"Q\s*[=:]\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE)
        for page_no, text in pages:
            for m in q_re.finditer(text):
                v = float(m.group(1).replace(",", "."))
                if 0.01 <= v <= 5000:
                    all_flow.append((v, page_no, fname, m.group(0)[:60]))

        # Column-based: look for "Q" header then grab numbers in next lines
        for page_no, text in pages:
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if re.search(r"\bQ\s*\[?m[³3]", line, re.IGNORECASE):
                    for bl in lines[i+1:i+30]:
                        for n in re.findall(r"\b(\d+(?:\.\d+)?)\b", bl):
                            v = float(n)
                            if 0.01 <= v <= 5000:
                                all_flow.append((v, page_no, fname, bl[:60]))

        # ── Head (H, m) ────────────────────────────────────────────────────
        head_re = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\b", re.IGNORECASE)
        # Lines explicitly mentioning head or H= patterns
        for page_no, text in pages:
            lines = text.split("\n")
            for line in lines:
                if re.search(r"\bhead\b|\bH\s*[=:\[]", line, re.IGNORECASE):
                    for m in head_re.finditer(line):
                        v = float(m.group(1).replace(",", "."))
                        if 0.1 <= v <= 2000:
                            all_head.append((v, page_no, fname, line[:80]))

        # H= inline patterns
        h_re = re.compile(r"H\s*[=:]\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE)
        for page_no, text in pages:
            for m in h_re.finditer(text):
                v = float(m.group(1).replace(",", "."))
                if 0.1 <= v <= 2000:
                    all_head.append((v, page_no, fname, m.group(0)[:60]))

        # Column-based: look for 'H [m]' table header then harvest next rows
        for page_no, text in pages:
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if re.search(r"\bH\s*\[\s*m\s*\]|\bHead\s*\[?m\]?", line, re.IGNORECASE):
                    for bl in lines[i+1:i+40]:
                        for n in re.findall(r"\b(\d+(?:\.\d+)?)\b", bl):
                            v = float(n)
                            if 0.1 <= v <= 2000:
                                all_head.append((v, page_no, fname, bl[:60]))

        # Also look for "max head X m" or "Hmax = X" patterns
        hmax_re = re.compile(
            r"(?:max(?:imum)?\s+head|Hmax|H\s*max)\s*[=:of]*\s*(\d+(?:[.,]\d+)?)",
            re.IGNORECASE
        )
        for page_no, text in pages:
            for m in hmax_re.finditer(text):
                v = float(m.group(1).replace(",", "."))
                if 0.1 <= v <= 2000:
                    all_head.append((v, page_no, fname, m.group(0)[:60]))

        # ── Power (P, kW) ──────────────────────────────────────────────────
        pwr_re = re.compile(r"(\d+(?:[.,]\d+)?)\s*kW\b", re.IGNORECASE)
        for page_no, text in pages:
            for m in pwr_re.finditer(text):
                v = float(m.group(1).replace(",", "."))
                if 0.01 <= v <= 10000:
                    all_power.append((v, page_no, fname, m.group(0)[:60]))

        # Also column-based P/kW header
        for page_no, text in pages:
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if re.search(r"\bP\s*\[?kW\]?|\bpower\b.*kW", line, re.IGNORECASE):
                    for bl in lines[i+1:i+20]:
                        for n in re.findall(r"\b(\d+(?:\.\d+)?)\b", bl):
                            v = float(n)
                            if 0.01 <= v <= 10000:
                                all_power.append((v, page_no, fname, bl[:60]))

        # ── Materials ──────────────────────────────────────────────────────
        mat_patterns = {
            "stainless_steel":    r"stainless[\s\-]steel|AISI\s*304|AISI\s*316|EN\s*1\.4301|EN\s*1\.4401",
            "cast_iron":          r"cast[\s\-]iron|grey[\s\-]iron|GG[\s\-]?25",
            "bronze":             r"\bbronze\b|gunmetal",
            "titanium":           r"\btitanium\b",
            "duplex_steel":       r"duplex|super[\s\-]duplex",
            "PVC":                r"\bPVC\b",
            "PEEK":               r"\bPEEK\b",
        }
        for mat, pat in mat_patterns.items():
            if re.search(pat, full_text, re.IGNORECASE):
                materials_found.add(mat)
                print(f"    Material found: {mat}")

    print("\n  Computing ranges …")

    def best_range(data, lo, hi, label):
        filtered = [(v, pg, fn, s) for v, pg, fn, s in data if lo <= v <= hi]
        if not filtered:
            print(f"    [{label}] No values found in range [{lo}, {hi}]")
            return None, None, None, None, None, None
        mn = min(filtered, key=lambda x: x[0])
        mx = max(filtered, key=lambda x: x[0])
        print(f"    [{label}] min={mn[0]} (p.{mn[1]} {mn[2]})  max={mx[0]} (p.{mx[1]} {mx[2]})")
        return mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]

    flow_min, flow_min_pg, flow_min_f, flow_max, flow_max_pg, flow_max_f = \
        best_range(all_flow, 0.01, 5000, "flow_rate")

    head_min, head_min_pg, head_min_f, head_max, head_max_pg, head_max_f = \
        best_range(all_head, 0.1, 2000, "head")

    pwr_min, pwr_min_pg, pwr_min_f, pwr_max, pwr_max_pg, pwr_max_f = \
        best_range(all_power, 0.01, 10000, "power")

    summary = {
        "flow_rate": (flow_min, flow_min_pg, flow_min_f, flow_max, flow_max_pg, flow_max_f),
        "head":      (head_min, head_min_pg, head_min_f, head_max, head_max_pg, head_max_f),
        "power":     (pwr_min,  pwr_min_pg,  pwr_min_f,  pwr_max,  pwr_max_pg,  pwr_max_f),
    }
    return summary, sorted(materials_found)


# ─────────────────────────────────────────────────────────────────────────────
# CIRCUIT BREAKERS
# ─────────────────────────────────────────────────────────────────────────────

BREAKER_PDFS = [
    "Schneider-ComPacT-NSX-User-Guide.pdf",
]

def extract_breaker_data():
    print("\n" + "="*70)
    print("CIRCUIT BREAKERS — extracting from PDFs …")
    print("="*70)

    all_current, all_voltage, all_breaking = [], [], []
    poles_found = set()

    for fname in BREAKER_PDFS:
        path = PDF_DIR / fname
        if not path.exists():
            print(f"  [SKIP] {fname} not found")
            continue
        print(f"\n  Reading {fname} …")
        pages = extract_text_pages(path)
        print(f"    Pages: {len(pages)}")

        full_text = " ".join(t for _, t in pages)

        # ── Rated current (In, A) ──────────────────────────────────────────
        # Look for "A" values near current-related keywords
        curr_re = re.compile(
            r"(\d+(?:[.,]\d+)?)\s*A\b", re.IGNORECASE
        )
        for page_no, text in pages:
            lines = text.split("\n")
            for line in lines:
                if re.search(r"\brated\s+current\b|\bIn\b|\bnominal\s+current\b", line, re.IGNORECASE):
                    for m in curr_re.finditer(line):
                        v = float(m.group(1).replace(",", "."))
                        if 1 <= v <= 6300:
                            all_current.append((v, page_no, fname, line[:80]))

        # Also look for "In = X A" style
        in_re = re.compile(r"In\s*=\s*(\d+(?:[.,]\d+)?)\s*A", re.IGNORECASE)
        for page_no, text in pages:
            for m in in_re.finditer(text):
                v = float(m.group(1).replace(",", "."))
                if 1 <= v <= 6300:
                    all_current.append((v, page_no, fname, m.group(0)[:80]))

        # NSX model names encode rating: NSX100, NSX160, NSX250, NSX400, NSX630
        nsx_re = re.compile(r"NSX\s*(\d{2,4})\b")
        for page_no, text in pages:
            for m in nsx_re.finditer(text):
                v = float(m.group(1))
                if 10 <= v <= 6300:
                    all_current.append((v, page_no, fname, m.group(0)[:80]))

        # Grab any "X A" from specification/characteristic tables
        for page_no, text in pages:
            lines = text.split("\n")
            for line in lines:
                if re.search(r"\bA\b", line):
                    nums = re.findall(r"\b(\d+(?:\.\d+)?)\s*A\b", line)
                    for n in nums:
                        v = float(n)
                        if 1 <= v <= 6300:
                            all_current.append((v, page_no, fname, line[:80]))

        # ── Rated voltage (Ue, V) ──────────────────────────────────────────
        volt_re = re.compile(r"(\d+(?:[.,]\d+)?)\s*V\b")
        for page_no, text in pages:
            lines = text.split("\n")
            for line in lines:
                if re.search(r"\bvoltage\b|\bUe\b|\bUn\b|\brated\s*V", line, re.IGNORECASE):
                    for m in volt_re.finditer(line):
                        v = float(m.group(1).replace(",", "."))
                        if 24 <= v <= 1500:
                            all_voltage.append((v, page_no, fname, line[:80]))

        # Also direct "XXX V" anywhere near "AC" or "DC"
        vac_re = re.compile(r"(\d{2,4})\s*V\s*(?:AC|DC)", re.IGNORECASE)
        for page_no, text in pages:
            for m in vac_re.finditer(text):
                v = float(m.group(1))
                if 24 <= v <= 1500:
                    all_voltage.append((v, page_no, fname, m.group(0)[:60]))

        # ── Breaking capacity (Icu/Ics, kA) ───────────────────────────────
        ka_re = re.compile(r"(\d+(?:[.,]\d+)?)\s*kA\b", re.IGNORECASE)
        for page_no, text in pages:
            for m in ka_re.finditer(text):
                v = float(m.group(1).replace(",", "."))
                if 1 <= v <= 200:
                    all_breaking.append((v, page_no, fname, m.group(0)[:60]))

        # ── Number of poles ────────────────────────────────────────────────
        pole_patterns = {
            3: r"\b3[\s\-]?pole[sd]?\b|3P\b",
            4: r"\b4[\s\-]?pole[sd]?\b|4P\b",
            2: r"\b2[\s\-]?pole[sd]?\b|2P\b",
            1: r"\b1[\s\-]?pole[sd]?\b|1P\b",
        }
        for pole_count, pat in pole_patterns.items():
            if re.search(pat, full_text, re.IGNORECASE):
                poles_found.add(pole_count)
                print(f"    Poles found: {pole_count}")

    print("\n  Computing ranges …")

    def best_range(data, lo, hi, label):
        filtered = [(v, pg, fn, s) for v, pg, fn, s in data if lo <= v <= hi]
        if not filtered:
            print(f"    [{label}] No values found in range [{lo}, {hi}]")
            return None, None, None, None, None, None
        mn = min(filtered, key=lambda x: x[0])
        mx = max(filtered, key=lambda x: x[0])
        print(f"    [{label}] min={mn[0]} (p.{mn[1]} {mn[2]})  max={mx[0]} (p.{mx[1]} {mx[2]})")
        return mn[0], mn[1], mn[2], mx[0], mx[1], mx[2]

    curr_min, curr_min_pg, curr_min_f, curr_max, curr_max_pg, curr_max_f = \
        best_range(all_current, 1, 6300, "rated_current")

    volt_min, volt_min_pg, volt_min_f, volt_max, volt_max_pg, volt_max_f = \
        best_range(all_voltage, 24, 1500, "rated_voltage")

    brk_min, brk_min_pg, brk_min_f, brk_max, brk_max_pg, brk_max_f = \
        best_range(all_breaking, 1, 200, "breaking_capacity")

    poles_list = sorted(poles_found)

    summary = {
        "rated_current":     (curr_min, curr_min_pg, curr_min_f, curr_max, curr_max_pg, curr_max_f),
        "rated_voltage":     (volt_min, volt_min_pg, volt_min_f, volt_max, volt_max_pg, volt_max_f),
        "breaking_capacity": (brk_min,  brk_min_pg,  brk_min_f,  brk_max,  brk_max_pg,  brk_max_f),
    }
    return summary, poles_list


# ─────────────────────────────────────────────────────────────────────────────
# WRITE SCHEMA FILES
# ─────────────────────────────────────────────────────────────────────────────

def write_schema(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    # Validate: re-read it
    with open(path, "r", encoding="utf-8") as f:
        json.load(f)
    print(f"  [OK] Written & validated: {path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY TABLE
# ─────────────────────────────────────────────────────────────────────────────

def print_summary_table(bearing_summary, bearing_materials,
                         pump_summary,    pump_materials,
                         breaker_summary, breaker_poles):
    print("\n" + "="*90)
    print("SUMMARY TABLE — all values sourced from real PDFs")
    print("="*90)
    print(f"{'Category':<18} {'Field':<25} {'Min':>10} {'Min Source':<40} {'Max':>10} {'Max Source':<40}")
    print("-"*90)

    def row(cat, field, summ):
        info = summ.get(field)
        if not info or info[0] is None:
            print(f"  !! {cat}/{field}: NOT FOUND in PDFs — omitted from schema")
            return
        mn, mn_pg, mn_f, mx, mx_pg, mx_f = info
        mn_src = f"{mn_f} p.{mn_pg}" if mn_f else "—"
        mx_src = f"{mx_f} p.{mx_pg}" if mx_f else "—"
        print(f"  {cat:<16} {field:<25} {mn:>10} {mn_src:<40} {mx:>10} {mx_src:<40}")

    for f in ["bore_diameter","outer_diameter","width","load_rating_dynamic","load_rating_static"]:
        row("ball_bearing", f, bearing_summary)
    print(f"  {'ball_bearing':<16} {'material (enum)':<25}  {bearing_materials}")

    for f in ["flow_rate","head","power"]:
        row("centrifugal_pump", f, pump_summary)
    print(f"  {'centrifugal_pump':<16} {'material (enum)':<25}  {pump_materials}")

    for f in ["rated_current","rated_voltage","breaking_capacity"]:
        row("circuit_breaker", f, breaker_summary)
    print(f"  {'circuit_breaker':<16} {'poles (enum)':<25}  {breaker_poles}")

    print("="*90)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    bearing_summary, bearing_materials = extract_bearing_data()
    pump_summary,    pump_materials    = extract_pump_data()
    breaker_summary, breaker_poles     = extract_breaker_data()

    print_summary_table(bearing_summary, bearing_materials,
                         pump_summary,    pump_materials,
                         breaker_summary, breaker_poles)

    # ── Build and write ball_bearing.json ──────────────────────────────────
    print("\nWriting schema files …")

    def v(summary, field, idx):
        info = summary.get(field)
        return info[idx] if info and info[idx] is not None else None

    # Ball bearing
    bb_fields = {}
    for field, lo_idx, hi_idx in [
        ("bore_diameter", 0, 3),
        ("outer_diameter", 0, 3),
        ("width", 0, 3),
        ("load_rating_dynamic", 0, 3),
    ]:
        info = bearing_summary.get(field)
        if info and info[0] is not None:
            bb_fields[field] = {
                "type": "number",
                "unit": "mm" if field in ("bore_diameter","outer_diameter","width") else "kN",
                "min": info[0],
                "max": info[3],
                "required": True,
            }
        else:
            print(f"  !! ball_bearing/{field} omitted — not found in PDFs")

    # load_rating_static is optional per spec
    stat_info = bearing_summary.get("load_rating_static")
    if stat_info and stat_info[0] is not None:
        bb_fields["load_rating_static"] = {
            "type": "number", "unit": "kN",
            "min": stat_info[0], "max": stat_info[3],
            "required": False,
        }

    if bearing_materials:
        bb_fields["material"] = {
            "type": "string",
            "enum": bearing_materials,
            "required": True,
        }

    bearing_schema = {"category": "ball_bearing", "fields": bb_fields}
    write_schema(SCHEMA_DIR / "ball_bearing.json", bearing_schema)

    # Centrifugal pump
    pump_fields = {}
    for field, unit in [("flow_rate","m3/h"),("head","m"),("power","kW")]:
        info = pump_summary.get(field)
        if info and info[0] is not None:
            pump_fields[field] = {
                "type": "number", "unit": unit,
                "min": info[0], "max": info[3],
                "required": True,
            }
        else:
            print(f"  !! centrifugal_pump/{field} omitted — not found in PDFs")

    if pump_materials:
        pump_fields["material"] = {
            "type": "string",
            "enum": pump_materials,
            "required": True,
        }

    pump_schema = {"category": "centrifugal_pump", "fields": pump_fields}
    write_schema(SCHEMA_DIR / "centrifugal_pump.json", pump_schema)

    # Circuit breaker
    cb_fields = {}
    for field, unit in [("rated_current","A"),("rated_voltage","V"),("breaking_capacity","kA")]:
        info = breaker_summary.get(field)
        if info and info[0] is not None:
            cb_fields[field] = {
                "type": "number", "unit": unit,
                "min": info[0], "max": info[3],
                "required": True,
            }
        else:
            print(f"  !! circuit_breaker/{field} omitted — not found in PDFs")

    if breaker_poles:
        cb_fields["poles"] = {
            "type": "number",
            "enum": breaker_poles,
            "required": True,
        }

    cb_schema = {"category": "circuit_breaker", "fields": cb_fields}
    write_schema(SCHEMA_DIR / "circuit_breaker.json", cb_schema)

    print("\n✅ All three schema files written and validated successfully.")


if __name__ == "__main__":
    main()
