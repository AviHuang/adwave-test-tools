"""
Browser Use wrapper for AdWave testing.
Provides a simplified interface for common test operations.
Supports multiple LLM providers: OpenAI-compatible, Claude, Gemini.
"""
import sys
from typing import Optional, Dict

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from browser_use import Agent, BrowserProfile

from .config import Config, LLMConfig


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
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=llm_config.model,
            google_api_key=llm_config.api_key,
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
