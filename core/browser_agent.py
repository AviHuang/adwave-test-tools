"""
Browser Use wrapper for AdWave testing.
Provides a simplified interface for common test operations.
Supports multiple LLM providers: OpenAI-compatible, Claude, Gemini.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Literal

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from browser_use import Agent, Browser, BrowserProfile
from browser_use.tools.service import Tools

from .config import Config, LLMConfig
from .gmail_helper import GmailHelper
from .prompts import (
    build_create_campaign_task,
    build_create_audience_task,
    build_create_creative_task,
    build_delete_creatives_task,
    build_single_flow_registration_task,
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

    elif provider == "ollama":
        from browser_use import ChatOpenAI

        return ChatOpenAI(
            model=llm_config.model,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            add_schema_to_system_prompt=True,
            dont_force_structured_output=True,
            timeout=120.0,  # LLM call timeout (local models can be slow)
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
        self._last_prompt: Optional[str] = None  # Store prompt for checkpoint extraction
        self._final_screenshot: Optional[bytes] = None  # Screenshot on success

        # Track if using local model (requires simplified Agent settings)
        self._is_local_model = config.llm_config.provider == "ollama"

        self.llm = create_llm(config.llm_config)
        print(f"Using LLM: {config.llm_config.provider} / {config.llm_config.model}")
        if self._is_local_model:
            print("Local model mode: Using simplified Agent settings")

        # Set viewport to 1080p for all modes
        viewport = {"width": 1920, "height": 1080}

        self.browser_profile = BrowserProfile(
            headless=headless,
            viewport=viewport,
        )

        # Initialize Gmail helper for registration tests (if configured)
        # Priority: GMAIL_* > SMTP_* (reuse SMTP config if available)
        # Note: Supports both @gmail.com and Gmail Workspace (custom domain) accounts
        gmail_address = os.getenv("GMAIL_ADDRESS") or os.getenv("SMTP_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("SMTP_PASSWORD")
        if gmail_address and gmail_password:
            self.gmail_helper = GmailHelper(gmail_address, gmail_password)
            print(f"Gmail/Workspace helper initialized for: {gmail_address}")
        else:
            self.gmail_helper = None

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

    def get_last_prompt(self) -> Optional[str]:
        """Get the last task prompt (for checkpoint extraction)."""
        return self._last_prompt

    async def run_task(
        self,
        task: str,
        sensitive_data: Optional[Dict[str, str]] = None,
        max_steps: int = 8,
        available_file_paths: Optional[list[str]] = None,
        step_timeout: int = 120,
    ) -> str:
        """Run a browser automation task."""
        # Store prompt for checkpoint extraction in reports
        self._last_prompt = task

        # Base Agent configuration
        agent_kwargs = {
            "task": task,
            "llm": self.llm,
            "browser_profile": self.browser_profile,
            "sensitive_data": sensitive_data,
            "max_steps": max_steps,
            "available_file_paths": available_file_paths,
            "step_timeout": step_timeout,
        }

        # Apply simplified settings for local models
        if self._is_local_model:
            agent_kwargs.update({
                "use_vision": True,         # Enable vision mode
                "flash_mode": True,         # Simplified output: memory + action only
                "max_actions_per_step": 1,  # One action at a time
                "use_thinking": False,      # No thinking process
                "use_judge": False,         # Skip judge evaluation
                "max_failures": 5,          # More retries for local model
                "include_tool_call_examples": True,  # Show action examples to model
            })

        self._current_agent = Agent(**agent_kwargs)

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

    async def register_account(
        self,
        password: str = "TestPassword123!",
        sender_filter: str = "adwave",
        verification_timeout: int = 120,
    ) -> str:
        """
        Single-flow registration with custom action for verification code.

        Agent executes all steps in one flow and calls get_verification_code action when needed.
        """
        if not self.gmail_helper:
            raise ValueError(
                "Gmail not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD "
                "environment variables to use registration tests."
            )

        # Generate unique email alias
        registration_start_time = datetime.now()
        email_alias = self.gmail_helper.generate_alias()
        print(f"Generated email alias: {email_alias}")
        print(f"Registration started at: {registration_start_time.strftime('%H:%M:%S')}")

        # Create tools with custom action for getting verification code
        tools = Tools()

        # Store gmail helper reference for the action
        gmail_helper = self.gmail_helper

        @tools.action("Get the email verification code from inbox. Call this after submitting email on signup page.")
        def get_verification_code() -> str:
            """Retrieves the verification code from the email inbox."""
            print(f"[get_verification_code] Waiting for verification code...")
            code = gmail_helper.wait_for_verification_code(
                alias_email=email_alias,
                timeout=verification_timeout,
                sender_filter=sender_filter,
                start_time_override=registration_start_time,
            )
            if code:
                print(f"[get_verification_code] Got code: {code}")
                return f"Verification code is: {code}"
            else:
                return "ERROR: Could not retrieve verification code from email"

        # Build task prompt
        task = build_single_flow_registration_task(
            base_url=self.config.base_url,
            email_alias=email_alias,
        )

        # Sensitive data for password and email
        sensitive_data = {
            "email_alias": email_alias,
            "password": password,
        }

        browser = Browser(browser_profile=self.browser_profile)

        try:
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=browser,
                tools=tools,
                sensitive_data=sensitive_data,
                step_timeout=60,
                max_steps=60,
            )

            print("Starting single-flow registration...")
            result = await agent.run()
            result_str = str(result)

            # Check final URL for success
            registration_success = False
            try:
                current_url = await browser.get_current_page_url()
                print(f"Final URL: {current_url}")
                if current_url and "/campaign" in current_url:
                    registration_success = True
                    print("✓ Registration successful - landed on campaign page")
            except Exception as e:
                print(f"Could not get current URL: {e}")

            if registration_success:
                result_str += "\nREGISTRATION_SUCCESS: true\nLOGIN_SUCCESS: true"

            return (
                f"REGISTRATION_EMAIL: {email_alias}\n"
                f"{result_str}"
            )

        finally:
            try:
                await browser.close()
            except Exception:
                pass
