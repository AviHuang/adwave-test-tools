"""
Test report generator for AdWave tests.
Generates HTML reports with screenshots and AI error analysis.
Supports email and Slack delivery.
"""
import os
import re
import json
import base64
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


# Reports directory
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


@dataclass
class Checkpoint:
    """Represents a test checkpoint/step."""
    step: int
    name: str
    status: str  # "passed", "failed", "in_progress"
    details: str = ""
    screenshot_base64: Optional[str] = None


@dataclass
class TestResult:
    """Individual test result."""
    name: str
    module: str
    status: str  # "passed", "failed", "error"
    duration: float
    error_message: str = ""
    error_analysis: Optional[str] = None  # AI-generated error analysis
    screenshot_base64: Optional[str] = None  # Error screenshot
    final_screenshot_base64: Optional[str] = None  # Success screenshot
    checkpoints: List[Checkpoint] = field(default_factory=list)


@dataclass
class TestReport:
    """Test report data."""
    title: str = "AdWave Test Report"
    environment: str = "production"
    llm_provider: str = ""
    llm_model: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    results: List[TestResult] = field(default_factory=list)

    @property
    def total_tests(self) -> int:
        return len(self.results)

    @property
    def passed_tests(self) -> int:
        return len([r for r in self.results if r.status == "passed"])

    @property
    def failed_tests(self) -> int:
        return len([r for r in self.results if r.status in ("failed", "error")])

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    @property
    def total_duration(self) -> float:
        return sum(r.duration for r in self.results)


