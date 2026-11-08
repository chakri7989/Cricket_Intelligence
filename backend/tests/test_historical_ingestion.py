import os
import json
import sqlite3
import pytest
from pathlib import Path

from app.data_ingestion.historical_ingestion import (
    historical_ingestion_service,
    CricsheetValidator,
    PlayerNormalizer
)
from app.db.sqlite_manager import SQLiteManager

TEST_DB_PATH = Path("backend/data/sqlite/test_cricsheet.db")

@pytest.fixture(scope="session")
def test_db():
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except OSError:
            pass

    db_manager = SQLiteManager(db_path=TEST_DB_PATH)
    db_manager.initialize_database()
    yield db_manager

    # Cleanup after session safely
    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except OSError:
        pass

def test_cricsheet_validator_clean_and_corrupt():
    """
    Verifies that CricsheetValidator correctly accepts valid JSON
    and rejects corrupted or invalid schemas.
    """
    valid_data = {
        "meta": {"data_version": "1.3.0", "created": "2024-01-01"},
        "info": {
            "match_type": "T20",
            "teams": ["India", "Australia"],
            "dates": ["2024-01-01"]
        },
        "innings": [
            {
                "team": "India",
                "overs": [
                    {
                        "over": 0,
                        "deliveries": [
                            {
                                "batter": "Batter A",
                                "bowler": "Bowler B",
                                "runs": {"batter": 4, "extras": 0, "total": 4}
                            }
                        ]
                    }
                ]
            }
        ]
    }
    is_valid, errors = CricsheetValidator.validate_match(valid_data)
    assert is_valid is True
    assert len(errors) == 0

    # Corrupt case 1: Run math mismatch (total != batter + extras)
    corrupt_math = json.loads(json.dumps(valid_data))
    corrupt_math["innings"][0]["overs"][0]["deliveries"][0]["runs"]["total"] = 99
    is_valid, errors = CricsheetValidator.validate_match(corrupt_math)
    assert is_valid is False
    assert any("Run math mismatch" in err for err in errors)

    # Corrupt case 2: Less than 2 teams
    corrupt_teams = json.loads(json.dumps(valid_data))
    corrupt_teams["info"]["teams"] = ["OnlyOneTeam"]
    is_valid, errors = CricsheetValidator.validate_match(corrupt_teams)
    assert is_valid is False
    assert any("at least 2 teams" in err for err in errors)

def test_player_name_and_id_normalization():
    """
    Verifies that player names are normalized and registry IDs are preserved.
    """
    registry = {
        "DA Warner": "b0682224",
        "V Kohli": "b0682224_diff"
    }
    
    # Registered player
    p_id, reg_id = PlayerNormalizer.create_player_id("DA Warner", registry)
    assert p_id == "p_b0682224"
    assert reg_id == "b0682224"

    # Unregistered player falls back to deterministic slug
    p_id2, reg_id2 = PlayerNormalizer.create_player_id("Unregistered Player  ExtraSpaces ", {})
    assert p_id2 == "p_unregistered_player_extraspaces"
    assert reg_id2 is None

def test_extract_records_fidelity_with_original_source(test_db):
    """
    Verifies that extracted database records match original raw Cricsheet JSON data exactly:
    - Match score matches the sum of delivery runs.
    - Total deliveries count matches source JSON.
    - Wickets count matches source JSON.
    - Player of match, venue, outcome match source.
    """
    raw_dir = historical_ingestion_service.find_raw_data_dir()
    raw_path = raw_dir / "IPL" / "1082591.json"
    assert raw_path.exists(), f"Raw test file {raw_path} must exist"

    with open(raw_path, "r", encoding="utf-8") as f:
        source_json = json.load(f)

    # Ingest file into test database
    conn = test_db.get_connection()
    success, action, err = historical_ingestion_service.ingest_single_match(raw_path, conn, force_match_id="1082591")
    assert success is True
    assert action in ("imported", "updated")

    # 1. Verify Match Metadata
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = '1082591';")
    match_row = dict(cursor.fetchone())

    assert match_row["id"] == "1082591"
    assert match_row["winner"] == source_json["info"]["outcome"]["winner"]
    assert match_row["win_by_runs"] == source_json["info"]["outcome"]["by"]["runs"]
    assert match_row["player_of_match"] == source_json["info"]["player_of_match"][0]
    assert match_row["venue"] == source_json["info"]["venue"]
    assert match_row["city"] == source_json["info"]["city"]
    assert match_row["source_file"] == str(raw_path.as_posix())

    # 2. Verify Deliveries and Run Calculations
    cursor.execute("""
        SELECT 
            inning,
            COUNT(*) as delivery_count,
            SUM(batsman_runs) as bat_runs,
            SUM(extra_runs) as extra_runs,
            SUM(total_runs) as total_runs,
            SUM(is_wicket) as wickets,
            SUM(is_six) as sixes,
            SUM(is_boundary) as boundaries
        FROM deliveries
        WHERE match_id = '1082591'
        GROUP BY inning
        ORDER BY inning;
    """)
    db_innings = [dict(row) for row in cursor.fetchall()]
    assert len(db_innings) == len(source_json["innings"])

    # Calculate truth metrics directly from source JSON
    for inn_idx, source_inn in enumerate(source_json["innings"]):
        db_inn = db_innings[inn_idx]
        
        expected_deliveries = 0
        expected_total_runs = 0
        expected_bat_runs = 0
        expected_extras = 0
        expected_wickets = 0
        expected_sixes = 0

        for over in source_inn["overs"]:
            for d in over["deliveries"]:
                expected_deliveries += 1
                r = d.get("runs", {})
                expected_bat_runs += r.get("batter", 0)
                expected_extras += r.get("extras", 0)
                expected_total_runs += r.get("total", 0)
                if d.get("wickets"):
                    expected_wickets += len(d["wickets"])
                if r.get("batter") == 6:
                    expected_sixes += 1

        assert db_inn["delivery_count"] == expected_deliveries
        assert db_inn["total_runs"] == expected_total_runs
        assert db_inn["bat_runs"] == expected_bat_runs
        assert db_inn["extra_runs"] == expected_extras
        assert db_inn["wickets"] == expected_wickets
        assert db_inn["sixes"] == expected_sixes

    conn.close()

