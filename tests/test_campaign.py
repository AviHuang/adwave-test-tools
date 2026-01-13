"""
Campaign module tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_campaign_page(browser_agent, config):
    """Test that Campaign page is accessible after login."""
    result = await browser_agent.login_and_navigate(config.campaign_url)

    success = "campaign" in result.lower()
    assert success, f"Campaign page not accessible: {result}"
