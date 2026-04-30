import datetime

def get_current_datetime() -> str:
    """Returns ISO-8601 datetime string."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def fetch_market_snapshot(sector: str) -> dict:
    """Mock API to fetch simulated market data."""
    return {
        "sector": sector,
        "competitor_prices": [
            {"competitor": "CompetitorX", "price": 125.50},
            {"competitor": "CompetitorY", "price": 89.20}
        ],
        "headlines": [
            f"{sector} sector sees rapid AI adoption.",
            "Regulatory concerns grow around data privacy."
        ],
        "macro_indicators": {
            "interest_rate": "5.25%",
            "inflation": "3.1%"
        }
    }

def calculate_risk_score(probability: float, impact: float) -> float:
    """Calculates risk score as probability * impact."""
    return probability * impact

def check_hallucination(claim: str, context_chunks: list[str]) -> dict:
    """
    Checks if a claim is supported by the context chunks.
    Uses simple keyword overlap for demonstration.
    """
    if not context_chunks:
        return {"supported": False, "best_match_chunk": None, "similarity_score": 0.0}
    
    claim_words = set(claim.lower().split())
    best_score = 0.0
    best_chunk = None
    
    for chunk in context_chunks:
        chunk_words = set(chunk.lower().split())
        if not chunk_words: continue
        overlap = len(claim_words.intersection(chunk_words))
        score = overlap / len(claim_words) if claim_words else 0
        if score > best_score:
            best_score = score
            best_chunk = chunk
            
    # threshold for considering it supported
    supported = best_score > 0.3 
    
    return {
        "supported": supported,
        "best_match_chunk": best_chunk,
        "similarity_score": best_score
    }
