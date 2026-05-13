import re
from typing import Dict, Any, Tuple

def validate_query(query: str) -> Tuple[bool, str]:
    """Validate user query"""
    if not query:
        return False, "Query cannot be empty"
    
    if len(query) > 1000:
        return False, "Query too long (max 1000 characters)"
    
    if len(query.strip()) < 3:
        return False, "Query too short (min 3 characters)"
    
    # Optional: Check for malicious content
    dangerous_patterns = [
        r'<script',
        r'DROP\s+TABLE',
        r'DELETE\s+FROM',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Query contains invalid content"
    
    return True, ""

def validate_request(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate incoming request"""
    if not data:
        return False, "Empty request body"
    
    query = data.get("query", "")
    return validate_query(query)