import re
from typing import Dict, Any, Tuple, List, Optional
from google import genai
from app.core.config import settings
from app.db.sqlite_manager import sqlite_manager

VALID_TABLES = {"matches", "deliveries", "players", "teams"}
FORBIDDEN_KEYWORDS = [
    "drop", "delete", "truncate", "update", "insert", 
    "alter", "create", "replace", "pragma", "vacuum", "attach", "detach"
]

class SQLQueryService:
    """
    Translates natural language cricket questions into safe, optimized SQLite queries,
    validates syntax and read-only safety, and provides a self-healing repair mechanism.
    """
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self._client: Optional[genai.Client] = None
        if self.api_key and self.api_key.strip():
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Gemini Client ({e})")

    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validates that the SQL query is strictly read-only, contains no DDL/DML,
        and targets known tables.
        """
        cleaned = sql_query.strip()
        lowered = cleaned.lower()

        if not lowered.startswith("select"):
            return False, "Query must strictly start with SELECT"

        for kw in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", lowered):
                return False, f"Forbidden keyword '{kw}' detected. Only read-only SELECT queries are allowed."

        # Check that query references at least one valid table
        has_valid_table = any(table in lowered for table in VALID_TABLES)
        if not has_valid_table:
            return False, f"Query must reference one of the valid tables: {VALID_TABLES}"

        return True, None

    def generate_and_execute(self, query: str) -> Dict[str, Any]:
        """
        Converts question to SQL, validates it, executes against SQLite,
        and returns structured tabular output.
        """
        schema_prompt = sqlite_manager.get_schema_summary()
        sql_query = self._generate_sql(query, schema_prompt)
        
        is_valid, validation_err = self.validate_sql(sql_query)
        if not is_valid:
            # Attempt repair
            sql_query = self.repair_sql(query, sql_query, validation_err or "Invalid SQL syntax")

        try:
            columns, rows = sqlite_manager.execute_query(sql_query)
            return {
                "success": True,
                "sql_query": sql_query,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "error": None
            }
        except Exception as e:
            # Self-healing retry
            repaired_sql = self.repair_sql(query, sql_query, str(e))
            try:
                columns, rows = sqlite_manager.execute_query(repaired_sql)
                return {
                    "success": True,
                    "sql_query": repaired_sql,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "error": None,
                    "was_repaired": True
                }
            except Exception as e2:
                return {
                    "success": False,
                    "sql_query": repaired_sql,
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "error": f"Execution failed after repair: {str(e2)}"
                }

    def repair_sql(self, query: str, failed_sql: str, error_message: str) -> str:
        """
        Self-healing engine: corrects failed SQL queries based on error feedback and schema.
        """
        schema_prompt = sqlite_manager.get_schema_summary()
        
        if self._client:
            prompt = f"""
You are an expert SQLite repair engineer. The following SQL query failed with an error. 
Please correct the SQL query so it runs successfully on SQLite.

ORIGINAL QUESTION:
{query}

FAILED SQL QUERY:
{failed_sql}

ERROR MESSAGE:
{error_message}

CRICKET DATABASE SCHEMA:
{schema_prompt}

RULES:
1. ONLY return the single corrected SQL query. Do NOT add explanation, markdown code blocks, or comments.
2. Must be a SELECT query.
3. Ensure column names strictly match the schema (e.g. `batter` instead of `batsman`, `batsman_runs` instead of `runs`).
"""
            try:
                res = self._client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
                cleaned = self._clean_markdown(res.text)
                return cleaned
            except Exception:
                pass

        # Rule-based fallback repair
        repaired = failed_sql
        # Common column alias fixes
        repaired = re.sub(r"\bbatsman\b", "batter", repaired, flags=re.IGNORECASE)
        repaired = re.sub(r"\bruns\b(?!\s*conceded)", "batsman_runs", repaired, flags=re.IGNORECASE)
        repaired = re.sub(r"\bmatch_winner\b", "winner", repaired, flags=re.IGNORECASE)
        
        # Ensure it has a LIMIT if missing
        if "limit" not in repaired.lower():
            repaired = repaired.rstrip(";") + " LIMIT 15;"

        return repaired

    def _generate_sql(self, query: str, schema_info: str) -> str:
        """
        Invokes Gemini with system prompt instructing valid SQLite syntax,
        or uses rule-based heuristic generation.
        """
        if self._client:
            prompt = f"""
