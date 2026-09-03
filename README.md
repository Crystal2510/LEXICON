# LEXICON - AI-Powered Product Data Enrichment Platform

## What is LEXICON?

LEXICON transforms raw product data from 6 input columns into 252 enriched Unilog-ready columns automatically. It replaces hours of manual data entry with a 3-second automated pipeline.

**The Problem:**
- Product data arrives from 500+ distributors in minimal format (part number, description, brand)
- Unilog needs 252 enriched columns (classification, attributes, descriptions, UNSPSC codes)
- Manual processing takes hours per batch with inconsistent results

**The Solution:**
- LEXICON reads raw CSV, processes 1000 products in 3-5 seconds
- Outputs strict 252-column Unilog format ready for direct import
- Self-learning system that improves with every batch

---

## How It Works

### 4-Stage Pipeline

```
Input (6 columns) → Brand Resolution → Classification → Attribute Extraction → Description Generation → Output (252 columns)
```

**Stage 1: Brand Resolution**
- Maps 27,000+ manufacturers to brands using MPN prefix analysis
- Scans part descriptions for brand mentions
- Self-learns new brand mappings from input data

**Stage 2: Classification**
- Assigns Dept > Class > Fine hierarchy using regex pattern grammars
- Self-learning classifier improves with every confirmed row
- Covers Power Tools, Electrical, Hand Tools, Lighting, Building Materials, Safety, Appliances

**Stage 3: Attribute Extraction**
- Spec inference engine matches MPN prefixes against 79 known product families
- Extracts voltage, dimensions, material, finish, color, and 50+ other attributes
- Optional web enrichment via DuckDuckGo for missing specs

**Stage 4: Description Generation**
- Creates 4 Unilog-compliant descriptions:
  - MOBILE_DESC: 60-80 characters for mobile apps
  - INVOICE_DESC: Maximum 40 characters for billing
  - SHORT_DESC: Catalog listing
  - LONG_DESC: Detailed product description

### Quality Assurance
- Confidence scoring (0-99%) based on classification depth, brand match, attribute count
- Low-confidence items flagged for human review
- Duplicate MPN detection
- Product image generation from brand + MPN

---

## Architecture

```
Frontend (React + TypeScript) → FastAPI Backend → LEXICON Pipeline → Output
```

### Frontend
- **React + TypeScript** with Tailwind CSS
- **Data Ingestion**: Drag-and-drop CSV upload with preview
- **Analytics Dashboard**: Real-time stats, category distribution, confidence charts
- **Human Review Queue**: Edit and approve low-confidence items
- **Catalog Grid**: Search, filter, paginated table with export buttons

### Backend
- **FastAPI** with CORS middleware
- RESTful API endpoints for enrichment, review, approval, export
- In-memory processing with disk persistence (survives server restarts)

### Pipeline
- **Pandas** for data manipulation
- **Custom NLP** for brand resolution and classification
- **Regex grammars** for attribute extraction
- **DuckDuckGo search** for optional web enrichment (free, no API key)
- **Connection pooling** and lazy imports for fast startup

---

## Project Structure

```
LEXICON/
├── backend/
│   └── main.py              # FastAPI server, all API endpoints
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Main app with routing
│   │   ├── api.ts            # API client functions
│   │   └── components/
│   │       ├── DataIngestion.tsx    # Upload and processing
│   │       ├── Dashboard.tsx        # Analytics dashboard
│   │       ├── HumanReview.tsx      # Review queue
│   │       └── CatalogGrid.tsx      # Data grid with export
│   ├── index.css             # Tailwind config and theme
│   └── vite.config.ts        # Vite config with API proxy
├── src/
│   ├── pipeline.py           # Main pipeline orchestrator
│   ├── brand_normalizer.py   # 27,000+ manufacturer mappings
│   ├── brand_learner.py      # Self-learning brand resolver
│   ├── classifier_learner.py # Self-learning classifier
│   ├── description_parser.py # Part description parser
│   ├── desc_engine.py        # Description generator
│   ├── desc_generator.py     # Short/Long description builder
│   ├── spec_inference.py     # 79 MPN prefix spec database
│   ├── web_sourcing.py       # DuckDuckGo web enricher
│   ├── attribute_grammars.py # Regex attribute extractor
│   ├── data_loader.py        # Reference data loader
│   └── write_parser.py       # Write/size parser
├── data/
│   └── sample_input.csv      # Sample 1000-row dataset
├── output/                   # Pipeline output files
├── requirements.txt          # Python dependencies
└── start_nexus.bat           # Windows startup script
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Server health and reference file status |
| `/api/preview` | POST | Preview CSV columns and first 50 rows |
| `/api/enrich` | POST | Process CSV through full pipeline |
| `/api/stats` | GET | Dashboard statistics |
| `/api/all-rows` | GET | All enriched rows for review |
| `/api/review-queue` | GET | Grouped review items |
| `/api/approve` | POST | Approve/edit a single row |
| `/api/approve-batch` | POST | Batch approve rows |
| `/api/download/csv` | GET | Download enriched CSV |
| `/api/download/xlsx` | GET | Download enriched Excel |
| `/api/download/unilog` | POST | Download strict 252-column format |
| `/api/product-image/{brand}/{mpn}` | GET | Generate product image |

---

## Setup

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open http://localhost:5173

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `/api` (proxy) |

For deployment, set `VITE_API_URL` to your backend URL.

---

## Deployment

### Backend (Render)
1. Connect GitHub repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)
1. Connect GitHub repo
2. Framework: Vite
3. Build command: `npm run build`
4. Output directory: `dist`
5. Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`

---

## Key Features

- **Self-Learning**: Learns brand mappings and classifications from input data
- **Dynamic**: Works with any product data, not hardcoded to specific categories
- **Fast**: 3ms per row processing speed
- **Quality Gate**: Confidence scoring with human-in-the-loop review
- **Offline**: No paid APIs required (DuckDuckGo is free)
- **252-Column Export**: Strict Unilog format with QA columns stripped
- **Disk Persistence**: Enriched data survives server restarts
- **Memory Optimized**: Lazy imports, garbage collection for free tier hosting

---

## Performance

| Metric | Value |
|--------|-------|
| Processing speed | 3-5 seconds per 1000 rows |
| Brand resolution | 27,000+ manufacturer mappings |
| Classification | 200+ product categories |
| Attribute extraction | 50+ attributes per product |
| Description generation | 4 formats (MOBILE, INVOICE, SHORT, LONG) |
| Memory usage | ~200MB after enrichment |
| CSV download | 0.4 seconds |
| XLSX download | 10 seconds |

---

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Framer Motion, Recharts
- **Backend**: Python 3.11, FastAPI, Pandas, Pydantic
- **Pipeline**: Custom NLP, Regex Grammars, Scikit-learn (TF-IDF classifier)
- **Web**: DuckDuckGo Search, BeautifulSoup4, Requests with connection pooling
- **Export**: Pandas CSV/Excel, OpenPyXL with styled headers

---

## Sample Data

The project includes `data/sample_input.csv` with 1000 product rows from multiple distributors covering:
- Power Tools (DeWalt, Milwaukee, Makita, Bosch, Hilti)
- Appliances (Whirlpool, Frigidaire, LG, Samsung)
- Electrical (Leviton, Lutron, Southwire)
- Lighting (Satco, Kichler, Lithonia)
- Hand Tools (Klein, Channellock, Irwin)
- Building Materials (Trex, Azek, Simpson Strong-Tie)
