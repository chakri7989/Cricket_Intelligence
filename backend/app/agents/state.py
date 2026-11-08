from typing import TypedDict, Optional, List, Dict, Any

class CricketState(TypedDict, total=False):
    query: str
    intent: str  # HISTORICAL_SQL, HISTORICAL_RAG, LIVE_MATCH, HYBRID, PLAYER_COMPARISON
    extracted_entities: Dict[str, Any]
    sql_query: Optional[str]
    sql_results: Optional[List[Dict[str, Any]]]
    sql_error: Optional[str]
    sql_retry_count: int
    vector_docs: Optional[List[Dict[str, Any]]]
    live_data: Optional[Dict[str, Any]]
    comparison_data: Optional[Dict[str, Any]]
    chart_payload: Optional[Dict[str, Any]]
    reasoning_steps: List[str]
    final_answer: str
    citations: List[str]
    guardrail_status: Optional[str]
    error: Optional[str]
