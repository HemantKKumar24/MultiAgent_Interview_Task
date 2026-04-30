import re

def injection_guard(chunk: str) -> tuple[bool, str]:
    """
    Scans for prompt injection patterns.
    Returns (is_flagged, cleaned_chunk).
    """
    # Patterns that typically indicate a prompt injection override
    patterns = [
        r"(?i)ignore\s+all\s+previous\s+instructions",
        r"(?i)system\s+override",
        r"(?i)you\s+are\s+now\s+a",
        r"(?i)disregard\s+previous"
    ]
    
    is_flagged = False
    cleaned_chunk = chunk
    
    for pattern in patterns:
        if re.search(pattern, chunk):
            is_flagged = True
            # Strip out the sentence containing the injection, or quarantine entirely.
            # For this task, we will quarantine (replace) the injected string.
            # A simple approach: remove sentences with the pattern.
            break
            
    if is_flagged:
        # Instead of parsing sentences, we just quarantine the entire chunk 
        # to be safe, or just return an empty string to avoid processing it.
        cleaned_chunk = "[SECURITY FLAG TRIGGERED: Content Quarantined]"
        
    return is_flagged, cleaned_chunk
