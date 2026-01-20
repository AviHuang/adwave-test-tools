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
    """Verify creative upload by checking count increase.

    Strict verification: requires valid before/after counts.
    No fallback - agent must output counts in the required format.
    """
    before_count, after_count = extract_creative_counts(result)

    # Strict verification: both counts must be valid
    if before_count < 0 or after_count < 0:
        return False  # No fallback - counts are required

    # Verify after_count > before_count (creative was added)
    return after_count > before_count
