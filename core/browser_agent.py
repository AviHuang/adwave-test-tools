"""
Browser Use wrapper for AdWave testing.
Provides a simplified interface for common test operations.
Supports multiple LLM providers: OpenAI-compatible, Claude, Gemini.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Literal

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from browser_use import Agent, BrowserProfile

from .config import Config, LLMConfig

# Asset paths for testing
ASSETS_DIR = Path(__file__).parent.parent / "assets"
ICON_192x192 = ASSETS_DIR / "icon_192x192.png"
DISPLAY_250x250 = ASSETS_DIR / "display_250x250.png"
MAIN_492x328 = ASSETS_DIR / "main_492x328.png"

# Ad format types
AdFormatType = Literal["Push", "Pop", "Display", "Native"]


def create_llm(llm_config: LLMConfig):
    """Create an LLM instance based on the provider configuration."""
    provider = llm_config.provider

    if provider == "openai":
        from browser_use import ChatOpenAI

        kwargs = {
            "model": llm_config.model,
            "api_key": llm_config.api_key,
        }

        if llm_config.base_url:
            kwargs["base_url"] = llm_config.base_url
            kwargs["add_schema_to_system_prompt"] = True
            kwargs["dont_force_structured_output"] = True

        return ChatOpenAI(**kwargs)

    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=llm_config.model,
            api_key=llm_config.api_key,
        )

    elif provider == "gemini":
        from browser_use import ChatGoogle

        return ChatGoogle(
            model=llm_config.model,
            api_key=llm_config.api_key,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


class AdWaveBrowserAgent:
    """Browser Use agent wrapper for AdWave testing."""

    def __init__(self, config: Config, headless: bool = True):
        self.config = config
        self.headless = headless
        self._current_agent: Optional[Agent] = None
        self._last_screenshot: Optional[bytes] = None

        self.llm = create_llm(config.llm_config)
        print(f"Using LLM: {config.llm_config.provider} / {config.llm_config.model}")

        self.browser_profile = BrowserProfile(headless=headless)

    async def capture_screenshot(self) -> Optional[bytes]:
        """Capture a screenshot of the current browser state."""
        try:
            if self._current_agent and self._current_agent.browser_session:
                page = await self._current_agent.browser_session.get_current_page()
                if page:
                    screenshot = await page.screenshot(full_page=False)
                    self._last_screenshot = screenshot
                    return screenshot
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
        return None

    def get_last_screenshot(self) -> Optional[bytes]:
        """Get the last captured screenshot."""
        return self._last_screenshot

    async def run_task(
        self,
        task: str,
        sensitive_data: Optional[Dict[str, str]] = None,
        max_steps: int = 8,
    ) -> str:
        """Run a browser automation task."""
        self._current_agent = Agent(
            task=task,
            llm=self.llm,
            browser_profile=self.browser_profile,
            sensitive_data=sensitive_data,
            max_steps=max_steps,
        )

        try:
            result = await self._current_agent.run()
            return str(result)
        except Exception:
            await self.capture_screenshot()
            raise

    async def login(self) -> str:
        """Perform login to AdWave."""
        self.config.validate()

        task = f"""
Go to {self.config.login_url}
Enter {{email}} in the email input field
Enter {{password}} in the password input field
Click the login button
Done when: URL changes to /campaign
"""

        return await self.run_task(task, sensitive_data=self.config.credentials)

    async def login_and_navigate(self, target_url: str) -> str:
        """Login and navigate to a specific page."""
        self.config.validate()

        # Extract page name from URL for navigation
        page_key = target_url.split("/")[-1]

        task = f"""
Go to {self.config.login_url}
Enter {{email}} in the email input field
Enter {{password}} in the password input field
Click the login button
After login, click the navigation menu item for "{page_key}"
Done when: URL contains /{page_key}
"""

        return await self.run_task(task, sensitive_data=self.config.credentials)

    async def create_campaign(
        self,
        campaign_name: Optional[str] = None,
        ad_format: AdFormatType = "Push",
        target_event: Optional[str] = None,
        location: str = "United States",
        target_bid: str = "1.0",
        budget: str = "10",
    ) -> str:
        """
        Create a new campaign with complete wizard flow.

        Args:
            campaign_name: Campaign name (auto-generated with timestamp if not provided)
            ad_format: One of "Push", "Pop", "Display", "Native"
            target_event: One of "Unique Visit", "Login", "Deposit", "Register" (random if not provided)
            location: Target location (e.g., "United States")
            target_bid: Bid amount (0.5-2.5 recommended)
            budget: Daily budget amount

        Returns:
            Result string from the browser agent
        """
        import random

        self.config.validate()

        # Generate campaign name with timestamp if not provided
        # Format: timestamp first for better visibility in truncated lists
        if not campaign_name:
            timestamp = datetime.now().strftime("%H%M%S_%Y%m%d")
            campaign_name = f"{timestamp}_test"

        # Default target event if not provided
        if not target_event:
            target_event = "Unique Visit"

        # Calculate end date (tomorrow)
        end_date = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")

        # Determine asset upload instructions based on ad format
        if ad_format == "Push":
            asset_instructions = """
