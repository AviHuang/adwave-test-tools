"""
Gmail IMAP helper for reading verification emails.

Uses Gmail's '+' alias feature to generate unlimited test email addresses,
all of which deliver to the same inbox. Verification codes are extracted
via IMAP, avoiding the need to navigate temporary email websites.

Example:
    - Main inbox: yourname@gmail.com
    - Alias: yourname+20250119_143052@gmail.com → delivers to yourname@gmail.com

Supports SOCKS proxy for corporate network environments where direct
connections to Gmail IMAP are blocked.
"""
import imaplib
import email
import os
import re
import socket
import time
from datetime import datetime
from email.header import decode_header
from typing import Optional

# Try to import socks for proxy support
try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False


class GmailHelper:
    """Helper class to read emails via IMAP for registration verification."""

    def __init__(
        self,
        email_address: str,
        app_password: str,
        proxy_host: str = None,
        proxy_port: int = None,
    ):
        """
        Initialize Gmail helper.

        Args:
            email_address: Gmail address (e.g., yourname@gmail.com)
            app_password: Gmail App Password (16 characters, generated from Google Account settings)
            proxy_host: SOCKS5 proxy host (default: from SOCKS_PROXY env or 127.0.0.1)
            proxy_port: SOCKS5 proxy port (default: from SOCKS_PROXY env or 7891)
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap_server = "imap.gmail.com"

        # Configure SOCKS proxy (for corporate networks)
        # Priority: parameters > environment variable > default
        if proxy_host and proxy_port:
            self.proxy_host = proxy_host
            self.proxy_port = proxy_port
        elif os.getenv("SOCKS_PROXY"):
            # Parse SOCKS_PROXY=host:port
            proxy_env = os.getenv("SOCKS_PROXY")
            if ":" in proxy_env:
                self.proxy_host, port_str = proxy_env.rsplit(":", 1)
                self.proxy_port = int(port_str)
            else:
                self.proxy_host = proxy_env
                self.proxy_port = 7891
        else:
            # Default: Clash Verge mixed proxy port
            self.proxy_host = "127.0.0.1"
            self.proxy_port = 7897

    def _create_imap_connection(self):
        """
        Create IMAP connection, using SOCKS proxy if available.

        Returns:
            IMAP4_SSL connection object
        """
        if SOCKS_AVAILABLE:
            # Use SOCKS proxy
            socks.set_default_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            socket.socket = socks.socksocket
            print(f"Using SOCKS5 proxy: {self.proxy_host}:{self.proxy_port}")

        return imaplib.IMAP4_SSL(self.imap_server)

    def generate_alias(self, suffix: Optional[str] = None) -> str:
        """
        Generate a unique email alias using Gmail's '+' feature.

        Args:
            suffix: Custom suffix for the alias. If None, uses readable timestamp.

        Returns:
            Email alias (e.g., yourname+20250119_143052@gmail.com)
        """
        if suffix is None:
            # Use readable timestamp format: YYYYMMDD_HHMMSS
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        username, domain = self.email_address.split("@")
        return f"{username}+{suffix}@{domain}"

    def wait_for_verification_code(
        self,
        alias_email: str,
        timeout: int = 120,
        poll_interval: int = 5,
        sender_filter: str = "revosurge",
        start_time_override: datetime = None,
    ) -> str:
        """
        Wait for and extract verification code from email.

        Polls the Gmail inbox via IMAP, looking for emails matching:
        1. Sender contains sender_filter (e.g., "revosurge")
        2. To/Delivered-To header contains alias_email (primary filter)
        3. Received AFTER start_time_override (if provided)

        After successful extraction, marks the email as read to prevent
        re-processing in future test runs.

        Args:
            alias_email: The alias email address to check (used for To: header matching)
            timeout: Maximum seconds to wait for email
            poll_interval: Seconds between inbox checks
            sender_filter: Filter emails by sender (partial match, case-insensitive)
            start_time_override: Optional start time to filter old emails (default: now)

        Returns:
            Extracted verification code, or empty string if not found within timeout
        """
        mail = self._create_imap_connection()
        mail.login(self.email_address, self.app_password)

        # Use override time if provided (should be set before Phase 1 starts)
        search_start_time = start_time_override if start_time_override else datetime.now()
        start_time = time.time()

        print(f"Searching for verification email to: {alias_email}")
        print(f"Search started at: {search_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sender filter: {sender_filter}")

        try:
            mail.select("inbox")

            while time.time() - start_time < timeout:

                # Search for emails from today (don't require UNSEEN - email might be auto-read)
                # Using SINCE filter to limit to recent emails
                today_str = search_start_time.strftime("%d-%b-%Y")
                _, messages = mail.search(None, f'(SINCE "{today_str}")')

                message_ids = messages[0].split()
                if message_ids:
                    print(f"Found {len(message_ids)} email(s) from today, checking...")

                for msg_num in message_ids:
                    # Fetch email with FLAGS to check/modify read status
                    _, msg_data = mail.fetch(msg_num, "(RFC822)")
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    # Get email metadata for logging
                    sender = msg.get("From", "").lower()
                    subject = msg.get("Subject", "")
                    to_addr = msg.get("To", "").lower()
                    delivered_to = msg.get("Delivered-To", "").lower()
                    email_date = self._parse_email_date(msg.get("Date", ""))
                    email_time = email_date.strftime('%H:%M:%S') if email_date else "unknown"

                    # Check sender matches filter
                    if sender_filter.lower() not in sender:
                        # Only log first poll to avoid spam
                        if time.time() - start_time < poll_interval + 1:
                            print(f"  Skipping (sender): {sender[:40]}...")
                        continue

                    # Check if email is addressed to our alias (primary filter for alias emails)
                    # Use exact match on the email address portion
                    alias_lower = alias_email.lower()
                    email_matches_alias = (
                        alias_lower in to_addr or
                        alias_lower in delivered_to or
                        alias_lower.split('@')[0] in to_addr  # Also check username+suffix part
                    )
                    if not email_matches_alias:
                        # Email is from revosurge but not to our alias - skip
                        print(f"  Skipping (wrong recipient): To={to_addr[:40]}, want={alias_lower[:30]}")
                        continue

                    # Check email date - must be AFTER search started (backup filter)
                    # If we can't parse the date, skip the email to be safe
                    if email_date is None:
                        print(f"  Skipping (unparseable date): {subject[:50]}")
                        continue
                    if email_date < search_start_time:
                        print(f"  Skipping old ({email_time}): {subject[:50]}")
                        continue

                    # Log that we're checking this email
                    print(f"  Checking email ({email_time}): {subject[:50]}")

                    # Extract body and find verification code
                    body = self._get_email_body(msg)
                    code = self._extract_code(body)

                    if code:
                        print(f"✓ Found verification code in email:")
                        print(f"  From: {sender}")
                        print(f"  To: {to_addr}")
                        print(f"  Expected alias: {alias_lower}")
                        print(f"  Subject: {subject}")
                        print(f"  Time: {email_time}")
                        print(f"  Code: {code}")

                        # Verify the To address matches our alias (double-check)
                        if alias_lower not in to_addr and alias_lower not in delivered_to:
                            print(f"  ⚠️ WARNING: Email To address doesn't match expected alias!")
                            print(f"  Delivered-To: {delivered_to}")
                            # Continue searching instead of returning wrong code
                            continue

                        # Mark email as read (SEEN) to prevent re-processing
                        mail.store(msg_num, '+FLAGS', '\\Seen')
                        print(f"  Email marked as read")

                        return code
                    else:
                        # Debug: print first 500 chars of body to understand format
                        body_preview = body[:500].replace('\n', '\\n').replace('\r', '')
                        print(f"  No verification code found in email body")
                        print(f"  Body preview: {body_preview}...")

                time.sleep(poll_interval)
                elapsed = int(time.time() - start_time)
                print(f"Waiting for verification email... ({elapsed}s / {timeout}s)")

            print(f"✗ Timeout waiting for verification email after {timeout}s")
            return ""

        finally:
            try:
                mail.logout()
            except Exception:
                pass

    def _parse_email_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse email Date header into datetime object.

        Converts timezone-aware dates to local time for comparison.

        Args:
            date_str: Email Date header string

        Returns:
            datetime object in local time, or None if parsing fails
        """
        if not date_str:
            return None

        # Common email date formats
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",      # RFC 2822: "Mon, 19 Jan 2025 14:30:52 +0800"
            "%a, %d %b %Y %H:%M:%S %Z",      # With timezone name
            "%d %b %Y %H:%M:%S %z",          # Without weekday
            "%a, %d %b %Y %H:%M:%S",         # Without timezone
        ]

        # Remove extra whitespace and parenthetical timezone names
        date_str = re.sub(r'\s+\([^)]+\)', '', date_str).strip()

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Convert to local time if timezone aware
                if dt.tzinfo:
                    # Convert to local time, then remove tzinfo for naive comparison
                    dt = dt.astimezone().replace(tzinfo=None)
                return dt
            except ValueError:
                continue

        return None

    def _get_email_body(self, msg) -> str:
        """Extract text body from email message."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode("utf-8", errors="replace")
                    except Exception:
                        pass
                elif content_type == "text/html":
                    try:
                        return part.get_payload(decode=True).decode("utf-8", errors="replace")
                    except Exception:
                        pass
        else:
            try:
                return msg.get_payload(decode=True).decode("utf-8", errors="replace")
            except Exception:
                pass
        return ""

    def _extract_code(self, body: str) -> str:
        """
        Extract verification code from email body.

        Tries multiple common patterns for verification codes:
        - HTML styled codes (spans with styling) - most specific
        - Chinese format: 验证码：123456
        - English formats: code: 123456, verification: 123456
        - Alphanumeric codes (like M4JPD3) with mixed letters/digits
        """
        # Common verification code patterns (ordered by specificity - most specific first)
        patterns = [
            # HTML span with color styling (common for highlighted codes)
            r'<span[^>]*style="[^"]*color[^"]*">([A-Z0-9]{6})</span>',
            # Code in styled div/span with letter-spacing (formatted code box)
            r'letter-spacing[^>]*>\s*(?:<span[^>]*>)?([A-Z0-9]{6})(?:</span>)?',
            # HTML bold code
            r'<strong>([A-Za-z0-9]{6})</strong>',
            # Chinese format: 验证码：ABC123
            r'验证码[：:]\s*([A-Za-z0-9]{4,8})',
            # Explicit patterns with text context
            r'verification\s+code[：:\s]+([A-Za-z0-9]{4,8})',
            r'your\s+code\s+is[：:\s]+([A-Za-z0-9]{4,8})',
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                code = match.group(1).upper()
                # Validate: must have mixed content (not common words)
                # Good code: M4JPD3, ABC123, 123456
                # Bad: CODE, CURSOR, LETTER (common words)
                if self._is_valid_code(code):
                    return code

        # Fallback: Look for standalone 6-char alphanumeric with at least one digit
        # This catches codes like M4JPD3 that have mixed letters and numbers
        fallback_pattern = r'\b([A-Z][A-Z0-9]{4}[A-Z0-9])\b|\b([0-9][A-Z0-9]{4}[A-Z0-9])\b'
        for match in re.finditer(fallback_pattern, body, re.IGNORECASE):
            code = (match.group(1) or match.group(2)).upper()
            if self._is_valid_code(code):
                return code

        return ""

    def _is_valid_code(self, code: str) -> bool:
        """
        Check if a code looks like a valid verification code.

        Valid codes:
        - Have mixed content (letters + digits, or varied characters)
        - Are not common English words
        """
        # Common words that might accidentally match
        invalid_words = {
            'CODE', 'CURSOR', 'LETTER', 'NUMBER', 'STRING', 'STYLE',
            'COLOR', 'WIDTH', 'HEIGHT', 'MARGIN', 'BORDER', 'BUTTON',
            'EMAIL', 'LOGIN', 'SUBMIT', 'VERIFY', 'HEADER', 'FOOTER',
        }

        if code in invalid_words:
            return False

        # Must have at least 2 different characters
        if len(set(code)) < 2:
            return False

        # Prefer codes with mixed letters and digits
        has_letter = any(c.isalpha() for c in code)
        has_digit = any(c.isdigit() for c in code)

        # If it's all letters, it might be a word - be more careful
        if has_letter and not has_digit:
            # All-letter 6-char codes are suspicious unless they look random
            # Check if it looks like a random string (no common patterns)
            return len(set(code)) >= 4  # At least 4 unique chars

        return True

    def check_connection(self) -> bool:
        """
        Test IMAP connection to verify credentials.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            mail = self._create_imap_connection()
            mail.login(self.email_address, self.app_password)
            mail.logout()
            return True
        except Exception as e:
            print(f"Gmail connection failed: {e}")
            return False
