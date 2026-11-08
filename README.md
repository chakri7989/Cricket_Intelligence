# 🏏 AI-Powered Cricket Intelligence System

An end-to-end, full-stack Cricket Intelligence platform orchestrated by **LangGraph** and **Google Gemini**, backed by **SQLAlchemy SQLite** for ball-by-ball historical records and **ChromaDB** for semantic narrative retrieval.

Features a responsive, high-contrast monochrome (Black & White) user interface built with **React** and **Tailwind CSS**.

---

## 🌟 Key Capabilities

1. **Historical Cricket Queries (Deterministic Text-to-SQL)**:
   - Evaluates career records, death-over strike rates (overs 16–20), powerplay economy, boundary frequencies, and tournament statistics directly from Cricsheet historical datasets.
2. **Live Match Center & Telemetry**:
   - Real-time match scorecards, ball-by-ball updates, current run rate vs. required run rate equation solver, and active batter/bowler figures with TTL caching.
3. **Hybrid Contextual Reasoning**:
   - Merges ongoing live match equations with historical run chase records under identical venue, pitch, and player conditions.
4. **Player Comparison Studio & Radar Maps**:
   - Head-to-head performance matrix evaluating strike rate, boundary %, death-over acceleration, dot-ball resistance, and six-hitting frequency with dynamic high-contrast radar charts.
5. **ChromaDB Semantic Vector RAG**:
   - Semantic retrieval over iconic cricket match reports, tournament narratives, and official cricket laws (DLS method, Super Over rules, DRS guidelines, boundary countback).

---

## 🏗️ System Architecture

```
                      +-----------------------------+
                      |   React + Tailwind Frontend |
                      |    (http://localhost:5173)  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |      FastAPI Backend        |
                      |    (http://localhost:8000)  |
                      +--------------+--------------+
                                     |
             +-----------------------+-----------------------+
             |                       |                       |
             v                       v                       v
    +-----------------+     +-----------------+     +-----------------+
    | LangGraph Multi |     |  SQLite Engine  |     | ChromaDB Vector |
    |   Agent Graph   |     | (Ball-by-Ball)  |     |   (Narratives)  |
    +--------+--------+     +--------+--------+     +--------+--------+
             |                       |                       |
             v                       v                       v
      Gemini API &            406 deliveries,         Iconic Matches &
     Intent Router              17 players,             Tactical RAG
                                 5 matches
```

---

## 📁 Repository Structure

```
Cricket_Intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI server & lifecycle health checks
│   │   ├── core/
│   │   │   └── config.py            # Pydantic settings & environment configuration
│   │   ├── db/
│   │   │   ├── models.py            # SQLAlchemy models (Match, Delivery, Player, Team)
│   │   │   ├── sqlite_manager.py    # Auto-init SQLite, connection pool, DDL migrations
│   │   │   └── chromadb_manager.py  # LangChain Chroma persistent vector store & embeddings
│   │   ├── data_ingestion/
│   │   │   ├── historical_ingestion.py # Multi-format Cricsheet parser, validator & reporter
│   │   │   ├── narrative_indexer.py    # Automated match summaries & rules indexer
│   │   │   └── cricsheet_parser.py     # Batch ingestion CLI
│   │   ├── services/
│   │   │   ├── sql_query_service.py    # Safe Text-to-SQL engine with self-repair
│   │   │   ├── live_cricket_service.py # Live match tracker with TTL cache & simulation
│   │   │   └── comparison_service.py   # Head-to-head metric matrix & radar generator
│   │   └── agents/
│   │       ├── state.py             # LangGraph typed state
│   │       └── graph.py             # Compiled multi-agent DAG workflow
│   ├── tests/
│   │   ├── test_historical_ingestion.py     # Cricsheet parser & data fidelity test suite
│   │   └── test_database_initialization.py # SQLite & ChromaDB health and auto-init tests
│   └── requirements.txt             # Lean Python backend dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/layout/       # Navbar, Footer (monochrome visual system)
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx      # High-contrast hero & interactive 4-portal grid
│   │   │   ├── IntelligenceHub.jsx  # Multi-agent chat terminal with reasoning breakdown
│   │   │   ├── LiveCenter.jsx       # Real-time scorecards, equation solver & commentary
│   │   │   ├── PlayerComparePage.jsx# Head-to-head studio & interactive radar chart
│   │   │   └── HistoricalVault.jsx  # Cricsheet match records explorer
│   │   ├── services/api.js          # REST client communicating with FastAPI
│   │   ├── App.jsx                  # React Router configuration
│   │   └── index.css                # Tailwind CSS v4 directives & theme variables
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   └── raw/                         # Raw Cricsheet datasets (IPL, ODI, T20, TEST)
└── README.md
```

---

## ⚡ Quickstart Guide

### Prerequisites
- **Python**: 3.11+
- **Node.js**: v18+ (npm v9+)
- **Git**

### 1. Backend Setup
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Start FastAPI server (Port 8000)
python -m uvicorn app.main:app --port 8000 --reload
```

*Note: SQLite tables and ChromaDB vector collections automatically initialize on startup with zero manual DDL commands.*

### 2. Frontend Setup
```powershell
cd frontend
npm install

# Start Vite dev server (Port 5173)
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## 🧪 Running Automated Tests

Run the full test suite with pytest:
```powershell
cd backend
python -m pytest tests/ -v
```

All 14 unit and integration tests verify:
- Source data fidelity (deliveries, runs, wickets, extras)
- Idempotence & duplicate prevention
- Multi-format ingestion (T20, ODI, Test)
- Missing values handling (zero invented stats)
- SQLite SQLAlchemy relationship integrity
- ChromaDB vector search & in-place update deduplication

---

## 🔐 Environment Variables (Optional)

Create `.env` inside `backend/`:
```env
# Google Gemini API Key (optional for live LLM routing; heuristic fallbacks enabled)
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash

# Live Cricket API (optional; automated mock engine runs if unset)
CRICKET_API_KEY=
CRICKET_API_BASE_URL=https://api.cricapi.com/v1
```

---

## 📜 License
Open-source under the MIT License. Historical cricket datasets provided by [Cricsheet](https://cricsheet.org/) under the ODbL.
