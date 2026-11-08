import time
import httpx
from typing import Dict, Any, List, Optional
from cachetools import TTLCache
from app.core.config import settings

class LiveCricketService:
    """
    Handles live match polling, live scorecard tracking, and commentary.
    Implements TTL caching to respect rate limits, with a comprehensive
    live match mock engine when no live international match is currently in play.
    """
    def __init__(self):
        # 30-second TTL cache for live match lists and scorecards
        self._matches_cache = TTLCache(maxsize=10, ttl=30)
        self._scorecard_cache = TTLCache(maxsize=50, ttl=15)
        self.api_key = settings.CRICKET_API_KEY
        self.base_url = settings.CRICKET_API_BASE_URL

    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """
        Retrieves active ongoing cricket matches.
        """
        cache_key = "current_live_matches"
        if cache_key in self._matches_cache:
            return self._matches_cache[cache_key]

        if self.api_key and self.api_key.strip():
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(
                        f"{self.base_url}/currentMatches",
                        params={"apikey": self.api_key, "offset": 0}
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        if data:
                            self._matches_cache[cache_key] = data
                            return data
            except Exception as e:
                # Log error and gracefully fall back to simulation
                print(f"Warning: Live API call failed ({e}). Falling back to live simulation engine.")

        # Default fallback to realistic simulated live matches
        matches = self._get_simulated_live_matches()
        self._matches_cache[cache_key] = matches
        return matches

    async def get_match_scorecard(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed scorecard, commentary, and ball-by-ball updates for a match.
        """
        if match_id in self._scorecard_cache:
            return self._scorecard_cache[match_id]

        if self.api_key and self.api_key.strip() and not match_id.startswith("sim_"):
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(
                        f"{self.base_url}/match_scorecard",
                        params={"apikey": self.api_key, "id": match_id}
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        if data:
                            self._scorecard_cache[match_id] = data
                            return data
            except Exception as e:
                print(f"Warning: Scorecard fetch failed ({e}). Returning simulated match state.")

        scorecard = self._get_simulated_scorecard(match_id)
        if scorecard:
            self._scorecard_cache[match_id] = scorecard
        return scorecard

    def _get_simulated_live_matches(self) -> List[Dict[str, Any]]:
        """
        Generates realistic ongoing match telemetry with live overs, run rates, and active batters.
        """
        return [
            {
                "id": "sim_ind_aus_scg_2026",
                "name": "India vs Australia, 3rd T20I",
                "matchType": "t20",
                "status": "India need 44 runs in 28 balls to win",
                "venue": "Sydney Cricket Ground, Sydney",
                "date": "2026-11-08",
                "teams": ["India", "Australia"],
                "teamInfo": [
                    {"name": "Australia", "shortname": "AUS"},
                    {"name": "India", "shortname": "IND"}
                ],
                "score": [
                    {"r": 186, "w": 5, "o": 20, "inning": "Australia Inning 1"},
                    {"r": 143, "w": 3, "o": 15.2, "inning": "India Inning 2"}
                ],
                "series_id": "series_ind_aus_2026",
                "is_live": True
            },
            {
                "id": "sim_eng_pak_gaddafi_2026",
                "name": "Pakistan vs England, 2nd Test",
                "matchType": "test",
                "status": "Day 3 - Pakistan lead by 182 runs",
                "venue": "Gaddafi Stadium, Lahore",
                "date": "2026-11-08",
                "teams": ["Pakistan", "England"],
                "teamInfo": [
                    {"name": "Pakistan", "shortname": "PAK"},
                    {"name": "England", "shortname": "ENG"}
                ],
                "score": [
                    {"r": 366, "w": 10, "o": 112.4, "inning": "Pakistan Inning 1"},
                    {"r": 291, "w": 10, "o": 84.2, "inning": "England Inning 1"},
                    {"r": 107, "w": 2, "o": 34.0, "inning": "Pakistan Inning 2"}
                ],
                "series_id": "series_eng_pak_2026",
                "is_live": True
            }
        ]

    def _get_simulated_scorecard(self, match_id: str) -> Dict[str, Any]:
        """
        Detailed breakdown for live queries (batting figures, bowling spell, recent commentary).
        """
        if "eng_pak" in match_id:
            return {
                "id": "sim_eng_pak_gaddafi_2026",
                "name": "Pakistan vs England, 2nd Test",
                "venue": "Gaddafi Stadium, Lahore",
                "status": "Day 3: Session 2 - Pakistan lead by 182 runs with 8 wickets in hand",
                "current_batters": [
                    {"name": "Babar Azam", "runs": 64, "balls": 118, "fours": 7, "sixes": 1, "strike_rate": 54.2},
                    {"name": "Shan Masood", "runs": 32, "balls": 74, "fours": 3, "sixes": 0, "strike_rate": 43.2}
                ],
                "current_bowler": {
                    "name": "Jack Leach", "overs": 14.0, "maidens": 2, "runs": 48, "wickets": 1, "economy": 3.42
                },
                "summary": "Pakistan are consolidating their lead in Lahore on a turning surface."
            }

        # SCG T20I thriller simulation
        return {
            "id": "sim_ind_aus_scg_2026",
            "name": "India vs Australia, 3rd T20I",
            "venue": "Sydney Cricket Ground, Sydney",
            "status": "India need 44 runs in 28 balls to win (RRR: 9.43)",
            "current_innings": 2,
            "target": 187,
            "required_runs": 44,
            "remaining_balls": 28,
            "current_run_rate": 9.32,
            "required_run_rate": 9.43,
            "current_batters": [
                {"name": "Virat Kohli", "runs": 68, "balls": 44, "fours": 6, "sixes": 3, "strike_rate": 154.5},
                {"name": "Hardik Pandya", "runs": 22, "balls": 11, "fours": 2, "sixes": 1, "strike_rate": 200.0}
            ],
            "current_bowler": {
                "name": "Mitchell Starc", "overs": 3.2, "maidens": 0, "runs": 34, "wickets": 1, "economy": 10.2
            },
            "recent_balls": ["1", "4", "1", "W", "2", "6", "1"],
            "commentary_highlights": [
                "15.2 - Mitchell Starc to Virat Kohli, 1 run, driven firmly down to long-off.",
                "15.1 - Mitchell Starc to Hardik Pandya, SIX! In the slot and hoisted over deep midwicket into the SCG stands!",
                "14.6 - Pat Cummins to Virat Kohli, 2 runs, flicked through midwicket with exquisite placement.",
                "14.5 - Pat Cummins to Suryakumar Yadav, OUT! Caught at deep backward point. Big breakthrough for Australia!"
            ]
        }

live_cricket_service = LiveCricketService()

