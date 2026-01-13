"""
Campaign module tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_campaign_page_loads(browser_agent, config):
    """Test that the Campaign page loads correctly after login."""
    result = await browser_agent.check_module(
        module_url=config.campaign_url,
        module_name="Campaign",
        expected_features=[
            "Campaign list or table",
            "Create campaign button or action",
            "Campaign status indicators",
            "Navigation menu",
        ],
    )

    assert result["success"], f"Campaign page test failed: {result['raw_result']}"
    print(f"\nCampaign page verification:\n{result['raw_result']}")


@pytest.mark.asyncio
async def test_campaign_list_displays(browser_agent, config):
    """Test that the campaign list displays properly."""
    result = await browser_agent.login_and_navigate(config.campaign_url)

    # Should see campaign-related content
    assert any(
        term in result.lower()
        for term in ["campaign", "list", "table", "create", "status"]
    ), f"Campaign list may not be displaying: {result}"

    print(f"\nCampaign list display result:\n{result}")


@pytest.mark.asyncio
async def test_campaign_navigation_accessible(browser_agent, config):
    """Test that Campaign module is accessible from navigation."""
    task = f"""
    1. Navigate to {config.login_url}
    2. Enter {{email}} in the email input field
    3. Enter {{password}} in the password input field
    4. Click the login button
    5. Wait for login to complete
    6. Look for and click on Campaign in the navigation menu
    7. Verify the Campaign page loads
    8. Report what you see on the Campaign page
    """

    result = await browser_agent.run_task(task, sensitive_data=config.credentials)

    assert "campaign" in result.lower(), f"Campaign navigation test result: {result}"
    print(f"\nCampaign navigation result:\n{result}")
