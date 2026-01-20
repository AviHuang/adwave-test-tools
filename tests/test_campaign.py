"""
P1 Functional Test: Create Campaigns (All Ad Formats)

Tests campaign creation for all supported ad formats:
- Push: Push notification ads
- Pop: Pop-under/pop-up ads
- Display: Banner display ads
- Native: Native advertising format
"""
import pytest
from datetime import datetime
from .campaign_helpers import extract_campaign_list, verify_campaign_in_list


# Ad formats to test
AD_FORMATS = ["Push", "Pop", "Display", "Native"]


@pytest.mark.parametrize("ad_format", AD_FORMATS, ids=lambda x: f"Campaign_{x}")
@pytest.mark.asyncio
async def test_create_campaign(browser_agent, config, ad_format):
    """
    Test creating a campaign for the specified ad format.

    This parametrized test runs once for each ad format, creating a campaign
    and verifying it appears in the campaign list.

    Args:
        browser_agent: Browser automation agent fixture
        config: Test configuration fixture
        ad_format: The ad format to test (Push, Pop, Display, Native)
    """
    # Generate unique campaign name with timestamp and format
    timestamp = datetime.now().strftime("%H%M%S_%Y%m%d")
    campaign_name = f"{timestamp}_{ad_format}"

    # Create campaign using browser agent
    result = await browser_agent.create_campaign(
        campaign_name=campaign_name,
        ad_format=ad_format,
        target_bid="0.5",
        budget="1",
    )

    # Verify campaign appears in the list
    campaign_found = verify_campaign_in_list(result, campaign_name)

    # Provide detailed error message if verification fails
    if not campaign_found:
        campaigns = extract_campaign_list(result)
        pytest.fail(
            f"{ad_format} campaign '{campaign_name}' not found in campaign list.\n"
            f"Extracted campaigns: {campaigns}\n"
            f"Result excerpt: {result[:1500]}..."
        )

    assert campaign_found, f"{ad_format} campaign creation verification failed"
