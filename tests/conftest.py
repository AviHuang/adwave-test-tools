"""
Pytest configuration and fixtures for AdWave tests.
"""
import os
import sys
import time
from datetime import datetime

import pytest
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config
from core.browser_agent import AdWaveBrowserAgent, create_llm
from core.reporter import TestReport, TestResult, ReportGenerator


def _generate_error_analysis(test_name: str, error_text: str, has_screenshot: bool) -> str:
    """
    Generate AI analysis of test failure.

    Instead of showing raw error logs, this function provides a human-readable
    analysis of what went wrong.
    """
    # Extract key error information
    error_lines = error_text.strip().split("\n")

    # Find the actual error message (usually at the end)
    actual_error = ""
    for line in reversed(error_lines):
        line = line.strip()
        if line and not line.startswith(">") and not line.startswith("E "):
            if "Error" in line or "Exception" in line or "assert" in line.lower():
                actual_error = line
                break

    # Find assertion errors
    assertion_info = ""
    for line in error_lines:
        if line.strip().startswith("E "):
            assertion_info += line.strip()[2:] + " "

    # Generate concise analysis
    analysis_parts = []

    if "AssertionError" in error_text or "assert" in error_text.lower():
        if "success" in error_text.lower() and "false" in error_text.lower():
            analysis_parts.append("Test verification failed - expected elements or conditions were not met on the page.")
        elif assertion_info:
            analysis_parts.append(f"Assertion failed: {assertion_info.strip()}")
        else:
            analysis_parts.append("Test assertion failed during verification.")
    elif "TimeoutError" in error_text or "timeout" in error_text.lower():
        analysis_parts.append("Page or element loading timed out. The page may be slow or the element may not exist.")
    elif "ElementNotFound" in error_text or "not found" in error_text.lower():
        analysis_parts.append("Expected element was not found on the page. Page structure may have changed.")
    elif "ConnectionError" in error_text or "connection" in error_text.lower():
        analysis_parts.append("Network connection error. Check if the target URL is accessible.")
    elif "LoginError" in error_text or "login" in error_text.lower():
        analysis_parts.append("Login process failed. Check credentials or login page structure.")
    else:
        analysis_parts.append(f"Test encountered an error: {actual_error or 'Unknown error'}")

    if has_screenshot:
        analysis_parts.append("See the screenshot below for the page state at the time of failure.")

    return " ".join(analysis_parts)


def pytest_runtest_teardown(item, nextitem):
    """Add delay between tests for API rate limit cooldown."""
    if nextitem is not None:
        time.sleep(10)


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
    parser.addoption(
        "--report",
        action="store_true",
        default=False,
        help="Generate HTML test report",
    )
    parser.addoption(
        "--report-dir",
        action="store",
        default="reports",
        help="Directory for test reports",
    )
    parser.addoption(
        "--email",
        action="store",
        default=None,
        help="Email address to send report to",
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


# Report generation hooks
def pytest_configure(config):
    """Initialize report data at start of test session."""
    config._test_report = TestReport(
        start_time=datetime.now(),
        environment=config.getoption("--env"),
    )
    config._report_generator = ReportGenerator(
        output_dir=config.getoption("--report-dir")
    )
    config._current_screenshot = None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results and screenshots."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        # Get the config
        config = item.config

        # Determine test status
        if report.passed:
            status = "passed"
        elif report.failed:
            status = "failed"
        else:
            status = "error"

        # Get module name from test path
        module = item.module.__name__.split(".")[-1] if item.module else "unknown"

        # Try to get screenshot from browser_agent if test failed
        screenshot_base64 = None
        if status in ("failed", "error"):
            # Try to get screenshot from the browser_agent fixture
            try:
                browser_agent = item.funcargs.get("browser_agent")
                if browser_agent:
                    screenshot_bytes = browser_agent.get_last_screenshot()
                    if screenshot_bytes:
                        screenshot_base64 = config._report_generator.screenshot_to_base64(
                            screenshot_bytes
                        )
            except Exception as e:
                print(f"Failed to get screenshot: {e}")

        # Generate AI error analysis for failed tests
        error_analysis = None
        if status in ("failed", "error") and report.longrepr:
            # Use AI to analyze the error instead of raw logs
            error_analysis = _generate_error_analysis(
                test_name=item.name,
                error_text=str(report.longrepr),
                has_screenshot=screenshot_base64 is not None,
            )

        # Create test result
        test_result = TestResult(
            name=item.name,
            module=module,
            status=status,
            duration=report.duration,
            error_analysis=error_analysis,
            screenshot_base64=screenshot_base64,
        )

        config._test_report.results.append(test_result)


def pytest_sessionstart(session):
    """Called after Session object is created."""
    # Load config to get LLM info
    load_dotenv()
    try:
        cfg = Config(
            env=session.config.getoption("--env"),
            llm_provider=session.config.getoption("--llm"),
            llm_model=session.config.getoption("--model"),
        )
        session.config._test_report.llm_provider = cfg.llm_config.provider
        session.config._test_report.llm_model = cfg.llm_config.model
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
    """Generate report at end of test session."""
    if session.config.getoption("--report"):
        report = session.config._test_report
        report.end_time = datetime.now()

        generator = session.config._report_generator
        report_path = generator.save_report(report)

        print(f"\n{'='*60}")
        print(f"Test Report Generated: {report_path}")
        print(f"{'='*60}")
        print(f"Total: {report.total_tests} | Passed: {report.passed_tests} | Failed: {report.failed_tests}")
        print(f"Pass Rate: {report.pass_rate:.1f}%")
        print(f"{'='*60}\n")

        # Send email if requested
        to_email = session.config.getoption("--email")
        if to_email:
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "465"))
            smtp_user = os.getenv("SMTP_USER", "")
            smtp_password = os.getenv("SMTP_PASSWORD", "")

            if smtp_user and smtp_password:
                print(f"Sending report to {to_email}...")
                success = generator.send_email(
                    report=report,
                    report_path=report_path,
                    to_email=to_email,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    smtp_user=smtp_user,
                    smtp_password=smtp_password,
                )
                if success:
                    print(f"Report sent successfully to {to_email}")
                else:
                    print("Failed to send email report")
            else:
                print("Warning: Email requested but SMTP credentials not configured")
                print("Set SMTP_USER and SMTP_PASSWORD in .env file")
