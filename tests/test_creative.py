"""
Creative Library module tests for AdWave platform.
"""
import pytest


@pytest.mark.asyncio
async def test_creative_library_page_loads(browser_agent, config):
    """Test that the Creative Library page loads correctly after login."""
    result = await browser_agent.check_module(
        module_url=config.creative_url,
        module_name="Creative Library",
        expected_features=[
            "Asset list or grid view",
            "Upload or add creative button",
            "Asset type filters",
            "Search functionality",
        ],
    )

    assert result["success"], f"Creative Library page test failed: {result['raw_result']}"
    print(f"\nCreative Library page verification:\n{result['raw_result']}")


@pytest.mark.asyncio
async def test_creative_assets_display(browser_agent, config):
    """Test that creative assets are displayed."""
    result = await browser_agent.login_and_navigate(config.creative_url)

    # Should see creative library related content
    assert any(
        term in result.lower()
        for term in ["creative", "library", "asset", "upload", "image", "video", "media"]
    ), f"Creative assets may not be displaying: {result}"

    print(f"\nCreative Library display result:\n{result}")


@pytest.mark.asyncio
async def test_creative_library_navigation_accessible(browser_agent, config):
    """Test that Creative Library module is accessible from navigation."""
    task = f"""
    1. Navigate to {config.login_url}
    2. Enter {{email}} in the email input field
    3. Enter {{password}} in the password input field
    4. Click the login button
    5. Wait for login to complete
    6. Look for and click on Creative Library (or similar) in the navigation menu
    7. Verify the Creative Library page loads
    8. Report the creative library content:
       - Types of assets shown (images, videos, etc.)
       - Grid or list layout
       - Available actions (upload, delete, edit)
    """

    result = await browser_agent.run_task(task, sensitive_data=config.credentials)

    assert any(
        term in result.lower()
        for term in ["creative", "library", "asset", "media"]
    ), f"Creative Library navigation test result: {result}"

    print(f"\nCreative Library navigation result:\n{result}")
