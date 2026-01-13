"""
Login functionality tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_login(browser_agent):
    """Test login with valid credentials."""
    result = await browser_agent.login()

    # Check for successful login indicators
    success = any(
        indicator in result.lower()
        for indicator in ["dashboard", "campaign", "welcome", "home", "success"]
    )

    assert success, f"Login failed: {result}"
