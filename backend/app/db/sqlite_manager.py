import os
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.db.models import Base, Match, Delivery, Player, Team

DATABASE_URL = f"sqlite:///{settings.SQLITE_DB_PATH.as_posix()}"

# Configure SQLAlchemy engine with WAL mode and foreign key enforcement
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30.0},
    echo=False,
    pool_pre_ping=True
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SQLiteManager:
    """
    Manages automatic SQLite initialization, table creation, schema migrations,
    indexing, and health monitoring using SQLAlchemy.
    Requires ZERO manual setup from the user.
    Preserves all existing data across restarts without overwriting.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self.engine = engine if (db_path is None or db_path == settings.SQLITE_DB_PATH) else create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False, "timeout": 30.0}
        )

    def get_connection(self) -> sqlite3.Connection:
        """
        Provides direct sqlite3 connection for high-throughput batch ingestion operations.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def get_session(self) -> Session:
        return Session(bind=self.engine)

    def initialize_database(self) -> Dict[str, Any]:
        """
        Auto-creates normalized tables and relationships using SQLAlchemy metadata.
        Applies migrations for any missing columns and preserves existing records.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. SQLAlchemy auto-table creation (checkfirst=True avoids overwriting)
        Base.metadata.create_all(bind=self.engine, checkfirst=True)

        # 2. Schema Migrations (safely add columns if older database instance exists)
        self._apply_migrations()

        # 3. Check existing records to preserve them without overwriting
        with self.get_session() as session:
            match_count = session.query(Match).count()
            player_count = session.query(Player).count()
            delivery_count = session.query(Delivery).count()

            # Only seed if the database is brand new and completely empty
            if match_count == 0 and player_count == 0:
                self._seed_starter_dataset(session)
                match_count = session.query(Match).count()
                player_count = session.query(Player).count()
                delivery_count = session.query(Delivery).count()

        return {
            "status": "ready",
            "db_path": str(self.db_path),
            "matches": match_count,
            "players": player_count,
            "deliveries": delivery_count,
        }

    def _apply_migrations(self):
        """
        Inspects existing tables via SQLAlchemy inspector and executes ALTER TABLE
        for any newly added columns.
        """
        inspector = inspect(self.engine)
        table_migrations = {
            "matches": {
                "outcome_result": "TEXT DEFAULT 'normal'",
                "event_name": "TEXT",
                "match_number": "INTEGER",
                "data_version": "TEXT",
                "created_date": "TEXT",
                "source_file": "TEXT"
            },
            "deliveries": {
                "batter_id": "TEXT",
                "bowler_id": "TEXT",
                "non_striker_id": "TEXT",
                "extras_type": "TEXT",
                "fielder": "TEXT"
            },
            "players": {
                "cricsheet_id": "TEXT"
            }
        }

        with self.engine.connect() as conn:
            for table_name, columns in table_migrations.items():
                if inspector.has_table(table_name):
                    existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                    for col_name, col_type in columns.items():
                        if col_name not in existing_cols:
                            try:
                                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"))
                                conn.commit()
                            except Exception:
                                pass

    def health_check(self) -> Dict[str, Any]:
        """
        Performs connectivity, schema verification, and latency tests.
        """
        start_time = time.perf_counter()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT 1;")).fetchone()
                connected = (res is not None and res[0] == 1)

            with self.get_session() as session:
                matches_count = session.query(Match).count()
                deliveries_count = session.query(Delivery).count()
                players_count = session.query(Player).count()
                teams_count = session.query(Team).count()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "status": "healthy" if connected else "unhealthy",
                "engine": "SQLAlchemy + SQLite",
                "database_path": str(self.db_path),
                "size_mb": round(db_size_bytes / (1024 * 1024), 2),
                "latency_ms": latency_ms,
                "counts": {
                    "matches": matches_count,
                    "deliveries": deliveries_count,
                    "players": players_count,
                    "teams": teams_count
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_path": str(self.db_path)
            }

    def execute_query(self, query: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Safely executes a read-only SELECT query against SQLite.
        Returns (column_names, rows).
        """
        cleaned_query = query.strip()
        lowered = cleaned_query.lower()

        # Security Guardrail: Read-only check
        forbidden_keywords = ["drop", "delete", "truncate", "update", "insert", "alter", "create", "replace", "pragma", "vacuum"]
        for kw in forbidden_keywords:
            if f"{kw} " in lowered or f";{kw}" in lowered:
                raise ValueError(f"Forbidden DDL/DML keyword '{kw}' detected. Only SELECT queries are permitted.")

        with self.engine.connect() as connection:
            result = connection.execute(text(cleaned_query))
            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return columns, rows
            return [], []

    def get_schema_summary(self) -> str:
        """
        Returns a concise DDL schema description to pass to the LLM Text-to-SQL engine.
        """
        inspector = inspect(self.engine)
        schema_lines = []

        tables = ["matches", "deliveries", "players", "teams"]
        for table in tables:
            if inspector.has_table(table):
                cols = inspector.get_columns(table)
                cols_str = ", ".join([f"{col['name']} ({col['type']})" for col in cols])
                schema_lines.append(f"Table '{table}': {cols_str}")

        return "\n".join(schema_lines)

    def _seed_starter_dataset(self, session: Session):
        """
        Seeds initial realistic records if the database is newly initialized.
        """
        # Seed Key Players
        seed_players = [
            Player(id="p_vkohli", name="Virat Kohli", cricsheet_id="b0682224", country="India", batting_style="Right-hand bat", bowling_style="Right-arm medium", role="Batter"),
            Player(id="p_rsharma", name="Rohit Sharma", cricsheet_id="c1783335", country="India", batting_style="Right-hand bat", bowling_style="Right-arm offbreak", role="Batter"),
            Player(id="p_jbumrah", name="Jasprit Bumrah", cricsheet_id="d2894446", country="India", batting_style="Right-hand bat", bowling_style="Right-arm fast", role="Bowler"),
            Player(id="p_msdhoni", name="MS Dhoni", cricsheet_id="e3905557", country="India", batting_style="Right-hand bat", bowling_style="Right-arm medium", role="Wicketkeeper"),
            Player(id="p_babar", name="Babar Azam", cricsheet_id="f4016668", country="Pakistan", batting_style="Right-hand bat", bowling_style="Right-arm offbreak", role="Batter"),
            Player(id="p_safridi", name="Shaheen Afridi", cricsheet_id="a5127779", country="Pakistan", batting_style="Left-hand bat", bowling_style="Left-arm fast", role="Bowler"),
            Player(id="p_ssmith", name="Steve Smith", cricsheet_id="b6238880", country="Australia", batting_style="Right-hand bat", bowling_style="Right-arm legbreak", role="Batter"),
            Player(id="p_thead", name="Travis Head", cricsheet_id="c7349991", country="Australia", batting_style="Left-hand bat", bowling_style="Right-arm offbreak", role="Batter"),
            Player(id="p_mstarc", name="Mitchell Starc", cricsheet_id="d8450002", country="Australia", batting_style="Left-hand bat", bowling_style="Left-arm fast", role="Bowler"),
            Player(id="p_pcummins", name="Pat Cummins", cricsheet_id="e9561113", country="Australia", batting_style="Right-hand bat", bowling_style="Right-arm fast", role="Bowler"),
            Player(id="p_bstokes", name="Ben Stokes", cricsheet_id="f0672224", country="England", batting_style="Left-hand bat", bowling_style="Right-arm fast-medium", role="All-rounder"),
            Player(id="p_jbuttler", name="Jos Buttler", cricsheet_id="a1783335", country="England", batting_style="Right-hand bat", bowling_style="None", role="Wicketkeeper"),
            Player(id="p_rkhan", name="Rashid Khan", cricsheet_id="b2894446", country="Afghanistan", batting_style="Right-hand bat", bowling_style="Right-arm legbreak", role="Bowler"),
            Player(id="p_hklaasen", name="Heinrich Klaasen", cricsheet_id="c3905557", country="South Africa", batting_style="Right-hand bat", bowling_style="Right-arm offbreak", role="Batter"),
            Player(id="p_kgill", name="Shubman Gill", cricsheet_id="d4016668", country="India", batting_style="Right-hand bat", bowling_style="Right-arm offbreak", role="Batter"),
            Player(id="p_skyadav", name="Suryakumar Yadav", cricsheet_id="e5127779", country="India", batting_style="Right-hand bat", bowling_style="Right-arm medium", role="Batter"),
            Player(id="p_hpandya", name="Hardik Pandya", cricsheet_id="f6238880", country="India", batting_style="Right-hand bat", bowling_style="Right-arm fast-medium", role="All-rounder"),
        ]
        session.bulk_save_objects(seed_players)

        # Seed Teams
        seed_teams = [
            Team(id="IND", name="India", short_code="IND"),
            Team(id="AUS", name="Australia", short_code="AUS"),
            Team(id="ENG", name="England", short_code="ENG"),
            Team(id="PAK", name="Pakistan", short_code="PAK"),
            Team(id="SA", name="South Africa", short_code="SA"),
            Team(id="AFG", name="Afghanistan", short_code="AFG"),
            Team(id="NZ", name="New Zealand", short_code="NZ"),
            Team(id="MI", name="Mumbai Indians", short_code="MI"),
            Team(id="CSK", name="Chennai Super Kings", short_code="CSK"),
            Team(id="RCB", name="Royal Challengers Bangalore", short_code="RCB"),
            Team(id="KKR", name="Kolkata Knight Riders", short_code="KKR"),
            Team(id="SRH", name="Sunrisers Hyderabad", short_code="SRH"),
        ]
        session.bulk_save_objects(seed_teams)

        # Seed Sample Matches
        m1 = Match(
            id="m_t20wc_2022_ind_pak",
            season="2022/23",
            date="2022-10-23",
            match_type="T20",
            venue="Melbourne Cricket Ground",
            city="Melbourne",
            team1="Pakistan",
            team2="India",
            toss_winner="India",
            toss_decision="field",
            winner="India",
            win_by_wickets=4,
            win_by_runs=0,
            outcome_result="normal",
            player_of_match="Virat Kohli",
            overs_limit=20,
            event_name="ICC Men's T20 World Cup",
            match_number=16,
            data_version="1.3.0",
            created_date="2022-10-24",
            source_file="seed://mcg_2022"
        )
        m2 = Match(
            id="m_t20wc_2024_final_ind_sa",
            season="2024",
            date="2024-06-29",
            match_type="T20",
            venue="Kensington Oval, Bridgetown",
            city="Barbados",
            team1="India",
            team2="South Africa",
            toss_winner="India",
            toss_decision="bat",
            winner="India",
            win_by_runs=7,
            win_by_wickets=0,
            outcome_result="normal",
            player_of_match="Virat Kohli",
            overs_limit=20,
            event_name="ICC Men's T20 World Cup",
            match_number=55,
            data_version="1.3.0",
            created_date="2024-06-30",
            source_file="seed://barbados_2024"
        )
        session.bulk_save_objects([m1, m2])

        # Seed deliveries
        deliveries = [
            Delivery(match_id="m_t20wc_2022_ind_pak", inning=2, batting_team="India", bowling_team="Pakistan", over=19, ball=5, batter="Virat Kohli", batter_id="p_vkohli", bowler="Haris Rauf", bowler_id="p_hrauf", non_striker="Hardik Pandya", non_striker_id="p_hpandya", batsman_runs=6, extra_runs=0, total_runs=6, is_boundary=True, is_six=True),
            Delivery(match_id="m_t20wc_2022_ind_pak", inning=2, batting_team="India", bowling_team="Pakistan", over=19, ball=6, batter="Virat Kohli", batter_id="p_vkohli", bowler="Haris Rauf", bowler_id="p_hrauf", non_striker="Hardik Pandya", non_striker_id="p_hpandya", batsman_runs=6, extra_runs=0, total_runs=6, is_boundary=True, is_six=True),
            Delivery(match_id="m_t20wc_2024_final_ind_sa", inning=2, batting_team="South Africa", bowling_team="India", over=16, ball=1, batter="Heinrich Klaasen", batter_id="p_hklaasen", bowler="Jasprit Bumrah", bowler_id="p_jbumrah", non_striker="David Miller", non_striker_id="p_dmiller", batsman_runs=0, extra_runs=0, total_runs=0),
            Delivery(match_id="m_t20wc_2024_final_ind_sa", inning=2, batting_team="South Africa", bowling_team="India", over=18, ball=1, batter="Marco Jansen", batter_id="p_mjansen", bowler="Jasprit Bumrah", bowler_id="p_jbumrah", non_striker="David Miller", non_striker_id="p_dmiller", batsman_runs=0, extra_runs=0, total_runs=0, is_wicket=True, dismissed_player="Marco Jansen", dismissal_kind="bowled"),
        ]
        session.bulk_save_objects(deliveries)
        session.commit()

sqlite_manager = SQLiteManager()
