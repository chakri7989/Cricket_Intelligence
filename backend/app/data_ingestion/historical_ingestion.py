import os
import re
import json
import time
import unicodedata
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import sqlite3

from app.core.config import settings
from app.db.sqlite_manager import sqlite_manager

# Canonical Format Normalization
FORMAT_MAP = {
    "t20": "T20",
    "it20": "T20",
    "odi": "ODI",
    "odm": "ODI",
    "test": "Test",
    "mdm": "Test",
    "100": "100-ball",
    "100-ball": "100-ball"
}

@dataclass
class IngestionReport:
    """
    Structured report returned after an ingestion run.
    """
    scanned_files: int = 0
    imported_matches: int = 0
    updated_matches: int = 0
    failed_matches: int = 0
    total_players: int = 0
    total_deliveries: int = 0
    formats: Dict[str, int] = field(default_factory=dict)
    errors: List[Dict[str, str]] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def summary_table(self) -> str:
        border = "=" * 60
        sub_border = "-" * 60
        fmt_lines = "\n".join([f"  - {fmt}: {count} match(es)" for fmt, count in self.formats.items()]) or "  None"
        
        return f"""
{border}
            CRICSHEET HISTORICAL INGESTION REPORT
{border}
  Total Files Scanned      : {self.scanned_files}
  New Matches Imported     : {self.imported_matches}
  Existing Matches Updated : {self.updated_matches}
  Matches Failed           : {self.failed_matches}
  Total Players Registered : {self.total_players}
  Total Deliveries Stored  : {self.total_deliveries}
  Ingestion Runtime        : {self.duration_seconds:.2f} seconds
{sub_border}
  Formats Imported:
{fmt_lines}
{border}
"""

class CricsheetValidator:
    """
    Validates Cricsheet JSON match data against schema integrity rules.
    """
    @staticmethod
    def validate_match(data: Dict[str, Any], file_path: str = "") -> Tuple[bool, List[str]]:
        errors = []

        if not isinstance(data, dict):
            return False, ["JSON root is not an object/dictionary"]

        meta = data.get("meta")
        if not isinstance(meta, dict):
            errors.append("Missing or invalid 'meta' object")

        info = data.get("info")
        if not isinstance(info, dict):
            return False, ["Missing or invalid 'info' object"]

        teams = info.get("teams")
        if not isinstance(teams, list) or len(teams) < 2:
            errors.append(f"Match must specify at least 2 teams, found: {teams}")

        dates = info.get("dates")
        if not isinstance(dates, list) or len(dates) == 0:
            errors.append("Match must specify at least one valid date in 'dates' list")

        innings = data.get("innings")
        if not isinstance(innings, list):
            errors.append("Missing or invalid 'innings' array")
        else:
            # Validate deliveries inside innings
            for inn_idx, inn in enumerate(innings):
                if not isinstance(inn, dict):
                    errors.append(f"Innings {inn_idx} is not a dictionary")
                    continue
                overs = inn.get("overs", [])
                if not isinstance(overs, list):
                    errors.append(f"Innings {inn_idx} 'overs' must be a list")
                    continue

                for over_obj in overs:
                    deliveries = over_obj.get("deliveries", [])
                    for d_idx, d in enumerate(deliveries):
                        runs = d.get("runs", {})
                        if not isinstance(runs, dict):
                            errors.append(f"Delivery missing runs dictionary in over {over_obj.get('over')}")
                            continue

                        batter_runs = runs.get("batter", 0)
                        extras_runs = runs.get("extras", 0)
                        total_runs = runs.get("total", 0)

                        if not isinstance(batter_runs, int) or not isinstance(extras_runs, int) or not isinstance(total_runs, int):
                            errors.append(f"Runs values must be integers in delivery {d_idx}")
                        elif total_runs != (batter_runs + extras_runs):
                            errors.append(f"Run math mismatch: total ({total_runs}) != batter ({batter_runs}) + extras ({extras_runs})")

                        if not d.get("batter") or not d.get("bowler"):
                            errors.append("Delivery missing batter or bowler identifier")

        return len(errors) == 0, errors