def test_idempotence_and_duplicate_prevention(test_db):
    """
    Verifies that re-ingesting the exact same match does NOT create duplicate records.
    """
    raw_dir = historical_ingestion_service.find_raw_data_dir()
    raw_path = raw_dir / "IPL" / "1082591.json"
    conn = test_db.get_connection()

    # Get baseline delivery count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM deliveries WHERE match_id = '1082591';")
    initial_deliveries = cursor.fetchone()[0]
    assert initial_deliveries > 0

    # Re-ingest exact same file
    success, action, err = historical_ingestion_service.ingest_single_match(raw_path, conn, force_match_id="1082591")
    assert success is True
    assert action == "updated"

    # Verify count is completely identical
    cursor.execute("SELECT COUNT(*) FROM deliveries WHERE match_id = '1082591';")
    after_deliveries = cursor.fetchone()[0]
    assert after_deliveries == initial_deliveries

    cursor.execute("SELECT COUNT(*) FROM matches WHERE id = '1082591';")
    match_count = cursor.fetchone()[0]
    assert match_count == 1

    conn.close()

def test_missing_values_handled_without_inventing_statistics(test_db):
    """
    Verifies that missing values (e.g., tie/no result match with no winner, no city)
    are stored as None or standard strings, and no stats are invented.
    """
    synthetic_tie_match = {
        "meta": {"data_version": "1.3.0", "created": "2024-05-01"},
        "info": {
            "match_type": "T20",
            "teams": ["Team Alpha", "Team Beta"],
            "dates": ["2024-05-01"],
            "outcome": {
                "result": "no result"
                # Note: No "winner", no "by" (runs/wickets)
            },
            # Note: No "city", no "player_of_match", no "toss"
            "venue": "Rainy Grounds"
        },
        "innings": []
    }

    temp_path = Path("backend/data/temp_no_result.json")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(synthetic_tie_match, f)

    conn = test_db.get_connection()
    success, action, err = historical_ingestion_service.ingest_single_match(temp_path, conn, force_match_id="m_no_result")
    assert success is True

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = 'm_no_result';")
    row = dict(cursor.fetchone())

    # Verify that missing fields remain None / 0, not fabricated
    assert row["winner"] is None
    assert row["win_by_runs"] == 0
    assert row["win_by_wickets"] == 0
    assert row["outcome_result"] == "no result"
    assert row["city"] is None
    assert row["player_of_match"] is None
    assert row["toss_winner"] is None

    conn.close()
    if temp_path.exists():
        temp_path.unlink()

def test_multiple_cricket_formats(test_db):
    """
    Verifies that T20, ODI, and Test formats are ingested with format-specific details.
    """
    raw_dir = historical_ingestion_service.find_raw_data_dir()
    conn = test_db.get_connection()

    # ODI
    odi_path = raw_dir / "ODI" / "1384439.json"
    if odi_path.exists():
        success, _, _ = historical_ingestion_service.ingest_single_match(odi_path, conn, force_match_id="odi_test_1")
        assert success is True
        cursor = conn.cursor()
        cursor.execute("SELECT match_type, overs_limit FROM matches WHERE id = 'odi_test_1';")
        r = cursor.fetchone()
        assert r[0] == "ODI"
        assert r[1] == 50

    # Test
    test_path = raw_dir / "TEST" / "1384440.json"
    if test_path.exists():
        success, _, _ = historical_ingestion_service.ingest_single_match(test_path, conn, force_match_id="test_test_1")
        assert success is True
        cursor = conn.cursor()
        cursor.execute("SELECT match_type, venue FROM matches WHERE id = 'test_test_1';")
        r = cursor.fetchone()
        assert r[0] == "Test"
        assert "Headingley" in r[1]

    conn.close()
