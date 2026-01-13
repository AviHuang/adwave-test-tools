"""
Analytics module tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_analytics_page(browser_agent, config):
    """Test that Analytics page is accessible after login."""
    result = await browser_agent.login_and_navigate(config.analytics_url)

    success = any(
        term in result.lower()
        for term in ["analytics", "chart", "metric", "data"]
    )
    assert success, f"Analytics page not accessible: {result}"
