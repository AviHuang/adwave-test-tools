"""
P1 Functional Test: Creative Management (Upload & Delete)

Tests creative operations for all supported ad formats:
- Upload Push: Push notification creatives (requires 2 images: icon + banner)
- Upload Display: Banner display creatives
- Upload Native: Native advertising creatives
- Delete: Remove all test creatives
"""
import pytest
from .creative_helpers import extract_creative_counts, verify_creative_upload


# Ad formats for creative upload (Note: Pop format doesn't have creatives)
AD_FORMATS = ["Push", "Display", "Native"]

# Creative names to delete (must match exactly what was uploaded)
CREATIVES_TO_DELETE = [
    "main_492x328.png - PUSH",
    "display_250x250.png",
    "main_492x328.png",
]


@pytest.mark.parametrize("ad_format", AD_FORMATS, ids=lambda x: f"Upload_{x}")
@pytest.mark.asyncio
async def test_upload_creative(browser_agent, config, ad_format):
    """
    Test uploading a creative for the specified ad format.

    This parametrized test runs once for each ad format, uploading a creative
    and verifying the upload was successful.

    Args:
        browser_agent: Browser automation agent fixture
        config: Test configuration fixture
        ad_format: The ad format to test (Push, Display, Native)
    """
    # Upload creative using browser agent
    result = await browser_agent.create_creative(ad_format=ad_format)

    # Extract counts for debugging
    before_count, after_count = extract_creative_counts(result)

    # Verify upload success (after_count > before_count)
    upload_success = verify_creative_upload(result)

    # Provide detailed error message if verification fails
    if not upload_success:
        pytest.fail(
            f"{ad_format} creative upload failed.\n"
            f"Before count: {before_count}, After count: {after_count}\n"
            f"Result excerpt: {result[:1500]}..."
        )

    assert upload_success, f"{ad_format} creative upload verification failed"


@pytest.mark.asyncio
async def test_delete_creatives(browser_agent, config):
    """
    Test deleting all test creatives in one task.

    This test runs after all upload tests to clean up the uploaded creatives.
    It deletes creatives by their exact names.
    """
    result = await browser_agent.delete_creatives(creative_names=CREATIVES_TO_DELETE)

    # Extract counts for verification
    before_count, after_count = extract_creative_counts(result)

    # Verify deletion success: after_count should be less than before_count
    expected_after = before_count - len(CREATIVES_TO_DELETE) if before_count >= 0 else -1

    if before_count >= 0 and after_count >= 0:
        delete_success = after_count < before_count
    else:
        # Fallback: check for success keywords
        result_lower = result.lower()
        delete_success = any(kw in result_lower for kw in ["deleted", "removed", "confirmed"])

    if not delete_success:
        pytest.fail(
            f"Creative deletion failed.\n"
            f"Before count: {before_count}, After count: {after_count}, Expected: {expected_after}\n"
            f"Result excerpt: {result[:1500]}..."
        )

    assert delete_success, "Creative deletion verification failed"
