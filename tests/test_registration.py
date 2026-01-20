"""
P1 Functional Test: User Registration with Email Verification

Tests the complete registration flow using Gmail + alias + IMAP:
1. Navigate to AdWave homepage, click Sign Up
2. Enter email, click Next
3. Wait for verification code via IMAP
4. Enter code, click Confirm
5. Set password, click Next
6. Fill profile information, click Next
7. Verify success page, click to login
8. Login with new account, verify success

Prerequisites:
- Gmail account configured with App Password
- Environment variables: GMAIL_ADDRESS/SMTP_USER, GMAIL_APP_PASSWORD/SMTP_PASSWORD
"""
import pytest

from .registration_helpers import (
    extract_registration_email,
    extract_verification_code,
    verify_registration_success,
    verify_login_success,
    get_registration_summary,
)


@pytest.mark.asyncio
async def test_register_new_account(browser_agent, config):
    """
    Test complete registration flow with email verification and login.

    Registration Flow:
    1. Go to https://adwave.revosurge.com
    2. Click "Sign Up"
    3. Enter email (Gmail alias with timestamp), click "Next"
    4. [IMAP] Wait for verification code
    5. Enter verification code, click "Confirm"
    6. Enter Password + Confirm Password, click "Next"
    7. Fill profile: Full Name, Last Name, Company, Address, Country (Aruba), Industry
    8. Click "Next"
    9. Success page: "It is all set! Registration completed."
    10. Click button to go to login page
    11. Login with new account
    12. Verify successful login (redirect to /campaign)

    Requirements:
    - Gmail configured (GMAIL_ADDRESS + GMAIL_APP_PASSWORD or SMTP_USER + SMTP_PASSWORD)
    - AdWave site accessible
    """
    # Skip if Gmail not configured
    if not browser_agent.gmail_helper:
        pytest.skip(
            "Gmail not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD "
            "(or SMTP_USER and SMTP_PASSWORD) to run registration tests."
        )

    # Run registration flow
    result = await browser_agent.register_account(
        password="TestPassword123!",
        sender_filter="revosurge",  # Sender: noreply@revosurge.com
        verification_timeout=120,
    )

    # Extract registration details
    summary = get_registration_summary(result)
    email = summary["email"]
    code = summary["verification_code"]
    reg_success = summary["registration_success"]
    login_success = summary["login_success"]
    message = summary["message"]

    # Log results for debugging
    print(f"\nRegistration Summary:")
    print(f"  Email: {email}")
    print(f"  Verification Code: {code}")
    print(f"  Registration Success: {reg_success}")
    print(f"  Login Success: {login_success}")
    print(f"  Message: {message}")

    # Verify registration and login succeeded
    if not reg_success:
        # Provide detailed failure information
        assert False, (
            f"Registration failed.\n"
            f"Email used: {email}\n"
            f"Verification code: {code or 'Not received'}\n"
            f"Login success: {login_success}\n"
            f"Message: {message}\n"
            f"Full result (first 3000 chars): {result[:3000]}"
        )

    assert reg_success, "Registration and login should complete successfully"
