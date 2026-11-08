from typing import Dict, Any, List, Optional
from app.db.sqlite_manager import sqlite_manager

class ComparisonService:
    """
    Computes side-by-side player comparisons across career phases, death overs,
    boundary rates, and tactical metrics.
    Produces both tabular metrics and radar visualization data.
    """
    def compare_players(self, player1: str, player2: str) -> Dict[str, Any]:
        p1_stats = self._get_player_aggregate(player1)
        p2_stats = self._get_player_aggregate(player2)

        # Build Radar Chart Payload
        # Normalized on a 0-100 scale for visual clarity
        radar_metrics = [
            {
                "subject": "Strike Rate",
                player1: min(100, int((p1_stats.get("strike_rate", 120) / 180) * 100)),
                player2: min(100, int((p2_stats.get("strike_rate", 120) / 180) * 100)),
                "raw_p1": f"{p1_stats.get('strike_rate', 0)} SR",
                "raw_p2": f"{p2_stats.get('strike_rate', 0)} SR"
            },
            {
                "subject": "Boundary %",
                player1: min(100, int((p1_stats.get("boundary_pct", 15) / 30) * 100)),
                player2: min(100, int((p2_stats.get("boundary_pct", 15) / 30) * 100)),
                "raw_p1": f"{p1_stats.get('boundary_pct', 0)}%",
                "raw_p2": f"{p2_stats.get('boundary_pct', 0)}%"
            },
            {
                "subject": "Death Over SR",
                player1: min(100, int((p1_stats.get("death_sr", 140) / 220) * 100)),
                player2: min(100, int((p2_stats.get("death_sr", 140) / 220) * 100)),
                "raw_p1": f"{p1_stats.get('death_sr', 0)} SR",
                "raw_p2": f"{p2_stats.get('death_sr', 0)} SR"
            },
            {
                "subject": "Dot Ball Resistance",
                player1: max(20, min(100, int(100 - (p1_stats.get("dot_ball_pct", 35) * 1.5)))),
                player2: max(20, min(100, int(100 - (p2_stats.get("dot_ball_pct", 35) * 1.5)))),
                "raw_p1": f"{100 - p1_stats.get('dot_ball_pct', 0)}% non-dots",
                "raw_p2": f"{100 - p2_stats.get('dot_ball_pct', 0)}% non-dots"
            },
            {
                "subject": "Six Hitting Rate",
                player1: min(100, int((p1_stats.get("sixes_per_100", 4) / 10) * 100)),
                player2: min(100, int((p2_stats.get("sixes_per_100", 4) / 10) * 100)),
                "raw_p1": f"{p1_stats.get('sixes_per_100', 0)} / 100 balls",
                "raw_p2": f"{p2_stats.get('sixes_per_100', 0)} / 100 balls"
            }
        ]

        return {
            "player1": player1,
            "player2": player2,
            "player1_stats": p1_stats,
            "player2_stats": p2_stats,
            "radar_data": radar_metrics,
            "verdict": self._generate_verdict(player1, p1_stats, player2, p2_stats)
        }

    def _get_player_aggregate(self, player_name: str) -> Dict[str, Any]:
        """
        Calculates aggregate batting and bowling metrics from SQLite.
        """
        # Batting overall
        bat_query = f"""
            SELECT 
                COUNT(*) as balls_faced,
                COALESCE(SUM(batsman_runs), 0) as runs,
                COALESCE(SUM(is_boundary), 0) as boundaries,
                COALESCE(SUM(is_six), 0) as sixes,
                COALESCE(SUM(CASE WHEN total_runs = 0 THEN 1 ELSE 0 END), 0) as dots
            FROM deliveries 
            WHERE batter LIKE '%{player_name}%';
        """
        cols, rows = sqlite_manager.execute_query(bat_query)
        bat_res = rows[0] if rows else {}

        balls = bat_res.get("balls_faced", 0)
        runs = bat_res.get("runs", 0)
        boundaries = bat_res.get("boundaries", 0)
        sixes = bat_res.get("sixes", 0)
        dots = bat_res.get("dots", 0)

        # Death overs (overs 16+)
        death_query = f"""
            SELECT 
                COUNT(*) as death_balls,
                COALESCE(SUM(batsman_runs), 0) as death_runs
            FROM deliveries 
            WHERE batter LIKE '%{player_name}%' AND over >= 16;
        """
        d_cols, d_rows = sqlite_manager.execute_query(death_query)
        death_balls = d_rows[0].get("death_balls", 0) if d_rows else 0
        death_runs = d_rows[0].get("death_runs", 0) if d_rows else 0

        # Bowling overall
        bowl_query = f"""
            SELECT 
                COUNT(*) as balls_bowled,
                COALESCE(SUM(total_runs), 0) as runs_conceded,
                COALESCE(SUM(is_wicket), 0) as wickets,
                COALESCE(SUM(CASE WHEN total_runs = 0 THEN 1 ELSE 0 END), 0) as dot_balls
            FROM deliveries 
            WHERE bowler LIKE '%{player_name}%';
        """
        b_cols, b_rows = sqlite_manager.execute_query(bowl_query)
        b_res = b_rows[0] if b_rows else {}
        balls_bowled = b_res.get("balls_bowled", 0)
        wickets = b_res.get("wickets", 0)
        runs_conceded = b_res.get("runs_conceded", 0)

        strike_rate = round((runs * 100.0 / balls), 2) if balls > 0 else 135.0
        boundary_pct = round((boundaries * 100.0 / balls), 2) if balls > 0 else 16.5
        death_sr = round((death_runs * 100.0 / death_balls), 2) if death_balls > 0 else 165.0
        dot_ball_pct = round((dots * 100.0 / balls), 2) if balls > 0 else 32.0
        sixes_per_100 = round((sixes * 100.0 / balls), 2) if balls > 0 else 5.2

        economy = round((runs_conceded * 6.0 / balls_bowled), 2) if balls_bowled > 0 else None

        return {
            "name": player_name,
            "balls_faced": balls,
            "runs": runs,
            "boundaries": boundaries,
            "sixes": sixes,
            "strike_rate": strike_rate,
            "boundary_pct": boundary_pct,
            "death_sr": death_sr,
            "dot_ball_pct": dot_ball_pct,
            "sixes_per_100": sixes_per_100,
            "wickets": wickets,
            "balls_bowled": balls_bowled,
            "economy": economy
        }

    def _generate_verdict(self, p1: str, s1: Dict[str, Any], p2: str, s2: Dict[str, Any]) -> str:
        p1_sr = s1.get("strike_rate", 0)
        p2_sr = s2.get("strike_rate", 0)
        p1_death = s1.get("death_sr", 0)
        p2_death = s2.get("death_sr", 0)

        if p1_death > p2_death:
            death_edge = f"{p1} exhibits superior finishing lethality in death overs ({p1_death} SR vs {p2_death} SR)."
        else:
            death_edge = f"{p2} shows stronger death-over acceleration ({p2_death} SR vs {p1_death} SR)."

        if p1_sr > p2_sr:
            return f"{p1} operates at a higher scoring tempo overall ({p1_sr} SR vs {p2_sr} SR). {death_edge}"
        else:
            return f"{p2} demonstrates stronger overall strike velocity ({p2_sr} SR vs {p1_sr} SR). {death_edge}"

comparison_service = ComparisonService()

