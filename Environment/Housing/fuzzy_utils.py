# fuzzy_utils.py

"""
Fuzzy matching utility using difflib's get_close_matches for
generalised searches against vocab lists.
"""

from difflib import get_close_matches


def fuzzy_match(query, options, cutoff=0.6):
    """
    Find the closest match to a query string from a list of options.

    :param query: The search string to match against.
    :param options: List of candidate strings to compare with.
    :param cutoff: Minimum similarity ratio (0.0 to 1.0) to count as a match.
    :return: The best matching string, or None if no match meets the cutoff.
    """
    if not query:
        return None
    matches = get_close_matches(query.lower(), [o.lower() for o in options], n=1, cutoff=cutoff)
    return matches[0] if matches else None
