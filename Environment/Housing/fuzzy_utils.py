# fuzzy_utils.py

"""
File to help with generalised searches using close_match
"""

from difflib import get_close_matches

def fuzzy_match(query, options, cutoff=0.6):
    if not query:
        return None
    matches = get_close_matches(query.lower(), [o.lower() for o in options], n=1, cutoff=cutoff)
    return matches[0] if matches else None
