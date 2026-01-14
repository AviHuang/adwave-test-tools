"""
P1 Functional Test: Create Push Campaign
"""
import pytest
from datetime import datetime
from .campaign_helpers import extract_campaign_list, verify_campaign_in_list


@pytest.mark.asyncio
async def test_create_push_campaign(browser_agent, config):
    """Test creating a Push ad campaign through the complete wizard."""
    timestamp = datetime.now().strftime("%H%M%S_%Y%m%d")
    campaign_name = f"{timestamp}_Push"

    result = await browser_agent.create_campaign(
        campaign_name=campaign_name,
        ad_format="Push",
        target_bid="0.5",
        budget="1",
    )

    # Verify campaign appears in the list
    campaign_found = verify_campaign_in_list(result, campaign_name)

    # Debug: show extracted campaigns if failed
    if not campaign_found:
        campaigns = extract_campaign_list(result)
        assert False, f"Push campaign '{campaign_name}' not found. Extracted campaigns: {campaigns}. Full result: {result[:2000]}"

    assert campaign_found