class PlayerNormalizer:
    """
    Normalizes player names and assigns deterministic, consistent IDs.
    """
    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalizes unicode characters and whitespace.
        """
        if not name:
            return "Unknown Player"
        # Normalize unicode accents (e.g., cafés, diacritics in names)
        normalized = unicodedata.normalize("NFKD", name).strip()
        # Collapse multiple spaces
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @classmethod
    def create_player_id(cls, name: str, registry_people: Optional[Dict[str, str]] = None) -> Tuple[str, Optional[str]]:
        """
        Returns (consistent_player_id, cricsheet_registry_id).
        Prefers official 8-char Cricsheet hex registry ID if available.
        Falls back to sanitized slug.
        """
        cleaned_name = cls.normalize_name(name)
        registry_id = None

        if registry_people and isinstance(registry_people, dict):
            registry_id = registry_people.get(name) or registry_people.get(cleaned_name)

        if registry_id:
            # Canonical Cricsheet player ID
            player_id = f"p_{registry_id.lower().strip()}"
        else:
            # Deterministic slug
            slug = re.sub(r"[^a-z0-9_]", "", cleaned_name.lower().replace(" ", "_"))
            player_id = f"p_{slug}" if slug else "p_unknown"

        return player_id, registry_id

class HistoricalIngestionService:
    """
    Repeatable, transactional ingestion service for Cricsheet datasets.
    """
    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.db_manager = db_manager or sqlite_manager

    def find_raw_data_dir(self, explicit_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Locates the raw Cricsheet data directory (checking root data/raw or backend/data/raw).
        """
        if explicit_path:
            p = Path(explicit_path)
            if p.exists():
                return p

        # Check candidate locations
        candidates = [
            Path("data/raw"),
            Path("backend/data/raw"),
            Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw",
            Path(__file__).resolve().parent.parent.parent / "data" / "raw",
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                return c

        default_dir = Path("data/raw")
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir

    def ingest_single_match(
        self, 
        file_path: Union[str, Path], 
        conn: sqlite3.Connection,
        force_match_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Parses, validates, and transactionally inserts a single Cricsheet JSON file.
        Returns (success: bool, status: 'imported'|'updated'|'failed', error_msg: Optional[str]).
        """
        path = Path(file_path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return False, "failed", f"JSON Read Error in {path.name}: {str(e)}"

        # 1. Validate
        is_valid, validation_errors = CricsheetValidator.validate_match(data, str(path))
        if not is_valid:
            return False, "failed", f"Validation Failed: {'; '.join(validation_errors[:3])}"

        info = data.get("info", {})
        meta = data.get("meta", {})
        registry_people = info.get("registry", {}).get("people", {})

        # 2. Extract match ID (use stem or explicit)
        match_id = force_match_id or path.stem

        # Check if match already exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM matches WHERE id = ?;", (match_id,))
        existing_match = cursor.fetchone()
        status_action = "updated" if existing_match else "imported"

        # 3. Extract Metadata without inventing statistics
        data_version = meta.get("data_version", "")
        created_date = meta.get("created", "")
        source_file = str(path.as_posix())

        season = str(info.get("season", "Unknown"))
        dates = info.get("dates", [])
        date_str = str(dates[0]) if dates else "Unknown"

        raw_match_type = str(info.get("match_type", "T20"))
        match_type = FORMAT_MAP.get(raw_match_type.lower(), raw_match_type)
        gender = str(info.get("gender", "male"))

        venue = PlayerNormalizer.normalize_name(info.get("venue") or "Unknown Venue")
        city = PlayerNormalizer.normalize_name(info.get("city")) if info.get("city") else None

        teams = info.get("teams", [])
        team1 = PlayerNormalizer.normalize_name(teams[0]) if len(teams) > 0 else "Team 1"
        team2 = PlayerNormalizer.normalize_name(teams[1]) if len(teams) > 1 else "Team 2"

        toss = info.get("toss")
        toss_winner = PlayerNormalizer.normalize_name(toss.get("winner")) if toss and toss.get("winner") else None
        toss_decision = toss.get("decision") if toss else None

        outcome = info.get("outcome", {})
        winner = PlayerNormalizer.normalize_name(outcome.get("winner")) if outcome.get("winner") else None
        win_by_runs = outcome.get("by", {}).get("runs", 0) if isinstance(outcome.get("by"), dict) else 0
        win_by_wickets = outcome.get("by", {}).get("wickets", 0) if isinstance(outcome.get("by"), dict) else 0
        outcome_result = outcome.get("result", "normal" if winner else "no result")

        potm_raw = info.get("player_of_match", [])
        player_of_match = PlayerNormalizer.normalize_name(potm_raw[0]) if potm_raw else None
        overs_limit = info.get("overs", 20 if match_type == "T20" else (50 if match_type == "ODI" else 0))

        event = info.get("event", {})
        event_name = event.get("name") if isinstance(event, dict) else None
        match_number = event.get("match_number") if isinstance(event, dict) else None

        # 4. Transactional Writing
        try:
            # Teams
            for t_name in [team1, team2]:
                code = "".join([w[0].upper() for w in t_name.split() if w])[:4]
                cursor.execute(
                    "INSERT OR IGNORE INTO teams (id, name, short_code) VALUES (?, ?, ?);",
                    (t_name, t_name, code)
                )

            # Insert / Replace Match
            cursor.execute(
                """INSERT OR REPLACE INTO matches 
                   (id, season, date, match_type, gender, venue, city, team1, team2, 
                    toss_winner, toss_decision, winner, win_by_runs, win_by_wickets, outcome_result, 
                    player_of_match, overs_limit, event_name, match_number, data_version, created_date, source_file)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (match_id, season, date_str, match_type, gender, venue, city, team1, team2,
                 toss_winner, toss_decision, winner, win_by_runs, win_by_wickets, outcome_result,
                 player_of_match, overs_limit, event_name, match_number, data_version, created_date, source_file)
            )

            # Repeatable & Safe: Clean any previous deliveries for this match to prevent duplicates
            cursor.execute("DELETE FROM deliveries WHERE match_id = ?;", (match_id,))

            # Innings and Deliveries
            innings = data.get("innings", [])
            deliveries_rows = []
            players_to_save: Dict[str, Tuple[str, Optional[str]]] = {}

            for inn_idx, inn in enumerate(innings, start=1):
                batting_team = PlayerNormalizer.normalize_name(inn.get("team", ""))
                bowling_team = team2 if batting_team == team1 else team1
                overs_list = inn.get("overs", [])

                for over_obj in overs_list:
                    raw_over = over_obj.get("over", 0)  # Cricsheet overs are 0-indexed
                    over_number = raw_over + 1          # Store 1-indexed (1 to 20/50)
                    deliveries_list = over_obj.get("deliveries", [])

                    for ball_num, d in enumerate(deliveries_list, start=1):
                        batter_raw = d.get("batter", "")
                        bowler_raw = d.get("bowler", "")
                        non_striker_raw = d.get("non_striker", "")

                        batter = PlayerNormalizer.normalize_name(batter_raw)
                        bowler = PlayerNormalizer.normalize_name(bowler_raw)
                        non_striker = PlayerNormalizer.normalize_name(non_striker_raw) if non_striker_raw else None

                        b_id, b_cric = PlayerNormalizer.create_player_id(batter_raw, registry_people)
                        bw_id, bw_cric = PlayerNormalizer.create_player_id(bowler_raw, registry_people)
                        ns_id, ns_cric = (PlayerNormalizer.create_player_id(non_striker_raw, registry_people)) if non_striker_raw else (None, None)

                        players_to_save[batter] = (b_id, b_cric)
                        players_to_save[bowler] = (bw_id, bw_cric)
                        if non_striker and ns_id:
                            players_to_save[non_striker] = (ns_id, ns_cric)

                        runs = d.get("runs", {})
                        batsman_runs = runs.get("batter", 0)
                        extra_runs = runs.get("extras", 0)
                        total_runs = runs.get("total", 0)

                        # Extras classification
                        extras_dict = d.get("extras", {})
                        extras_type = list(extras_dict.keys())[0] if extras_dict else None

                        # Boundaries
                        is_six = 1 if batsman_runs == 6 else 0
                        is_boundary = 1 if (batsman_runs == 4 or batsman_runs == 6) else 0

                        # Wickets
                        wickets = d.get("wickets", [])
                        if wickets and len(wickets) > 0:
                            w = wickets[0]
                            is_wicket = 1
                            dismissed_player = PlayerNormalizer.normalize_name(w.get("player_out", ""))
                            dismissal_kind = w.get("kind", "out")
                            fielders_list = w.get("fielders", [])
                            fielder_name = PlayerNormalizer.normalize_name(fielders_list[0].get("name")) if fielders_list and fielders_list[0].get("name") else None
                        else:
                            is_wicket = 0
                            dismissed_player = None
                            dismissal_kind = None
                            fielder_name = None

                        deliveries_rows.append((
                            match_id, inn_idx, batting_team, bowling_team,
                            over_number, ball_num,
                            batter, b_id, bowler, bw_id, non_striker, ns_id,
                            batsman_runs, extra_runs, total_runs, extras_type,
                            is_wicket, dismissed_player, dismissal_kind, fielder_name,
                            is_boundary, is_six
                        ))

            # Bulk insert deliveries
            cursor.executemany(
                """INSERT INTO deliveries 
                   (match_id, inning, batting_team, bowling_team, over, ball,
                    batter, batter_id, bowler, bowler_id, non_striker, non_striker_id,
                    batsman_runs, extra_runs, total_runs, extras_type,
                    is_wicket, dismissed_player, dismissal_kind, fielder, is_boundary, is_six)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                deliveries_rows
            )

            # Insert / update players
            for p_name, (p_id, cric_id) in players_to_save.items():
                cursor.execute(
                    """INSERT OR IGNORE INTO players (id, name, cricsheet_id)
                       VALUES (?, ?, ?);""",
                    (p_id, p_name, cric_id)
                )
                if cric_id:
                    cursor.execute("UPDATE players SET cricsheet_id = ? WHERE id = ?;", (cric_id, p_id))

            conn.commit()
            return True, status_action, None

        except Exception as e:
            conn.rollback()
            return False, "failed", f"DB Transaction Error: {str(e)}"

    def ingest_raw_directory(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        formats: Optional[List[str]] = None,
        max_files: Optional[int] = None
    ) -> IngestionReport:
        """
        Scans data/raw and ingests all Cricsheet JSON matches across formats.
        Generates and prints a complete IngestionReport.
        """
        start_time = time.time()
        raw_dir = self.find_raw_data_dir(base_dir)
        report = IngestionReport()

        if not raw_dir.exists():
            report.duration_seconds = time.time() - start_time
            return report

        # Find all JSON files recursively
        all_json_files = list(raw_dir.rglob("*.json"))
        # Filter out READMEs or non-match JSONs
        valid_files = [f for f in all_json_files if not f.name.startswith("README")]
        report.scanned_files = len(valid_files)

        if max_files:
            valid_files = valid_files[:max_files]

        conn = self.db_manager.get_connection()

        try:
            for f_path in valid_files:
                # Determine folder format tag (e.g. data/raw/IPL/1082591.json -> IPL)
                rel_parts = f_path.relative_to(raw_dir).parts
                folder_tag = rel_parts[0] if len(rel_parts) > 1 else "Unknown"

                success, action, err = self.ingest_single_match(f_path, conn)

                if success:
                    if action == "imported":
                        report.imported_matches += 1
                    else:
                        report.updated_matches += 1

                    # Count formats
                    cursor = conn.cursor()
                    cursor.execute("SELECT match_type FROM matches WHERE id = ?;", (f_path.stem,))
                    row = cursor.fetchone()
                    fmt = row[0] if row else folder_tag
                    report.formats[fmt] = report.formats.get(fmt, 0) + 1
                else:
                    report.failed_matches += 1
                    report.errors.append({
                        "file": f_path.name,
                        "error": err or "Unknown ingestion error"
                    })

            # Retrieve total active counts
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM players;")
            report.total_players = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM deliveries;")
            report.total_deliveries = cursor.fetchone()[0]

        finally:
            conn.close()

        report.duration_seconds = time.time() - start_time
        return report

historical_ingestion_service = HistoricalIngestionService()

