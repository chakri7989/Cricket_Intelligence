import re
from typing import Dict, Any, List, Optional, Tuple
from app.db.sqlite_manager import sqlite_manager
from app.db.chromadb_manager import chroma_manager

CANONICAL_CRICKET_RULES = [
    {
        "id": "rule_dls_method",
        "title": "Duckworth-Lewis-Stern (DLS) Method",
        "text": (
            "The Duckworth-Lewis-Stern (DLS) method is a mathematical formula designed to calculate the target score "
            "for the team batting second in a limited-overs cricket match interrupted by weather or other circumstances. "
            "It is based on the principle that teams have two resources available to make runs: the number of overs "
            "remaining and the number of wickets in hand. As overs and wickets are consumed, the resource percentage decreases. "
            "If an interruption occurs, the target score is adjusted proportionately to ensure fairness to both sides based on "
            "resource tables maintained by the ICC."
        ),
        "metadata": {"type": "rule", "topic": "DLS Method", "category": "match_regulations"}
    },
    {
        "id": "rule_super_over",
        "title": "Super Over Tiebreaker Rules",
        "text": (
            "A Super Over is used to break ties in limited-overs knockout matches and T20 games. "
            "Each team nominates three batsmen and one bowler to play a single six-ball over per side. "
            "If two wickets fall, that team's innings terminates immediately. "
            "Following the 2019 World Cup Final controversy, the ICC amended the rules: if a Super Over is tied, "
            "subsequent Super Overs are played until one team scores more runs, completely eliminating the former boundary countback rule."
        ),
        "metadata": {"type": "rule", "topic": "Super Over", "category": "tiebreaker"}
    },
    {
        "id": "rule_boundary_countback",
        "title": "Boundary Countback Rule Controversy",
        "text": (
            "The boundary countback rule was an ICC tiebreaker clause invoked during the 2019 Men's Cricket World Cup Final "
            "between England and New Zealand at Lord's. After both the standard 50-over match (241 runs each) and the Super Over "
            "(15 runs each) ended in ties, England were awarded the trophy having hit 26 boundaries (fours and sixes) to New Zealand's 17. "
            "The controversy prompted intense criticism, leading the ICC to abolish boundary countback and replace it with repeated Super Overs."
        ),
        "metadata": {"type": "trivia_rule", "topic": "Boundary Countback", "category": "historical_controversy"}
    },
    {
        "id": "rule_powerplay_t20_odi",
        "title": "Powerplay Fielding Restrictions",
        "text": (
            "Powerplays place strict limits on how many fielders can be positioned outside the 30-yard circle. "
            "In T20 cricket, overs 1 through 6 constitute the mandatory Powerplay, where only 2 fielders may field outside the circle. "
            "In 50-over ODIs, there are three phases: Mandatory Powerplay 1 (overs 1–10, maximum 2 fielders outside), "
            "Powerplay 2 (overs 11–40, maximum 4 fielders outside), and Powerplay 3 (overs 41–50, maximum 5 fielders outside)."
        ),
        "metadata": {"type": "rule", "topic": "Powerplay Restrictions", "category": "fielding_regulations"}
    },
    {
        "id": "rule_free_hit",
        "title": "Free Hit Delivery Rule",
        "text": (
            "In limited-overs cricket, any delivery deemed a No-Ball (for front-foot overstepping, height above waist, or fielding restriction breach) "
            "results in an immediate Free Hit on the subsequent legal ball. "
            "On a Free Hit delivery, the batsman cannot be dismissed by any means other than run out, obstructing the field, or hitting the ball twice. "
            "Fielders cannot change positions unless the batsmen changed ends on the preceding No-Ball."
        ),
        "metadata": {"type": "rule", "topic": "Free Hit", "category": "playing_conditions"}
    },
    {
        "id": "rule_lbw_drs",
        "title": "LBW and Decision Review System (DRS) Guidelines",
        "text": (
            "For a batsman to be dismissed Leg Before Wicket (LBW) under MCC Law 36, the ball must not be a no-ball, "
            "must pitch in line with the stumps or on the off side (never outside leg stump), must strike the batsman in line with the stumps "
            "(unless no stroke is offered, in which case impact outside off stump is allowed), and would have gone on to hit the stumps. "
            "Under DRS ball-tracking, 'Umpire's Call' is returned if more than 50% of the ball does not satisfy the tracking zone margins."
        ),
        "metadata": {"type": "rule", "topic": "LBW and DRS", "category": "laws_of_cricket"}
    }
]

