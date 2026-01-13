"""
Pytest configuration and fixtures for AdWave tests.
"""
import os
import sys

import pytest
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config
from core.browser_agent import AdWaveBrowserAgent


def pytest_addoption(parser):
    """Add command line options for pytest."""
    parser.addoption(
        "--env",
        action="store",
        default="production",
        help="Test environment: production or staging",
    )
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser in headed mode (visible)",
    )
    parser.addoption(
        "--llm",
        action="store",
        default=None,
        help="LLM provider: openai, claude, gemini (auto-detect if not specified)",
    )
    parser.addoption(
        "--model",
        action="store",
        default=None,
        help="LLM model name (uses provider default if not specified)",
    )


@pytest.fixture(scope="session")
def test_env(request) -> str:
    """Get the test environment from command line."""
    return request.config.getoption("--env")


@pytest.fixture(scope="session")
def headless(request) -> bool:
    """Get headless mode setting."""
    return not request.config.getoption("--headed")


@pytest.fixture(scope="session")
def llm_provider(request) -> str:
    """Get LLM provider from command line."""
    return request.config.getoption("--llm")


@pytest.fixture(scope="session")
def llm_model(request) -> str:
    """Get LLM model from command line."""
    return request.config.getoption("--model")


@pytest.fixture(scope="session")
def config(test_env, llm_provider, llm_model) -> Config:
    """Create test configuration."""
    # Load environment variables
    load_dotenv()

    return Config(
        env=test_env,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )


@pytest.fixture(scope="function")
def browser_agent(config, headless) -> AdWaveBrowserAgent:
    """Create a browser agent for testing."""
    return AdWaveBrowserAgent(config=config, headless=headless)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
