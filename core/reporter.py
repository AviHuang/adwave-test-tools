"""
Test report generator for AdWave tests.
Generates HTML reports with screenshots and AI error analysis.
Supports email delivery.
"""
import os
import re
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path
from typing import List, Optional
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


# =============================================================================
# Helper Functions
# =============================================================================

def get_checkpoints_for_test(test_name: str, test_passed: bool, last_step: int = 0) -> List[Checkpoint]:
    """
    Get predefined checkpoints based on the test name.
    Each test type has its own set of steps.

    Args:
        test_name: Name of the test
        test_passed: Whether the test passed
        last_step: The last step that was attempted (0 means unknown, use test status)
    """
    # Define checkpoints for each test type
    test_checkpoints = {
        # Campaign tests (7 steps)
        "campaign": [
            (1, "Login"),
            (2, "Switch Product"),
            (3, "Create Campaign"),
            (4, "Fill Campaign Details"),
            (5, "Upload Assets"),
            (6, "Review and Publish"),
            (7, "Verify Campaign Created"),
        ],
        # Audience test (6 steps)
        "audience": [
            (1, "Login"),
            (2, "Navigate to Audience"),
            (3, "Create New Audience"),
            (4, "Fill Audience Details"),
            (5, "Submit Audience"),
            (6, "Verify Audience Created"),
        ],
        # Creative upload tests (6 steps)
        "creative_upload": [
            (1, "Login"),
            (2, "Navigate to Creatives"),
            (3, "Add New Creative"),
            (4, "Choose Ad Format"),
            (5, "Upload Image"),
            (6, "Verify Upload"),
        ],
        # Creative delete tests (4 steps)
        "creative_delete": [
            (1, "Login"),
            (2, "Navigate to Creatives"),
            (3, "Delete All Creatives"),
            (4, "Verify Deletions"),
        ],
    }

    # Determine test type from test name
    test_name_lower = test_name.lower()
    if "campaign" in test_name_lower:
        steps = test_checkpoints["campaign"]
    elif "audience" in test_name_lower:
        steps = test_checkpoints["audience"]
    elif "delete" in test_name_lower and "creative" in test_name_lower:
        steps = test_checkpoints["creative_delete"]
    elif "creative" in test_name_lower:
        steps = test_checkpoints["creative_upload"]
    else:
        # Default generic steps
        steps = [
            (1, "Login"),
            (2, "Navigate"),
            (3, "Execute Task"),
            (4, "Verify Result"),
        ]

    # Convert to Checkpoint objects
    checkpoints = []
    total_steps = len(steps)

    for step_num, step_name in steps:
        if test_passed:
            # All steps passed
            status = "passed"
        elif last_step > 0:
            # We know which step failed
            if step_num < last_step:
                status = "passed"
            elif step_num == last_step:
                status = "failed"
            else:
                status = "skipped"
        else:
            # Unknown failure point - mark last step as failed, rest as skipped
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


def extract_checkpoints_from_result(result: str) -> List[Checkpoint]:
    """
    Legacy function - kept for compatibility.
    Prefer using get_checkpoints_for_test() instead.
    """
    checkpoints = []

    # Define step names based on common patterns in our prompts
    step_names = {
        1: "Login",
        2: "Navigate to Target Page",
        3: "Start Creation Flow",
        4: "Fill Details / Configure",
        5: "Upload / Submit",
        6: "Verify Result",
        7: "Final Verification",
    }

    # Find which steps are mentioned in the result
    for step_num in range(1, 8):
        patterns = [
            rf'STEP\s+{step_num}\b',
            rf'Step\s+{step_num}\b',
            rf'\[Step\s+{step_num}\]',
            rf'step\s+{step_num}\b',
        ]
        for pattern in patterns:
            if re.search(pattern, result, re.IGNORECASE):
                checkpoints.append(Checkpoint(
                    step=step_num,
                    name=step_names.get(step_num, f"Step {step_num}"),
                    status="passed",
                ))
                break

    # Deduplicate and sort
    seen_steps = set()
    unique_checkpoints = []
    for cp in checkpoints:
        if cp.step not in seen_steps:
            seen_steps.add(cp.step)
            unique_checkpoints.append(cp)

    unique_checkpoints.sort(key=lambda x: x.step)

    return unique_checkpoints


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