class NarrativeIndexer:
    """
    Synthesizes rich natural language match summaries and tactical narratives
    from SQLite relational records and indexes them into ChromaDB.
    """
    def __init__(self):
        self.chroma = chroma_manager

    def generate_match_narrative(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Synthesizes a rich natural language summary from SQLite match and delivery records.
        """
        # Fetch match info
        cols, rows = sqlite_manager.execute_query(f"SELECT * FROM matches WHERE id = '{match_id}';")
        if not rows:
            return None
        m = rows[0]

        team1 = m.get("team1")
        team2 = m.get("team2")
        venue = m.get("venue")
        date = m.get("date")
        season = m.get("season")
        match_type = m.get("match_type")
        winner = m.get("winner")
        win_by_runs = m.get("win_by_runs", 0)
        win_by_wickets = m.get("win_by_wickets", 0)
        potm = m.get("player_of_match")

        # Fetch Innings summaries
        deliv_cols, deliv_rows = sqlite_manager.execute_query(f"""
            SELECT 
                inning,
                batting_team,
                bowling_team,
                COUNT(*) as total_balls,
                MAX(over) as max_over,
                SUM(batsman_runs) as bat_runs,
                SUM(extra_runs) as extra_runs,
                SUM(total_runs) as total_runs,
                SUM(is_wicket) as wickets,
                SUM(is_six) as sixes,
                SUM(is_boundary) as fours
            FROM deliveries
            WHERE match_id = '{match_id}'
            GROUP BY inning
            ORDER BY inning;
        """)

        innings_narratives = []
        for inn in deliv_rows:
            inn_num = inn.get("inning")
            bat_team = inn.get("batting_team")
            total_r = inn.get("total_runs", 0)
            wkts = inn.get("wickets", 0)
            overs = inn.get("max_over", 0)
            sixes = inn.get("sixes", 0)

            # Top 2 batters in this inning
            _, top_batters = sqlite_manager.execute_query(f"""
                SELECT batter, SUM(batsman_runs) as runs, COUNT(*) as balls, SUM(is_six) as sixes
                FROM deliveries
                WHERE match_id = '{match_id}' AND inning = {inn_num}
                GROUP BY batter
                ORDER BY runs DESC
                LIMIT 2;
            """)
            bat_text_list = [f"{b['batter']} ({b['runs']} off {b['balls']}b, {b['sixes']}x6)" for b in top_batters]
            bat_str = ", ".join(bat_text_list) if bat_text_list else "collective contributions"

            # Top bowler in this inning
            _, top_bowlers = sqlite_manager.execute_query(f"""
                SELECT bowler, SUM(is_wicket) as wkts, SUM(total_runs) as runs
                FROM deliveries
                WHERE match_id = '{match_id}' AND inning = {inn_num}
                GROUP BY bowler
                ORDER BY wkts DESC, runs ASC
                LIMIT 1;
            """)
            bowl_str = f"led with the ball by {top_bowlers[0]['bowler']} ({top_bowlers[0]['wkts']}/{top_bowlers[0]['runs']})" if top_bowlers and top_bowlers[0]['wkts'] > 0 else "steady bowling"

            innings_narratives.append(
                f"Inning {inn_num}: {bat_team} scored {total_r}/{wkts} in {overs} overs, led by {bat_str}, with {bowl_str}."
            )

        inn_joined = " ".join(innings_narratives)

        # Margin text
        if win_by_runs > 0:
            result_str = f"{winner} won by {win_by_runs} runs"
        elif win_by_wickets > 0:
            result_str = f"{winner} won by {win_by_wickets} wickets"
        elif winner:
            result_str = f"{winner} won the match"
        else:
            result_str = "Match ended in a tie or no result"

        potm_str = f"Player of the Match was awarded to {potm}." if potm else ""

        full_text = (
            f"Match Summary: {team1} vs {team2} ({match_type}, Season {season}) at {venue} on {date}. "
            f"{inn_joined} {result_str}. {potm_str}"
        )

        metadata = {
            "type": "match_summary",
            "match_id": str(match_id),
            "match_type": str(match_type),
            "season": str(season),
            "teams": f"{team1} vs {team2}",
            "winner": str(winner) if winner else "None",
            "venue": str(venue),
            "potm": str(potm) if potm else "None"
        }

        return {
            "id": f"summary_{match_id}",
            "text": full_text,
            "metadata": metadata
        }

    def index_all_matches(self, max_matches: Optional[int] = None) -> int:
        """
        Generates and indexes narratives for all matches present in SQLite into ChromaDB.
        """
        cols, rows = sqlite_manager.execute_query("SELECT id FROM matches;")
        match_ids = [r["id"] for r in rows]
        if max_matches:
            match_ids = match_ids[:max_matches]

        docs_to_index = []
        for m_id in match_ids:
            doc = self.generate_match_narrative(m_id)
            if doc:
                docs_to_index.append(doc)

        if docs_to_index:
            col = self.chroma.get_collection()
            col.upsert(
                ids=[d["id"] for d in docs_to_index],
                documents=[d["text"] for d in docs_to_index],
                metadatas=[d["metadata"] for d in docs_to_index]
            )

        return len(docs_to_index)

    def index_canonical_rules(self) -> int:
        """
        Indexes foundational cricket laws, tiebreaker rules, and DLS documentation into ChromaDB.
        """
        col = self.chroma.get_collection()
        col.upsert(
            ids=[r["id"] for r in CANONICAL_CRICKET_RULES],
            documents=[r["text"] for r in CANONICAL_CRICKET_RULES],
            metadatas=[r["metadata"] for r in CANONICAL_CRICKET_RULES]
        )
        return len(CANONICAL_CRICKET_RULES)

    def search_narratives_with_filter(
        self, 
        query: str, 
        metadata_filter: Optional[Dict[str, Any]] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search over ChromaDB with optional metadata filtering.
        """
        col = self.chroma.get_collection()
        if col.count() == 0:
            return []

        query_params: Dict[str, Any] = {
            "query_texts": [query],
            "n_results": min(n_results, col.count())
        }
        if metadata_filter:
            query_params["where"] = metadata_filter

        results = col.query(**query_params)
        documents = []

        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)
            ids = results["ids"][0] if "ids" in results and results["ids"] else [""] * len(docs)

            for doc_id, text, meta, dist in zip(ids, docs, metadatas, distances):
                documents.append({
                    "id": doc_id,
                    "text": text,
                    "metadata": meta,
                    "distance": dist
                })

        return documents

narrative_indexer = NarrativeIndexer()

