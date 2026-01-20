"""
Helper functions for creative tests.
"""
import re


def extract_creative_counts(result: str) -> tuple[int, int]:
    """Extract before and after counts from agent result.

    Returns:
        Tuple of (before_count, after_count), or (-1, -1) if not found
    """
    result_lower = result.lower()

    before_match = re.search(r'creative_count_before:\s*(\d+)', result_lower)
    after_match = re.search(r'creative_count_after:\s*(\d+)', result_lower)

    before_count = int(before_match.group(1)) if before_match else -1
    after_count = int(after_match.group(1)) if after_match else -1

    return before_count, after_count


def verify_creative_upload(result: str) -> bool:
    """Verify creative upload by checking count increase."""
    before_count, after_count = extract_creative_counts(result)

    # If counts found, verify after > before
    if before_count >= 0 and after_count >= 0:
        return after_count > before_count

    # Fallback: check for success keywords
    result_lower = result.lower()
    return "success" in result_lower or "added" in result_lower
