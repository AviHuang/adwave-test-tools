"""
Analytics module tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_analytics_page_loads(browser_agent, config):
    """Test that the Analytics page loads correctly after login."""
    result = await browser_agent.check_module(
        module_url=config.analytics_url,
        module_name="Analytics",
        expected_features=[
            "Analytics dashboard or overview",
            "Charts or graphs area",
            "Metrics or KPIs display",
            "Date range selector or filter",
        ],
    )

    assert result["success"], f"Analytics page test failed: {result['raw_result']}"
    print(f"\nAnalytics page verification:\n{result['raw_result']}")


@pytest.mark.asyncio
async def test_analytics_charts_display(browser_agent, config):
    """Test that analytics charts are displayed."""
    result = await browser_agent.login_and_navigate(config.analytics_url)

    # Should see analytics-related content
    assert any(
        term in result.lower()
        for term in ["analytics", "chart", "graph", "metric", "data", "report"]
    ), f"Analytics charts may not be displaying: {result}"

    print(f"\nAnalytics display result:\n{result}")


@pytest.mark.asyncio
async def test_analytics_navigation_accessible(browser_agent, config):
    """Test that Analytics module is accessible from navigation."""
    task = f"""
    1. Navigate to {config.login_url}
    2. Enter {{email}} in the email input field
    3. Enter {{password}} in the password input field
    4. Click the login button
    5. Wait for login to complete
    6. Look for and click on Analytics in the navigation menu
    7. Verify the Analytics page loads
    8. Report the analytics content visible:
       - Any charts or graphs
       - Key metrics displayed
       - Available filters or date ranges
    """

    result = await browser_agent.run_task(task, sensitive_data=config.credentials)

    assert "analytics" in result.lower() or "chart" in result.lower() or "metric" in result.lower(), (
        f"Analytics navigation test result: {result}"
    )
    print(f"\nAnalytics navigation result:\n{result}")
