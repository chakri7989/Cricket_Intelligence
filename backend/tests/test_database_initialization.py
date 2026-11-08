import os
import shutil
import pytest
from pathlib import Path

from langchain_core.documents import Document
from app.db.models import Base, Match, Delivery, Player, Team
from app.db.sqlite_manager import SQLiteManager
from app.db.chromadb_manager import ChromaDBManager, GeminiCricketEmbeddings

TEMP_SQLITE_PATH = Path("backend/data/sqlite/test_phase3_init.db")
TEMP_CHROMA_DIR = Path("backend/data/chroma_test_phase3")

@pytest.fixture(scope="module")
def sqlite_test_instance():
    TEMP_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TEMP_SQLITE_PATH.exists():
        try:
            TEMP_SQLITE_PATH.unlink()
        except OSError:
            pass

    mgr = SQLiteManager(db_path=TEMP_SQLITE_PATH)
    yield mgr

    # Cleanup safely
    try:
        if TEMP_SQLITE_PATH.exists():
            TEMP_SQLITE_PATH.unlink()
    except OSError:
        pass

@pytest.fixture(scope="module")
def chroma_test_instance():
    TEMP_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    mgr = ChromaDBManager(persist_dir=TEMP_CHROMA_DIR)
    yield mgr

    # Cleanup directory safely
    try:
        shutil.rmtree(TEMP_CHROMA_DIR, ignore_errors=True)
    except Exception:
        pass

# ----------------- SQLITE INITIALIZATION TESTS -----------------

def test_sqlite_auto_initialization_and_tables(sqlite_test_instance):
    """
    Verifies that SQLite automatically initializes without manual DDL,
    creates normalized SQLAlchemy tables, primary keys, and foreign keys.
    """
    res = sqlite_test_instance.initialize_database()
    assert res["status"] == "ready"
    assert TEMP_SQLITE_PATH.exists()

    # Verify tables via SQLAlchemy session
    with sqlite_test_instance.get_session() as session:
        match_count = session.query(Match).count()
        player_count = session.query(Player).count()
        team_count = session.query(Team).count()
        delivery_count = session.query(Delivery).count()

        assert match_count > 0, "Matches table should contain initial records"
        assert player_count > 0, "Players table should contain initial records"
        assert team_count > 0, "Teams table should contain initial records"
        assert delivery_count > 0, "Deliveries table should contain initial records"

def test_sqlite_foreign_key_relationship(sqlite_test_instance):
    """
    Verifies that relationship and foreign keys between Match and Delivery work as configured.
    """
    with sqlite_test_instance.get_session() as session:
        first_match = session.query(Match).first()
        assert first_match is not None
        # Access relationship
        deliveries = first_match.deliveries
        assert isinstance(deliveries, list)
        for d in deliveries:
            assert d.match_id == first_match.id

def test_sqlite_preserves_records_across_restarts(sqlite_test_instance):
    """
    Verifies that re-running initialize_database does NOT overwrite or duplicate existing records.
    """
    with sqlite_test_instance.get_session() as session:
        initial_matches = session.query(Match).count()
        initial_players = session.query(Player).count()
        initial_deliveries = session.query(Delivery).count()

    # Re-run initialization
    res = sqlite_test_instance.initialize_database()
    assert res["matches"] == initial_matches
    assert res["players"] == initial_players
    assert res["deliveries"] == initial_deliveries

def test_sqlite_health_check(sqlite_test_instance):
    """
    Verifies that the SQLite health check returns healthy status, table counts, and latency.
    """
    health = sqlite_test_instance.health_check()
    assert health["status"] == "healthy"
    assert "counts" in health
    assert health["counts"]["matches"] > 0
    assert health["latency_ms"] >= 0

# ----------------- CHROMADB INITIALIZATION TESTS -----------------

def test_chromadb_auto_initialization_and_collections(chroma_test_instance):
    """
    Verifies that ChromaDB local persistent directory and required collections
    (cricket_narratives, cricket_knowledge) are created automatically without manual commands.
    """
    res = chroma_test_instance.initialize_database()
    assert res["status"] == "ready"
    assert "cricket_narratives" in res["collections"]
    assert "cricket_knowledge" in res["collections"]
    assert res["collections"]["cricket_narratives"] > 0
    assert res["collections"]["cricket_knowledge"] > 0

def test_chromadb_langchain_integration_and_search(chroma_test_instance):
    """
    Verifies that LangChain Chroma vectorstores perform semantic similarity search.
    """
    narratives_store = chroma_test_instance.get_narratives_store()
    assert narratives_store is not None

    # Search for Kohli's MCG innings
    results = chroma_test_instance.search_narratives("Kohli sixes Haris Rauf MCG", n_results=1)
    assert len(results) > 0
    first_doc = results[0]
    assert "Kohli" in first_doc["text"]
    assert "metadata" in first_doc

def test_chromadb_deduplication_and_update_handling(chroma_test_instance):
    """
    Verifies that inserting a document with an existing ID updates it in-place
    and does NOT duplicate collection document counts.
    """
    knowledge_store = chroma_test_instance.get_knowledge_store()
    initial_count = knowledge_store._collection.count()

    test_doc = Document(
        page_content="The DLS method target is revised when play is curtailed by rain.",
        metadata={"id": "rule_dls_method", "type": "rule", "version": "v1"}
    )

    # Upsert with existing ID
    chroma_test_instance.upsert_documents("knowledge", [test_doc], ids=["rule_dls_method"])
    updated_count = knowledge_store._collection.count()

    # Document count must NOT increase (no duplicate document created)
    assert updated_count == initial_count

    # Content must reflect updated text in the ChromaDB collection
    stored_doc = knowledge_store._collection.get(ids=["rule_dls_method"])
    assert len(stored_doc["documents"]) == 1
    assert "curtailed by rain" in stored_doc["documents"][0]
    assert stored_doc["metadatas"][0]["version"] == "v1"

def test_chromadb_health_check(chroma_test_instance):
    """
    Verifies that ChromaDB health check verifies connectivity, latency, and collections.
    """
    health = chroma_test_instance.health_check()
    assert health["status"] == "healthy"
    assert "collections" in health
    assert health["collections"]["cricket_narratives"] > 0
    assert health["collections"]["cricket_knowledge"] > 0
    assert health["test_query_returned"] is True
    assert health["latency_ms"] >= 0