class ReportGenerator:
    """Generates HTML test reports with email support."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def screenshot_to_base64(self, screenshot_bytes: bytes) -> str:
        """Convert screenshot bytes to base64 string."""
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    def generate_html(self, report: TestReport) -> str:
        """Generate HTML report content in markdown-like style."""

        # Group results by module
        modules = {}
        for result in report.results:
            if result.module not in modules:
                modules[result.module] = []
            modules[result.module].append(result)

        # Generate test results by module
        results_html = ""
        for module_name, results in modules.items():
            module_passed = all(r.status == "passed" for r in results)
            module_icon = "🟢" if module_passed else "🔴"

            results_html += f'''
            <div class="module">
                <h3>{module_icon} {module_name}</h3>
                <ul>
            '''

            for result in results:
                status_icon = "✅" if result.status == "passed" else "❌"
                duration_str = f"({result.duration:.1f}s)"

                # Checkpoints section
                checkpoints_html = ""
                if result.checkpoints:
                    checkpoints_html = '<div class="checkpoints"><strong>Checkpoints:</strong><ul>'
                    for cp in result.checkpoints:
                        if cp.status == "passed":
                            cp_icon = "✅"
                        elif cp.status == "failed":
                            cp_icon = "❌"
                        else:  # skipped
                            cp_icon = "⏭️"
                        cp_screenshot = ""
                        if cp.screenshot_base64:
                            cp_screenshot = f'''
                            <details>
                                <summary>Screenshot</summary>
                                <img src="data:image/png;base64,{cp.screenshot_base64}" alt="Step {cp.step}">
                            </details>
                            '''
                        checkpoints_html += f'''
                        <li>{cp_icon} Step {cp.step}: {cp.name}
                            {f'<span class="cp-details">- {cp.details}</span>' if cp.details else ''}
                            {cp_screenshot}
                        </li>
                        '''
                    checkpoints_html += '</ul></div>'

                # Error section for failed tests
                error_html = ""
                if result.status != "passed":
                    if result.error_message:
                        error_html += f'<div class="error-msg"><strong>Error:</strong><pre>{result.error_message[:500]}</pre></div>'
                    if result.error_analysis:
                        error_html += f'<div class="error-analysis"><strong>AI Analysis:</strong><p>{result.error_analysis}</p></div>'
                    if result.screenshot_base64:
                        error_html += f'''
                        <div class="error-screenshot">
                            <strong>Error Screenshot:</strong>
                            <img src="data:image/png;base64,{result.screenshot_base64}" alt="Error Screenshot">
                        </div>
                        '''

                # Success screenshot
                success_screenshot_html = ""
                if result.status == "passed" and result.final_screenshot_base64:
                    success_screenshot_html = f'''
                    <details open>
                        <summary>✅ Final Verification Screenshot</summary>
                        <img src="data:image/png;base64,{result.final_screenshot_base64}" alt="Final Screenshot">
                    </details>
                    '''

                results_html += f'''
                    <li class="test-result {'passed' if result.status == 'passed' else 'failed'}">
                        <div class="test-header">
                            {status_icon} <code>{result.name}</code> <span class="duration">{duration_str}</span>
                        </div>
                        {checkpoints_html}
                        {error_html}
                        {success_screenshot_html}
                    </li>
                '''

            results_html += '''
                </ul>
            </div>
            '''

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #24292e;
            line-height: 1.6;
            background: #fff;
        }}
        h1 {{
            border-bottom: 1px solid #eaecef;
            padding-bottom: 10px;
            margin-bottom: 16px;
        }}
        h2 {{
            border-bottom: 1px solid #eaecef;
            padding-bottom: 8px;
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        h3 {{
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background: #f6f8fa;
            font-weight: 600;
        }}
        code {{
            background: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
        .duration {{
            color: #6a737d;
            font-size: 0.85em;
        }}
        .error {{
            color: #cb2431;
            margin: 4px 0 4px 24px;
            font-size: 0.9em;
        }}
        .module {{
            margin-bottom: 20px;
        }}
        details {{
            margin: 8px 0 8px 24px;
        }}
        summary {{
            cursor: pointer;
            color: #0366d6;
            font-size: 0.9em;
        }}
        img {{
            max-width: 100%;
            margin-top: 8px;
            border: 1px solid #dfe2e5;
        }}
        hr {{
            border: 0;
            border-top: 1px solid #eaecef;
            margin: 24px 0;
        }}
        .footer {{
            color: #6a737d;
            font-size: 0.85em;
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #eaecef;
        }}
        .test-result {{
            margin: 16px 0;
            padding: 12px;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            list-style: none;
        }}
        .test-result.passed {{
            border-left: 4px solid #28a745;
        }}
        .test-result.failed {{
            border-left: 4px solid #cb2431;
        }}
        .test-header {{
            font-size: 1.1em;
            margin-bottom: 8px;
        }}
        .checkpoints {{
            margin: 12px 0;
            padding: 8px;
            background: #f6f8fa;
            border-radius: 4px;
        }}
        .checkpoints ul {{
            margin: 8px 0 0 0;
        }}
        .checkpoints li {{
            margin: 4px 0;
            font-size: 0.9em;
        }}
        .cp-details {{
            color: #6a737d;
            font-size: 0.85em;
        }}
        .error-msg {{
            margin: 12px 0;
            padding: 8px;
            background: #ffeef0;
            border-radius: 4px;
        }}
        .error-msg pre {{
            margin: 8px 0 0 0;
            white-space: pre-wrap;
            word-break: break-word;
            font-size: 0.85em;
            color: #cb2431;
        }}
        .error-analysis {{
            margin: 12px 0;
            padding: 8px;
            background: #fff8c5;
            border-radius: 4px;
        }}
        .error-analysis p {{
            margin: 8px 0 0 0;
            font-size: 0.9em;
        }}
        .error-screenshot {{
            margin: 12px 0;
        }}
        .error-screenshot img {{
            border: 2px solid #cb2431;
        }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>

    <h2>Summary</h2>
    <table>
        <tr>
            <th>Environment</th>
            <th>LLM</th>
            <th>Time</th>
            <th>Duration</th>
        </tr>
        <tr>
            <td>{report.environment}</td>
            <td>{report.llm_provider} / {report.llm_model}</td>
            <td>{report.start_time.strftime("%Y-%m-%d %H:%M:%S")}</td>
            <td>{report.total_duration:.1f}s</td>
        </tr>
    </table>

    <table>
        <tr>
            <th>Total</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Pass Rate</th>
        </tr>
        <tr>
            <td>{report.total_tests}</td>
            <td>🟢 {report.passed_tests}</td>
            <td>{"🔴 " + str(report.failed_tests) if report.failed_tests > 0 else "0"}</td>
            <td>{report.pass_rate:.1f}%</td>
        </tr>
    </table>

    <h2>Test Results</h2>
    {results_html}

    <hr>
    <div class="footer">
        Generated by AdWave Test Tools | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>
</body>
</html>'''
        return html

    def save_report(self, report: TestReport, filename: Optional[str] = None) -> str:
        """Save report to HTML file and return the path."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.html"

        filepath = self.output_dir / filename
        html = self.generate_html(report)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        return str(filepath)

    def send_email(
        self,
        report: TestReport,
        report_path: str,
        to_email: str,
        smtp_server: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: Optional[str] = None,
    ) -> bool:
        """
        Send test report via email.

        Args:
            report: Test report data
            report_path: Path to the HTML report file
            to_email: Recipient email address
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Sender email (defaults to smtp_user)

        Returns:
            True if email sent successfully
        """
        if from_email is None:
            from_email = smtp_user

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"AdWave Test Report - {report.pass_rate:.1f}% Pass Rate ({report.passed_tests}/{report.total_tests})"
        msg["From"] = from_email
        msg["To"] = to_email

        # Plain text summary
        plain_text = f"""
AdWave Test Report
==================

Environment: {report.environment}
LLM: {report.llm_provider} / {report.llm_model}
Time: {report.start_time.strftime("%Y-%m-%d %H:%M:%S")}

Results:
- Total Tests: {report.total_tests}
- Passed: {report.passed_tests}
- Failed: {report.failed_tests}
- Pass Rate: {report.pass_rate:.1f}%

See attached HTML report for details.
"""

        # Attach plain text
        msg.attach(MIMEText(plain_text, "plain"))

        # Attach HTML report
        html_content = self.generate_html(report)
        msg.attach(MIMEText(html_content, "html"))

        # Also attach as file
        with open(report_path, "rb") as f:
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f"attachment; filename={Path(report_path).name}",
            )
            msg.attach(attachment)

        # Send email
        try:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, to_email, msg.as_string())
            print(f"Report sent to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    # =========================================================================
    # Slack Integration
    # =========================================================================

    def generate_slack_blocks(self, report: TestReport) -> List[Dict[str, Any]]:
        """
        Generate Slack Block Kit message for the test report.

        Returns a list of blocks that create a rich, formatted message.
        """
        # Status emoji and color
        if report.pass_rate == 100:
            status_emoji = ":white_check_mark:"
            status_text = "All Tests Passed"
        elif report.pass_rate >= 80:
            status_emoji = ":large_yellow_circle:"
            status_text = "Most Tests Passed"
        else:
            status_emoji = ":x:"
            status_text = "Tests Failed"

        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} {report.title}",
                    "emoji": True
                }
            },
            # Summary section
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Environment:*\n{report.environment}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*LLM:*\n{report.llm_provider} / {report.llm_model}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{report.start_time.strftime('%Y-%m-%d %H:%M')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Duration:*\n{report.total_duration:.1f}s"
                    }
                ]
            },
            {"type": "divider"},
            # Results summary
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Test Results:* {status_text}\n"
                            f":white_check_mark: *Passed:* {report.passed_tests}  |  "
                            f":x: *Failed:* {report.failed_tests}  |  "
                            f":bar_chart: *Pass Rate:* {report.pass_rate:.1f}%"
                }
            },
        ]

        # Add detailed test results with checkpoints
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":clipboard: Test Details",
                "emoji": True
            }
        })

        for result in report.results:
            # Test status icon (use checkmark for test cases)
            if result.status == "passed":
                test_icon = ":white_check_mark:"
            else:
                test_icon = ":x:"

            # Test name as section header (larger font)
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{test_icon} *{result.name}*\n_{result.module}_ | {result.duration:.1f}s"
                }
            })

            # Build checkpoint string (smaller font using context block)
            if result.checkpoints:
                checkpoint_parts = []
                for cp in result.checkpoints:
                    if cp.status == "passed":
                        cp_icon = ":large_green_circle:"
                    elif cp.status == "failed":
                        cp_icon = ":red_circle:"
                    else:  # skipped
                        cp_icon = ":white_circle:"
                    checkpoint_parts.append(f"{cp_icon} {cp.name}")

                # Use context block for smaller checkpoint text
                blocks.append({
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": "  ".join(checkpoint_parts)
                    }]
                })

            # Add error info for failed tests
            if result.status != "passed" and result.error_message:
                error_preview = result.error_message[:100].replace('\n', ' ')
                if len(result.error_message) > 100:
                    error_preview += "..."
                blocks.append({
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": f":warning: `{error_preview}`"
                    }]
                })

        # Footer
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f":robot_face: Generated by AdWave Test Tools | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }]
        })

        return blocks

    def generate_slack_text(self, report: TestReport) -> str:
        """
        Generate plain text summary for Slack (used as fallback).
        """
        status = "PASSED" if report.pass_rate == 100 else "FAILED"

        text = f"""*{report.title}* - {status}

*Summary:*
• Environment: {report.environment}
• LLM: {report.llm_provider} / {report.llm_model}
• Total: {report.total_tests} | Passed: {report.passed_tests} | Failed: {report.failed_tests}
• Pass Rate: {report.pass_rate:.1f}%
• Duration: {report.total_duration:.1f}s
"""

        failed_tests = [r for r in report.results if r.status != "passed"]
        if failed_tests:
            text += "\n*Failed Tests:*\n"
            for result in failed_tests[:5]:
                text += f"• `{result.name}` - {result.module}\n"
            if len(failed_tests) > 5:
                text += f"_...and {len(failed_tests) - 5} more_\n"

        return text

    def send_to_slack(
        self,
        report: TestReport,
        webhook_url: str,
        channel: Optional[str] = None,
        mention_on_failure: Optional[str] = None,
    ) -> bool:
        """
        Send test report to Slack via Incoming Webhook.

        Args:
            report: Test report data
            webhook_url: Slack Incoming Webhook URL
            channel: Optional channel override (if webhook allows)
            mention_on_failure: User/group to mention when tests fail
                               e.g., "@channel", "@here", "<@U12345678>"

        Returns:
            True if message sent successfully

        Example:
            generator.send_to_slack(
                report,
                webhook_url="https://hooks.slack.com/services/T00/B00/XXX",
                mention_on_failure="@channel"
            )
        """
        # Build message payload
        payload: Dict[str, Any] = {
            "blocks": self.generate_slack_blocks(report),
            "text": self.generate_slack_text(report),  # Fallback for notifications
        }

        # Add channel override if specified
        if channel:
            payload["channel"] = channel

        # Add mention if tests failed
        if mention_on_failure and report.failed_tests > 0:
            mention_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{mention_on_failure} Tests failed! Please check the report."
                }
            }
            # Insert mention after header
            payload["blocks"].insert(1, mention_block)

        # Send to Slack
        try:
            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 200:
                    print("Report sent to Slack successfully")
                    return True
                else:
                    print(f"Slack returned status {response.status}")
                    return False

        except urllib.error.HTTPError as e:
            print(f"Failed to send to Slack: HTTP {e.code} - {e.reason}")
            return False
        except urllib.error.URLError as e:
            print(f"Failed to send to Slack: {e.reason}")
            return False
        except Exception as e:
            print(f"Failed to send to Slack: {e}")
            return False


