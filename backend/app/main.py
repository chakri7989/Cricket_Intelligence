from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
from app.db.sqlite_manager import sqlite_manager
from app.db.chromadb_manager import chroma_manager
from app.services.live_cricket_service import live_cricket_service
from app.services.comparison_service import comparison_service
from app.agents.graph import cricket_agent_graph

# Automatic lifecycle initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing SQLite Database...")
    db_status = sqlite_manager.initialize_database()
    print(f"SQLite Ready: {db_status}")

    print("Initializing ChromaDB Vector Store...")
    chroma_status = chroma_manager.initialize_database()
    print(f"ChromaDB Ready: {chroma_status}")

    yield
    print("Application shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    intent: str
    final_answer: str
    citations: list[str] = []
    chart_payload: Optional[Dict[str, Any]] = None
    sql_query: Optional[str] = None
    sql_results: Optional[list[Dict[str, Any]]] = None
    live_data: Optional[Dict[str, Any]] = None

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online"
    }

@app.get("/api/system/status")
@app.get("/api/system/health")
def system_status():
    """
    Returns automated database and service health checks with latency and table counts.
    """
    sqlite_health = sqlite_manager.health_check()
    chroma_health = chroma_manager.health_check()
    is_healthy = sqlite_health.get("status") == "healthy" and chroma_health.get("status") == "healthy"
    return {
        "status": "healthy" if is_healthy else "degraded",
        "sqlite": sqlite_health,
        "chromadb": chroma_health,
        "live_api_active": bool(settings.CRICKET_API_KEY.strip()),
        "gemini_active": bool(settings.GEMINI_API_KEY.strip())
    }

class IngestRequest(BaseModel):
    format_folder: Optional[str] = None  # e.g., "IPL", "ODI", "T20", "TEST", or None for all
    max_matches: Optional[int] = 20

@app.post("/api/system/ingest-raw")
def ingest_raw_dataset(request: IngestRequest):
    """
    Ingests historical Cricsheet JSON datasets from data/raw into SQLite with schema validation,
    consistent player ID normalization, duplicate prevention, and detailed reporting.
    """
    from app.data_ingestion.historical_ingestion import historical_ingestion_service
    try:
        base_dir = None
        if request.format_folder:
            raw_root = historical_ingestion_service.find_raw_data_dir()
            base_dir = raw_root / request.format_folder

        report = historical_ingestion_service.ingest_raw_directory(
            base_dir=base_dir,
            max_files=request.max_matches
        )
        return {
            "status": "success",
            "report": report.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
async def process_cricket_query(request: QueryRequest):
    """
    Main LangGraph intelligence orchestration endpoint.
    Handles historical SQL, ChromaDB RAG, Live matches, Hybrid queries, and Comparisons.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = await cricket_agent_graph.ainvoke({"query": request.query})
        return QueryResponse(
            query=request.query,
            intent=result.get("intent", "UNKNOWN"),
            final_answer=result.get("final_answer", ""),
            citations=result.get("citations", []),
            chart_payload=result.get("chart_payload"),
            sql_query=result.get("sql_query"),
            sql_results=result.get("sql_results"),
            live_data=result.get("live_data")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence Agent Error: {str(e)}")

@app.get("/api/matches/live")
async def get_live_matches():
    """
    Returns all active live cricket matches.
    """
    matches = await live_cricket_service.get_live_matches()
    return {"matches": matches}

@app.get("/api/matches/{match_id}")
async def get_match_details(match_id: str):
    """
    Returns detailed ball-by-ball, commentary, and scorecard for a live match.
    """
    scorecard = await live_cricket_service.get_match_scorecard(match_id)
    if not scorecard:
        raise HTTPException(status_code=404, detail="Match not found")
    return scorecard

@app.get("/api/players/compare")
def compare_players(p1: str = "Virat Kohli", p2: str = "Rohit Sharma"):
    """
    Head-to-head comparison endpoint emitting structured stats and radar metrics.
    """
    res = comparison_service.compare_players(p1, p2)
    return res

@app.get("/api/players/list")
def list_players():
    """
    Returns available players from SQLite for player picker.
    """
    cols, rows = sqlite_manager.execute_query("SELECT id, name, country, role, batting_style, bowling_style FROM players ORDER BY name ASC;")
    return {"players": rows}

@app.get("/api/vault/matches")
def list_vault_matches():
    """
    Returns historical matches from Cricsheet SQLite database.
    """
    cols, rows = sqlite_manager.execute_query("SELECT id, season, date, match_type, venue, team1, team2, winner, win_by_runs, win_by_wickets, player_of_match FROM matches ORDER BY date DESC;")
    return {"matches": rows}

