"""
P1 Functional Test: Upload Push Creative
"""
import pytest
from .creative_helpers import extract_creative_counts, verify_creative_upload


@pytest.mark.asyncio
async def test_upload_push_creative(browser_agent, config):
    """Test uploading a Push format creative (requires 2 images)."""
    result = await browser_agent.create_creative(ad_format="Push")

    # Extract counts for debugging
    before_count, after_count = extract_creative_counts(result)

    # Verify upload success (after_count > before_count)
    upload_success = verify_creative_upload(result)

    if not upload_success:
        assert False, (
            f"Push creative upload failed. "
            f"Before: {before_count}, After: {after_count}. "
            f"Result: {result[:2000]}"
        )

    assert upload_success
