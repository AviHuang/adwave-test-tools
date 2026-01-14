"""
Configuration management for AdWave test tools.
Supports multiple environments (production, staging) and LLM providers.
"""
import os
from dataclasses import dataclass
from typing import Optional, Literal

# Supported LLM providers
LLMProvider = Literal["openai", "claude", "gemini"]


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider
    model: str
    api_key: str
    base_url: Optional[str] = None


class Config:
    """Test configuration."""

    # Environment URLs
    ENVIRONMENTS = {
        "production": "https://adwave.revosurge.com",
        "staging": None,  # To be provided later
    }

    # Default models for each provider
    DEFAULT_MODELS = {
        "openai": "gpt-4o",
        "claude": "claude-sonnet-4-20250514",
        "gemini": "gemini-2.0-flash",
    }

    def __init__(
        self,
        env: str = "production",
        llm_provider: Optional[LLMProvider] = None,
        llm_model: Optional[str] = None,
    ):
        """
        Initialize configuration.

        Args:
            env: Environment name ('production' or 'staging')
            llm_provider: LLM provider to use (auto-detected if not specified)
            llm_model: LLM model to use (uses default for provider if not specified)
        """
        self.env = env
        self.base_url = self.ENVIRONMENTS.get(env)
        if not self.base_url:
            raise ValueError(f"Unknown or unavailable environment: {env}")

        # Load credentials from environment variables
        self.email = os.getenv("ADWAVE_EMAIL")
        self.password = os.getenv("ADWAVE_PASSWORD")

        # Initialize LLM config
        self.llm_config = self._init_llm_config(llm_provider, llm_model)

    def _init_llm_config(
        self,
        provider: Optional[LLMProvider],
        model: Optional[str],
    ) -> LLMConfig:
        """Initialize LLM configuration based on available API keys."""

        # OpenAI-compatible API
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_base_url = os.getenv("OPENAI_BASE_URL")
        openai_model = os.getenv("OPENAI_MODEL")

        # API keys for each provider (GOOGLE_API_KEY is the new standard for Gemini)
        api_keys = {
            "openai": openai_api_key,
            "claude": os.getenv("ANTHROPIC_API_KEY"),
            "gemini": os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        }

        # Auto-detect provider if not specified
        if provider is None:
            for p in ["openai", "claude", "gemini"]:
                if api_keys.get(p):
                    provider = p
                    break

        if provider is None:
            raise ValueError(
                "No LLM API key found. Set one of: "
                "OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY"
            )

        api_key = api_keys.get(provider)
        if not api_key:
            raise ValueError(f"API key not found for provider: {provider}")

        # Determine model (priority: parameter > env var > default)
        if model is None:
            if provider == "openai" and openai_model:
                model = openai_model
            elif provider == "gemini" and os.getenv("GEMINI_MODEL"):
                model = os.getenv("GEMINI_MODEL")
            else:
                model = self.DEFAULT_MODELS.get(provider, "gpt-4o")

        # Set base_url for OpenAI-compatible providers
        base_url = openai_base_url if provider == "openai" else None

        return LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    @property
    def login_url(self) -> str:
        return f"{self.base_url}/login"

    @property
    def campaign_url(self) -> str:
        return f"{self.base_url}/campaign"

    @property
    def analytics_url(self) -> str:
        return f"{self.base_url}/analytics"

    @property
    def creative_url(self) -> str:
        return f"{self.base_url}/creative-library"

    @property
    def audience_url(self) -> str:
        return f"{self.base_url}/audience"

    @property
    def create_campaign_url(self) -> str:
        return f"{self.base_url}/campaign/create"

    @property
    def credentials(self) -> dict:
        """Return credentials as sensitive_data dict for Browser Use."""
        return {
            "email": self.email,
            "password": self.password,
        }

    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        if not self.email or not self.password:
            raise ValueError("ADWAVE_EMAIL and ADWAVE_PASSWORD must be set")
        return True
