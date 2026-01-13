"""
Test report generator for AdWave tests.
Generates HTML reports with screenshots and AI error analysis.
Supports email delivery.
"""
import os
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


@dataclass
class TestResult:
    """Individual test result."""
    name: str
    module: str
    status: str  # "passed", "failed", "error"
    duration: float
    error_analysis: Optional[str] = None  # AI-generated error analysis
    screenshot_base64: Optional[str] = None


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
                status_icon = "🟢" if result.status == "passed" else "🔴"
                duration_str = f"({result.duration:.1f}s)"

                # Error analysis for failed tests
                error_html = ""
                if result.error_analysis and result.status != "passed":
                    error_html = f'<p class="error">{result.error_analysis}</p>'

                # Screenshot for failed tests
                screenshot_html = ""
                if result.screenshot_base64 and result.status != "passed":
                    screenshot_html = f'''
                    <details>
                        <summary>Screenshot</summary>
                        <img src="data:image/png;base64,{result.screenshot_base64}" alt="Screenshot">
                    </details>
                    '''

                results_html += f'''
                    <li>
                        {status_icon} <code>{result.name}</code> <span class="duration">{duration_str}</span>
                        {error_html}
                        {screenshot_html}
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