Select assets for Push ad format from library:
1. Click "Add from Library" button
2. In the library popup, click on "Push Ad Set1" to select it
3. Click "Add" button to confirm
CHECKPOINT: Images should be selected and displayed
"""
        elif ad_format == "Pop":
            asset_instructions = """
Pop ad format does not require image uploads.
CHECKPOINT: Proceed directly, no upload areas should be required
"""
        elif ad_format == "Display":
            asset_instructions = """
Select assets for Display ad format from library:
1. Click "Add from Library" button
2. In the library popup, click on the first available image to select it
3. Click "Add" button to confirm
CHECKPOINT: Image should be selected and displayed
"""
        elif ad_format == "Native":
            asset_instructions = """
Select assets for Native ad format from library:
1. Click "Add from Library" button
2. In the library popup, click on the first available image to select it
3. Click "Add" button to confirm
CHECKPOINT: Image should be selected and displayed
"""
        else:
            asset_instructions = "Proceed with default asset handling."

        task = f"""
STEP 1: Login
- Go to {self.config.login_url}
- Wait for the login page to fully load
- Enter {{email}} in the email input field
- Enter {{password}} in the password input field
- Click the "Login" button to submit the form
- Wait for redirect to campaign page
CHECKPOINT: URL should change to contain "/campaign" after successful login

STEP 2: Switch Product
- Click the product dropdown/selector in the top-left corner of the page
- From the dropdown list, select "browser-use-test - https://revosrge.com"
- Wait for the page to refresh with the new product context
CHECKPOINT: The product selector should now display "browser-use-test"

STEP 3: Create Campaign
- Click the "+ Create Campaign" button
- Wait for the campaign creation form/wizard to load
CHECKPOINT: Campaign creation form should be visible with input fields

STEP 4: Fill Campaign Details
- Find the Campaign Name input field and type: "{campaign_name}"
- For Target Event: click the dropdown to open it, then click on "{target_event}" option in the list
- For Ad Format: click the dropdown to open it, then click on "{ad_format}" option in the list
- For Location Targeting: click the dropdown to open it, click on "Aruba" (the first option), then click on empty/blank area to close
- Find Target Bid input field and type: "{target_bid}"
- Find Budget input field and type: "{budget}"
- For Schedule section:
  - Leave Start Date as default (today)
  - Click the End Date field to open calendar picker
  - In the calendar, click on tomorrow's date (the day after today)
- Click "Next" button to proceed to asset upload step
CHECKPOINT: All fields should be filled and Next button should be clickable

STEP 5: Upload Assets
{asset_instructions}
- After assets are ready, click "Next" button to proceed to review step
CHECKPOINT: Should advance to review/summary page

STEP 6: Review and Publish
- Review the campaign summary showing all entered details
- Verify campaign name "{campaign_name}" is displayed correctly
- Click "Publish" or "Create Campaign" or "Submit" button to finalize
- Wait for success confirmation or redirect
CHECKPOINT: Should see success message or be redirected to campaign list

STEP 7: Verify Campaign Created
- Navigate to campaign list if not already there (click Campaign in sidebar if needed)
- Look at the campaign list table
- Read and list ALL campaign names visible in the first page of the table

IMPORTANT: You must report the campaign names you see in this exact format:
CAMPAIGN_LIST_START
[list each campaign name on a separate line]
CAMPAIGN_LIST_END

Example output format:
CAMPAIGN_LIST_START
campaign_name_1
campaign_name_2
campaign_name_3
CAMPAIGN_LIST_END
"""

        return await self.run_task(
            task,
            sensitive_data=self.config.credentials,
            max_steps=50,
        )

    async def create_post_ad(self, ad_name: str, headline: str, description: str) -> str:
        """Create a Post ad within a campaign."""
        self.config.validate()

        task = f"""
Go to {self.config.login_url}
Enter {{email}} in the email input field
Enter {{password}} in the password input field
Click the login button
Wait for the campaign page to load
Click on an existing campaign or create new one
Click "Add Ad" or "Create Ad" button
Select "Post" ad type
Fill in the ad name: "{ad_name}"
Fill in the headline: "{headline}"
Fill in the description: "{description}"
If there's a creative library, select an existing image
Otherwise, upload an image or skip if optional
Click "Save" or "Create" to submit the ad
Done when: Ad is created successfully or confirmation appears
"""

        return await self.run_task(
            task,
            sensitive_data=self.config.credentials,
            max_steps=20,
        )
