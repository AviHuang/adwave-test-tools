"""
Creative Library module tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_creative_page(browser_agent, config):
    """Test that Creative Library page is accessible after login."""
    result = await browser_agent.login_and_navigate(config.creative_url)

    success = any(
        term in result.lower()
        for term in ["creative", "library", "asset", "media"]
    )
    assert success, f"Creative Library page not accessible: {result}"
