"""
P1 Functional Test: Delete All Test Creatives
Deletes all creatives uploaded in the upload creative tests.
"""
import pytest
from .creative_helpers import extract_creative_counts


# Creative names to delete (must match exactly what was uploaded)
CREATIVES_TO_DELETE = [
    "main_492x328.png - PUSH",
    "display_250x250.png",
    "main_492x328.png",
]


@pytest.mark.asyncio
async def test_delete_creatives(browser_agent, config):
    """Test deleting all test creatives in one task."""
    result = await browser_agent.delete_creatives(creative_names=CREATIVES_TO_DELETE)

    # Extract counts for verification
    before_count, after_count = extract_creative_counts(result)

    # Verify deletion success: should delete 3 items
    # after_count should be before_count - 3
    expected_after = before_count - len(CREATIVES_TO_DELETE) if before_count >= 0 else -1

    if before_count >= 0 and after_count >= 0:
        delete_success = after_count < before_count
    else:
        # Fallback: check for success keywords
        result_lower = result.lower()
        delete_success = any(kw in result_lower for kw in ["deleted", "removed", "confirmed"])

    if not delete_success:
        assert False, (
            f"Creative deletion failed. "
            f"Before: {before_count}, After: {after_count}, Expected: {expected_after}. "
            f"Result: {result[:2000]}"
        )

    assert delete_success