# =============================================================================
# Helper Functions
# =============================================================================

def extract_checkpoints_from_prompt(prompt: str) -> List[tuple]:
    """
    Auto-extract checkpoints from prompt text by parsing STEP markers.

    Parses patterns like:
        STEP 1: Login
        STEP 2: Navigate to Creatives

    Args:
        prompt: The task prompt string

    Returns:
        List of (step_number, step_name) tuples
    """
    if not prompt:
        return []

    # Pattern to match "STEP {n}: {description}"
    pattern = r'STEP\s+(\d+):\s*([^\n]+)'
    matches = re.findall(pattern, prompt, re.IGNORECASE)

    # Convert to list of tuples and deduplicate
    steps = []
    seen_steps = set()
    for num_str, name in matches:
        step_num = int(num_str)
        if step_num not in seen_steps:
            # Clean up the step name (remove trailing punctuation, etc.)
            clean_name = name.strip().rstrip(':').strip()
            steps.append((step_num, clean_name))
            seen_steps.add(step_num)

    # Sort by step number
    steps.sort(key=lambda x: x[0])
    return steps


def get_checkpoints_for_test(
    test_name: str,
    test_passed: bool,
    last_step: int = 0,
    prompt: str = None,
) -> List[Checkpoint]:
    """
    Get checkpoints for a test, auto-extracting from prompt if available.

    Args:
        test_name: Name of the test
        test_passed: Whether the test passed
        last_step: The last step that was attempted (0 means unknown)
        prompt: The task prompt (if available, checkpoints will be auto-extracted)

    Returns:
        List of Checkpoint objects with appropriate status
    """
    # Try to auto-extract from prompt first
    if prompt:
        steps = extract_checkpoints_from_prompt(prompt)
        if steps:
            # Successfully extracted from prompt
            pass
        else:
            # Fallback to generic steps
            steps = _get_fallback_steps(test_name)
    else:
        # No prompt provided, use fallback
        steps = _get_fallback_steps(test_name)

    # Convert to Checkpoint objects with status
    checkpoints = []
    total_steps = len(steps)

    for step_num, step_name in steps:
        if test_passed:
            status = "passed"
        elif last_step > 0:
            if step_num < last_step:
                status = "passed"
            elif step_num == last_step:
                status = "failed"
            else:
                status = "skipped"
        else:
            # Unknown failure point - mark last step as failed
            if step_num == total_steps:
                status = "failed"
            else:
                status = "passed"

        checkpoints.append(Checkpoint(
            step=step_num,
            name=step_name,
            status=status,
        ))

    return checkpoints


