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
from core.reporter import (
    TestReport,
    TestResult,
    ReportGenerator,
    Checkpoint,
    get_checkpoints_for_test,
    extract_last_step_from_result,
    analyze_error,
    extract_key_error_log,
)


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


# Define test execution order: Campaign -> Creatives -> Audience
TEST_ORDER = [
    "test_create_push_campaign",
    "test_create_pop_campaign",
    "test_create_display_campaign",
    "test_create_native_campaign",
    "test_upload_push_creative",
    "test_upload_display_creative",
    "test_upload_native_creative",
    "test_create_audience",
]


def pytest_collection_modifyitems(items):
    """Sort tests according to predefined order."""
    def get_order(item):
        try:
            return TEST_ORDER.index(item.name)
        except ValueError:
            return len(TEST_ORDER)  # Unknown tests go last

    items.sort(key=get_order)


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
    # Use absolute path for reports directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(project_root, config.getoption("--report-dir"))
    config._report_generator = ReportGenerator(output_dir=reports_dir)
    config._current_screenshot = None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results, screenshots, and checkpoints."""
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

        # Initialize variables
        screenshot_base64 = None
        final_screenshot_base64 = None
        checkpoints = []
        error_message = ""
        error_analysis = None
        last_step = 0

        # Try to get data from browser_agent
        try:
            browser_agent = item.funcargs.get("browser_agent")
            if browser_agent:
                # Get last result to extract step info
                last_result = browser_agent.get_last_result()
                if last_result:
                    last_step = extract_last_step_from_result(last_result)

                if status == "passed":
                    # Get final screenshot on success
                    final_data = browser_agent.get_final_screenshot()
                    if final_data:
                        if isinstance(final_data, str):
                            final_screenshot_base64 = final_data
                        else:
                            final_screenshot_base64 = config._report_generator.screenshot_to_base64(
                                final_data
                            )
                else:
                    # Get error screenshot on failure
                    error_data = browser_agent.get_last_screenshot()
                    if error_data:
                        if isinstance(error_data, str):
                            screenshot_base64 = error_data
                        else:
                            screenshot_base64 = config._report_generator.screenshot_to_base64(
                                error_data
                            )
        except Exception:
            pass  # Report data collection not critical

        # Generate error analysis for failed tests
        if status in ("failed", "error") and report.longrepr:
            error_text = str(report.longrepr)
            error_message = extract_key_error_log(error_text)
            error_analysis = analyze_error(error_text, browser_agent.get_last_result() if browser_agent else "")

        # Generate checkpoints based on test name, status, and last step
        test_passed = (status == "passed")
        checkpoints = get_checkpoints_for_test(item.name, test_passed, last_step)

        # Create test result with all data
        test_result = TestResult(
            name=item.name,
            module=module,
            status=status,
            duration=report.duration,
            error_message=error_message,
            error_analysis=error_analysis,
            screenshot_base64=screenshot_base64,
            final_screenshot_base64=final_screenshot_base64,
            checkpoints=checkpoints,
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
