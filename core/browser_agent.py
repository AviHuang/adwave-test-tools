"""
Browser Use wrapper for AdWave testing.
Provides a simplified interface for common test operations.
Supports multiple LLM providers: OpenAI, DeepSeek, Claude, Gemini.
"""
import asyncio
import sys
from typing import Optional, Dict, Any

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from browser_use import Agent, BrowserProfile

from .config import Config, LLMConfig


def create_llm(llm_config: LLMConfig):
    """
    Create an LLM instance based on the provider configuration.

    Args:
        llm_config: LLM configuration

    Returns:
        LLM instance for browser_use
    """
    provider = llm_config.provider

    if provider == "openai":
        # OpenAI-compatible providers (OpenAI, DeepSeek, etc.)
        from browser_use import ChatOpenAI

        kwargs = {
            "model": llm_config.model,
            "api_key": llm_config.api_key,
        }

        if llm_config.base_url:
            kwargs["base_url"] = llm_config.base_url
            # Non-OpenAI providers often don't support structured output
            kwargs["add_schema_to_system_prompt"] = True
            kwargs["dont_force_structured_output"] = True

        return ChatOpenAI(**kwargs)

    elif provider == "claude":
        # Anthropic Claude
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=llm_config.model,
            api_key=llm_config.api_key,
        )

    elif provider == "gemini":
        # Google Gemini
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
        """
        Initialize the browser agent.

        Args:
            config: Test configuration
            headless: Run browser in headless mode
        """
        self.config = config
        self.headless = headless
        self._logged_in = False

        # Initialize LLM based on config
        self.llm = create_llm(config.llm_config)
        print(f"Using LLM: {config.llm_config.provider} / {config.llm_config.model}")

        # Browser profile
        self.browser_profile = BrowserProfile(
            headless=headless,
        )

    async def run_task(
        self,
        task: str,
        sensitive_data: Optional[Dict[str, str]] = None,
        max_steps: int = 25,
    ) -> str:
        """
        Run a browser automation task.

        Args:
            task: Task description for the agent
            sensitive_data: Optional sensitive data (credentials, etc.)
            max_steps: Maximum number of agent steps

        Returns:
            Result string from the agent
        """
        agent = Agent(
            task=task,
            llm=self.llm,
            browser_profile=self.browser_profile,
            sensitive_data=sensitive_data,
            max_steps=max_steps,
        )

        result = await agent.run()
        return str(result)

    async def login(self) -> str:
        """
        Perform login to AdWave.

        Returns:
            Result string describing login outcome
        """
        self.config.validate()

        task = f"""
        1. Navigate to {self.config.login_url}
        2. Enter {{email}} in the email input field
        3. Enter {{password}} in the password input field
        4. Click the login button
        5. Wait for the page to redirect after login
        6. Return the current page URL and any visible user info or dashboard content
        """

        result = await self.run_task(task, sensitive_data=self.config.credentials)
        self._logged_in = True
        return result

    async def verify_page_loads(self, url: str, expected_elements: list[str]) -> Dict[str, Any]:
        """
        Verify that a page loads correctly and contains expected elements.

        Args:
            url: URL to navigate to
            expected_elements: List of element descriptions to look for

        Returns:
            Dict with 'success', 'found_elements', 'missing_elements', 'page_content'
        """
        elements_str = "\n".join([f"   - {elem}" for elem in expected_elements])

        task = f"""
        1. Navigate to {url}
        2. Wait for the page to fully load
        3. Check if the following elements are visible on the page:
{elements_str}
        4. For each element, report:
           - Whether it exists (YES/NO)
           - Brief description of what you see
        5. Report the page title and main content areas
        6. Format your response as:
           PAGE_URL: [url]
           PAGE_TITLE: [title]
           ELEMENTS_CHECK:
           [element name]: [YES/NO] - [description]
           ...
           OVERALL_STATUS: [PASS/FAIL]
        """

        result = await self.run_task(task, sensitive_data=self.config.credentials)

        # Parse result
        success = "OVERALL_STATUS: PASS" in result or "PASS" in result.upper()

        return {
            "success": success,
            "url": url,
            "raw_result": result,
        }

    async def login_and_navigate(self, target_url: str) -> str:
        """
        Login and navigate to a specific page.

        Args:
            target_url: URL to navigate to after login

        Returns:
            Page content description
        """
        self.config.validate()

        task = f"""
        1. Navigate to {self.config.login_url}
        2. Enter {{email}} in the email input field
        3. Enter {{password}} in the password input field
        4. Click the login button
        5. Wait for login to complete
        6. Navigate to {target_url}
        7. Wait for the page to fully load
        8. Describe the page content including:
           - Page title
           - Main navigation elements
           - Key content areas (tables, charts, lists, etc.)
           - Any important buttons or actions visible
        """

        return await self.run_task(task, sensitive_data=self.config.credentials)

    async def check_module(
        self,
        module_url: str,
        module_name: str,
        expected_features: list[str],
    ) -> Dict[str, Any]:
        """
        Check a module by logging in and verifying expected features.

        Args:
            module_url: Full URL of the module
            module_name: Name of the module for reporting
            expected_features: List of features/elements to verify

        Returns:
            Test result dict
        """
        self.config.validate()

        features_str = "\n".join([f"   - {feat}" for feat in expected_features])

        task = f"""
        1. Navigate to {self.config.login_url}
        2. Enter {{email}} in the email input field
        3. Enter {{password}} in the password input field
        4. Click the login button
        5. Wait for login to complete
        6. Navigate to {module_url}
        7. Wait for the page to fully load
        8. Verify the following features are present:
{features_str}
        9. For each feature, indicate if it is:
           - FOUND: The feature is visible and appears functional
           - NOT_FOUND: The feature could not be located
           - PARTIAL: The feature exists but may have issues
        10. Provide a summary with:
            MODULE: {module_name}
            URL: {module_url}
            STATUS: PASS/FAIL
            FEATURES:
            [feature]: [FOUND/NOT_FOUND/PARTIAL] - [notes]
        """

        result = await self.run_task(task, sensitive_data=self.config.credentials)

        success = "STATUS: PASS" in result or (
            "NOT_FOUND" not in result and "FAIL" not in result.upper()
        )

        return {
            "module": module_name,
            "url": module_url,
            "success": success,
            "raw_result": result,
        }