def _get_fallback_steps(test_name: str) -> List[tuple]:
    """
    Get fallback steps based on test name keywords.
    Used when prompt is not available for auto-extraction.
    """
    # Generic fallback steps
    return [
        (1, "Login"),
        (2, "Navigate"),
        (3, "Execute Task"),
        (4, "Verify Result"),
    ]


def extract_last_step_from_result(result: str) -> int:
    """Extract the last step number mentioned in the result."""
    if not result:
        return 0

    # Find all step mentions
    step_matches = re.findall(r'(?:STEP|Step|step)\s*(\d+)', result)
    if step_matches:
        return int(step_matches[-1])
    return 0


def analyze_error(error_message: str, result: str = "") -> str:
    """
    Analyze error and provide a summary.
    This is a simple rule-based analysis. Can be enhanced with AI later.
    """
    analysis_lines = []
    error_lower = error_message.lower() if error_message else ""
    result_lower = result.lower() if result else ""

    # Common error patterns
    if "timeout" in error_lower:
        analysis_lines.append("• Page load or element wait timeout")
    if "element" in error_lower and ("not found" in error_lower or "not visible" in error_lower):
        analysis_lines.append("• UI element not found - selector may have changed")
    if "login" in error_lower or "auth" in error_lower:
        analysis_lines.append("• Authentication issue - check credentials")
    if "upload" in error_lower or "file" in error_lower:
        analysis_lines.append("• File upload failed - check file path and format")
    if "click" in error_lower:
        analysis_lines.append("• Click action failed - element may be obscured")
    if "network" in error_lower or "connection" in error_lower:
        analysis_lines.append("• Network connectivity issue")

    # Try to identify which step failed
    step_matches = re.findall(r'(?:step|STEP)\s*(\d+)', result_lower)
    if step_matches:
        last_step = step_matches[-1]
        analysis_lines.append(f"• Failed at or after Step {last_step}")

    if not analysis_lines:
        analysis_lines.append("• Unknown error - check screenshot and logs for details")

    return "\n".join(analysis_lines)


def extract_key_error_log(error_message: str, max_lines: int = 5) -> str:
    """Extract the most relevant lines from an error message."""
    if not error_message:
        return ""

    lines = error_message.strip().split('\n')

    # Priority keywords for relevant lines
    priority_keywords = ['error', 'failed', 'exception', 'timeout', 'not found', 'assert']

    # Find lines with priority keywords
    priority_lines = []
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in priority_keywords):
            priority_lines.append(line.strip())

    # Return priority lines if found, otherwise first/last lines
    if priority_lines:
        return '\n'.join(priority_lines[:max_lines])
    else:
        # Return first and last lines
        if len(lines) <= max_lines:
            return '\n'.join(lines)
        else:
            return '\n'.join(lines[:2] + ['...'] + lines[-2:])
