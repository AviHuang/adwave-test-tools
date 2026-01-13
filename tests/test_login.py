"""
Login functionality tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_login_page_loads(browser_agent, config):
    """Test that the login page loads correctly."""
    result = await browser_agent.verify_page_loads(
        url=config.login_url,
        expected_elements=[
            "Email input field",
            "Password input field",
            "Login button",
            "AdWave logo or branding",
        ],
    )

    assert result["success"], f"Login page failed to load properly: {result['raw_result']}"
    print(f"\nLogin page verification result:\n{result['raw_result']}")


@pytest.mark.asyncio
async def test_login_with_valid_credentials(browser_agent):
    """Test login with valid credentials."""
    result = await browser_agent.login()

    # Check for successful login indicators
    assert any(
        indicator in result.lower()
        for indicator in ["dashboard", "campaign", "welcome", "logged in", "home"]
    ), f"Login may have failed. Result: {result}"

    print(f"\nLogin result:\n{result}")


@pytest.mark.asyncio
async def test_login_redirects_to_dashboard(browser_agent, config):
    """Test that successful login redirects to dashboard."""
    task = f"""
    1. Navigate to {config.login_url}
    2. Enter {{email}} in the email input field
    3. Enter {{password}} in the password input field
    4. Click the login button
    5. Wait for redirect
    6. Report the current URL after login
    7. Check if we're on a dashboard or main application page
    """

    result = await browser_agent.run_task(task, sensitive_data=config.credentials)

    # Should not still be on login page
    assert "login" not in result.lower() or "logged in" in result.lower(), (
        f"May still be on login page: {result}"
    )

    print(f"\nPost-login navigation result:\n{result}")
