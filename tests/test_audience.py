"""
Audience module tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_audience_page_loads(browser_agent, config):
    """Test that the Audience page loads correctly after login."""
    result = await browser_agent.check_module(
        module_url=config.audience_url,
        module_name="Audience",
        expected_features=[
            "Audience list or table",
            "Create audience button or action",
            "Audience segment indicators",
            "Audience size or reach metrics",
        ],
    )

    assert result["success"], f"Audience page test failed: {result['raw_result']}"
    print(f"\nAudience page verification:\n{result['raw_result']}")


@pytest.mark.asyncio
async def test_audience_list_displays(browser_agent, config):
    """Test that the audience list displays properly."""
    result = await browser_agent.login_and_navigate(config.audience_url)

    # Should see audience-related content
    assert any(
        term in result.lower()
        for term in ["audience", "segment", "target", "list", "create"]
    ), f"Audience list may not be displaying: {result}"

    print(f"\nAudience list display result:\n{result}")


@pytest.mark.asyncio
async def test_audience_navigation_accessible(browser_agent, config):
    """Test that Audience module is accessible from navigation."""
    task = f"""
    1. Navigate to {config.login_url}
    2. Enter {{email}} in the email input field
    3. Enter {{password}} in the password input field
    4. Click the login button
    5. Wait for login to complete
    6. Look for and click on Audience in the navigation menu
    7. Verify the Audience page loads
    8. Report the audience content:
       - List of audiences/segments
       - Audience metrics (size, reach)
       - Available actions (create, edit)
    """

    result = await browser_agent.run_task(task, sensitive_data=config.credentials)

    assert any(
        term in result.lower()
        for term in ["audience", "segment", "target"]
    ), f"Audience navigation test result: {result}"

    print(f"\nAudience navigation result:\n{result}")
