"""
Audience module tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_audience_page(browser_agent, config):
    """Test that Audience page is accessible after login."""
    result = await browser_agent.login_and_navigate(config.audience_url)

    success = any(
        term in result.lower()
        for term in ["audience", "segment", "target"]
    )
    assert success, f"Audience page not accessible: {result}"
