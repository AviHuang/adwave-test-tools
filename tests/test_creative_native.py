"""
P1 Functional Test: Upload Native Creative
"""
import pytest
from .creative_helpers import extract_creative_counts, verify_creative_upload


@pytest.mark.asyncio
async def test_upload_native_creative(browser_agent, config):
    """Test uploading a Native format creative."""
    result = await browser_agent.create_creative(ad_format="Native")

    # Extract counts for debugging
    before_count, after_count = extract_creative_counts(result)

    # Verify upload success (after_count > before_count)
    upload_success = verify_creative_upload(result)

    if not upload_success:
        assert False, (
            f"Native creative upload failed. "
            f"Before: {before_count}, After: {after_count}. "
            f"Result: {result[:2000]}"
        )

    assert upload_success
