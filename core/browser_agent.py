"""
Browser Use wrapper for AdWave testing.
Provides a simplified interface for common test operations.
Supports multiple LLM providers: OpenAI-compatible, Claude, Gemini.
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Literal

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from browser_use import Agent, BrowserProfile

from .config import Config, LLMConfig
from .prompts import (
    build_create_campaign_task,
    build_create_audience_task,
    build_create_creative_task,
    build_delete_creatives_task,
)

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
        self._last_result: Optional[str] = None
        self._final_screenshot: Optional[bytes] = None  # Screenshot on success

        self.llm = create_llm(config.llm_config)
        print(f"Using LLM: {config.llm_config.provider} / {config.llm_config.model}")

        # Set viewport to 1080p for all modes
        viewport = {"width": 1920, "height": 1080}

        self.browser_profile = BrowserProfile(
            headless=headless,
            viewport=viewport,
        )

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
        """Get the last captured screenshot (error screenshot)."""
        return self._last_screenshot

    def get_final_screenshot(self) -> Optional[bytes]:
        """Get the final screenshot (success screenshot)."""
        return self._final_screenshot

    def get_last_result(self) -> Optional[str]:
        """Get the last task result."""
        return self._last_result

    async def run_task(
        self,
        task: str,
        sensitive_data: Optional[Dict[str, str]] = None,
        max_steps: int = 8,
        available_file_paths: Optional[list[str]] = None,
        step_timeout: int = 120,
    ) -> str:
        """Run a browser automation task."""
        self._current_agent = Agent(
            task=task,
            llm=self.llm,
            browser_profile=self.browser_profile,
            sensitive_data=sensitive_data,
            max_steps=max_steps,
            available_file_paths=available_file_paths,
            step_timeout=step_timeout,
        )

        try:
            result = await self._current_agent.run()
            result_str = str(result)
            self._last_result = result_str
            # Get final screenshot from agent history (browser may already be closed)
            try:
                screenshots = result.screenshots()
                if screenshots and len(screenshots) > 0:
                    self._final_screenshot = screenshots[-1]
            except Exception:
                pass  # Screenshot not critical
            return result_str
        except Exception as e:
            error_type = type(e).__name__
            print(f"Task failed with {error_type}: {str(e)[:200]}")

            # Try to get screenshot from agent history first (more reliable)
            try:
                if self._current_agent and hasattr(self._current_agent, 'history'):
                    history = self._current_agent.history
                    if history:
                        screenshots = history.screenshots()
                        if screenshots and len(screenshots) > 0:
                            self._last_screenshot = screenshots[-1]
                            print("Screenshot captured from agent history")
            except Exception as screenshot_err:
                print(f"Failed to get screenshot from history: {screenshot_err}")

            # Fallback: try to capture from browser directly
            if not self._last_screenshot:
                try:
                    await self.capture_screenshot()
                    if self._last_screenshot:
                        print("Screenshot captured from browser")
                except Exception as capture_err:
                    print(f"Failed to capture screenshot: {capture_err}")

            # Store error message for debugging
            self._last_result = f"Error ({error_type}): {str(e)}"

            # Clean up browser session to ensure next test starts fresh
            try:
                if self._current_agent and self._current_agent.browser_session:
                    await self._current_agent.browser_session.close()
                    print("Browser session closed")
            except Exception:
                pass

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
        target_bid: str = "0.5",
        budget: str = "1",
    ) -> str:
        """
        Create a new campaign with complete wizard flow.

        Args:
            campaign_name: Campaign name (auto-generated with timestamp if not provided)
            ad_format: One of "Push", "Pop", "Display", "Native"
            target_event: One of "Unique Visit", "Login", "Deposit", "Register"
            target_bid: Bid amount (default 0.5)
            budget: Daily budget amount (default 1)

        Returns:
            Result string from the browser agent
        """
        self.config.validate()

        # Generate campaign name with timestamp if not provided
        if not campaign_name:
            timestamp = datetime.now().strftime("%H%M%S_%Y%m%d")
            campaign_name = f"{timestamp}_test"

        # Default target event if not provided
        if not target_event:
            target_event = "Unique Visit"

        task = build_create_campaign_task(
            login_url=self.config.login_url,
            campaign_name=campaign_name,
            ad_format=ad_format,
            target_event=target_event,
            target_bid=target_bid,
            budget=budget,
        )

        return await self.run_task(
            task,
            sensitive_data=self.config.credentials,
            max_steps=50,
        )

    async def create_audience(
        self,
        audience_name: Optional[str] = None,
    ) -> str:
        """
        Create a new audience segment with minimal configuration.

        Args:
            audience_name: Segment name (auto-generated with timestamp if not provided)

        Returns:
            Result string from the browser agent
        """
        self.config.validate()

        # Generate audience name with timestamp if not provided
        if not audience_name:
            timestamp = datetime.now().strftime("%H%M%S_%Y%m%d")
            audience_name = f"{timestamp}_audience"

        task = build_create_audience_task(
            login_url=self.config.login_url,
            audience_name=audience_name,
        )

        return await self.run_task(
            task,
            sensitive_data=self.config.credentials,
            max_steps=30,
        )

    async def create_creative(
        self,
        ad_format: AdFormatType = "Display",
    ) -> str:
        """
        Upload a new creative to the library.

        Args:
            ad_format: One of "Push", "Display", "Native"

        Returns:
            Result string from the browser agent
        """
        self.config.validate()

        # Prepare file paths based on ad format
        if ad_format == "Push":
            file_paths = [str(ICON_192x192), str(MAIN_492x328)]
            task = build_create_creative_task(
                login_url=self.config.login_url,
                ad_format=ad_format,
                icon_path=str(ICON_192x192),
                main_path=str(MAIN_492x328),
            )
        elif ad_format == "Display":
            file_paths = [str(DISPLAY_250x250)]
            task = build_create_creative_task(
                login_url=self.config.login_url,
                ad_format=ad_format,
                image_path=str(DISPLAY_250x250),
            )
        elif ad_format == "Native":
            file_paths = [str(MAIN_492x328)]
            task = build_create_creative_task(
                login_url=self.config.login_url,
                ad_format=ad_format,
                image_path=str(MAIN_492x328),
            )
        else:
            raise ValueError(f"Unknown ad format: {ad_format}")

        return await self.run_task(
            task,
            sensitive_data=self.config.credentials,
            max_steps=30,
            available_file_paths=file_paths,
        )

    async def delete_creatives(
        self,
        creative_names: list[str],
    ) -> str:
        """
        Delete multiple creatives from the library in one task.

        Args:
            creative_names: List of creative names to delete

        Returns:
            Result string from the browser agent
        """
        self.config.validate()

        task = build_delete_creatives_task(
            login_url=self.config.login_url,
            creative_names=creative_names,
        )

        return await self.run_task(
            task,
            sensitive_data=self.config.credentials,
            max_steps=30,
        )