You are an expert Cricket SQL Data Analyst. Generate a single, highly accurate, read-only SQLite SELECT query to answer the user's question.

CRICKET DATABASE SCHEMA:
{schema_info}

CRICKET STATISTICAL GUIDELINES:
1. ONLY return the raw SQL query. Do NOT include markdown code blocks, backticks, or explanations.
2. The query MUST be a SELECT statement. Never use INSERT, UPDATE, DELETE, or DROP.
3. For player names, use `LIKE '%PlayerName%'` (e.g. `batter LIKE '%Kohli%'` or `bowler LIKE '%Bumrah%'`).
4. To calculate strike rate: `ROUND(SUM(batsman_runs) * 100.0 / COUNT(*), 2)`.
5. To calculate economy rate: `ROUND(SUM(total_runs) * 6.0 / COUNT(*), 2)`.
6. To calculate bowling average: `ROUND(SUM(total_runs) * 1.0 / NULLIF(SUM(is_wicket), 0), 2)`.
7. Death overs are overs 16 to 20 (`over >= 16`). Powerplay is overs 1 to 6 (`over <= 6`).
8. Dot balls: `SUM(CASE WHEN total_runs = 0 THEN 1 ELSE 0 END)`.
9. Always add `LIMIT 20` unless explicitly querying for all.

USER QUESTION:
{query}
"""
            try:
                response = self._client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt
                )
                cleaned = self._clean_markdown(response.text)
                return cleaned
            except Exception as e:
                print(f"Gemini SQL generation fallback ({e})")

        # Heuristic rules for common cricket statistical queries
        lowered = query.lower()
        if "six" in lowered or "death" in lowered:
            return "SELECT batter, COUNT(*) as balls, SUM(batsman_runs) as total_runs, SUM(is_six) as sixes, SUM(is_boundary) as boundaries, ROUND(SUM(batsman_runs)*100.0/COUNT(*), 2) as strike_rate FROM deliveries WHERE over >= 16 GROUP BY batter ORDER BY sixes DESC LIMIT 10;"
        elif "bumrah" in lowered or "economy" in lowered or "bowler" in lowered:
            return "SELECT bowler, COUNT(*) as balls_bowled, SUM(is_wicket) as wickets, SUM(total_runs) as runs_conceded, ROUND(SUM(total_runs)*6.0/COUNT(*), 2) as economy FROM deliveries GROUP BY bowler ORDER BY wickets DESC, economy ASC LIMIT 10;"
        elif "kohli" in lowered:
            return "SELECT batter, COUNT(*) as balls_faced, SUM(batsman_runs) as runs, SUM(is_boundary) as fours, SUM(is_six) as sixes, ROUND(SUM(batsman_runs)*100.0/COUNT(*), 2) as strike_rate FROM deliveries WHERE batter LIKE '%Kohli%' GROUP BY batter;"
        elif "head to head" in lowered or "winner" in lowered or "final" in lowered:
            return "SELECT id, season, date, match_type, venue, team1, team2, winner, win_by_runs, win_by_wickets, player_of_match FROM matches ORDER BY date DESC LIMIT 10;"
        else:
            return "SELECT batter, COUNT(*) as balls_faced, SUM(batsman_runs) as runs, SUM(is_boundary) as fours, SUM(is_six) as sixes, ROUND(SUM(batsman_runs)*100.0/COUNT(*), 2) as strike_rate FROM deliveries GROUP BY batter ORDER BY runs DESC LIMIT 10;"

    def _clean_markdown(self, raw_text: str) -> str:
        text = raw_text.strip()
        text = re.sub(r"^```(sql)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
        return text

sql_query_service = SQLQueryService()
