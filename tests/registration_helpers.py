"""
Helper functions for registration tests.

Provides utilities for parsing agent results and verifying registration outcomes.
"""
import re
from typing import Optional


def extract_registration_email(result: str) -> str:
    """
    Extract the registration email from agent result.

    Args:
        result: Full result string from browser agent

    Returns:
        Email address used for registration, or empty string if not found
    """
    match = re.search(r'REGISTRATION_EMAIL:\s*(\S+@\S+)', result)
    return match.group(1) if match else ""


def extract_verification_code(result: str) -> str:
    """
    Extract the verification code from agent result.

    Args:
        result: Full result string from browser agent

    Returns:
        Verification code, or empty string if not found
    """
    match = re.search(r'VERIFICATION_CODE:\s*([A-Za-z0-9]{4,8})', result)
    return match.group(1) if match else ""


def extract_registration_message(result: str) -> str:
    """
    Extract the registration status message from agent result.

    Args:
        result: Full result string from browser agent

    Returns:
        Status message, or empty string if not found
    """
    match = re.search(r'REGISTRATION_MESSAGE:\s*(.+?)(?:\n|$)', result)
    return match.group(1).strip() if match else ""


def verify_login_success(result: str) -> bool:
    """
    Verify login with new account was successful.

    Args:
        result: Full result string from browser agent

    Returns:
        True if login appears successful, False otherwise
    """
    # Check for new format: REGISTRATION_RESULT_START block
    result_block = re.search(
        r'REGISTRATION_RESULT_START\s*(.*?)\s*REGISTRATION_RESULT_END',
        result, re.DOTALL | re.IGNORECASE
    )
    if result_block:
        block_content = result_block.group(1).lower()
        if "login_success: true" in block_content or "login_success:true" in block_content:
            return True

    # Check for explicit login success marker
    login_match = re.search(r'LOGIN_SUCCESS:\s*(true|false)', result.lower())
    if login_match:
        return login_match.group(1) == "true"

    # Fallback: check for indicators of successful login
    result_lower = result.lower()
    success_indicators = [
        "/campaign",
        "dashboard",
        "welcome",
        "logged in",
        "login successful",
        "campaign list",
        "link your first product",
        "unlock the power of adwave",
        "registration and login successful",
    ]

    for indicator in success_indicators:
        if indicator in result_lower:
            return True

    return False


def verify_registration_success(result: str) -> bool:
    """
    Verify registration completed successfully.

    Checks for explicit success markers first, then falls back to
    keyword detection in the result. Also considers login success
    as confirmation of successful registration.

    Args:
        result: Full result string from browser agent

    Returns:
        True if registration appears successful, False otherwise
    """
    # Check for new format: REGISTRATION_RESULT_START block
    result_block = re.search(
        r'REGISTRATION_RESULT_START\s*(.*?)\s*REGISTRATION_RESULT_END',
        result, re.DOTALL | re.IGNORECASE
    )
    if result_block:
        block_content = result_block.group(1).lower()
        reg_success = "registration_success: true" in block_content or "registration_success:true" in block_content
        login_success = "login_success: true" in block_content or "login_success:true" in block_content
        if reg_success and login_success:
            return True

    # Check for explicit success/failure marker
    success_match = re.search(r'REGISTRATION_SUCCESS:\s*(true|false)', result.lower())
    if success_match:
        explicit_success = success_match.group(1) == "true"
        # If registration reported success, also check login
        if explicit_success:
            return verify_login_success(result)
        return False

    # Fallback: check for common success indicators
    success_keywords = [
        "it is all set",
        "registration completed",
        "successfully registered",
        "registration complete",
        "account created",
        "let's start your journey",
    ]

    result_lower = result.lower()
    for keyword in success_keywords:
        if keyword in result_lower:
            # Also verify login succeeded
            return verify_login_success(result)

    # Check for failure indicators
    failure_keywords = [
        "failed to receive verification",
        "registration failed",
        "invalid",
        "already exists",
        "email taken",
        "error occurred",
    ]

    for keyword in failure_keywords:
        if keyword in result_lower:
            return False

    # Default to False if unclear
    return False


def get_registration_summary(result: str) -> dict:
    """
    Extract a complete summary of the registration attempt.

    Args:
        result: Full result string from browser agent

    Returns:
        Dictionary with email, code, registration success, login success, and message
    """
    return {
        "email": extract_registration_email(result),
        "verification_code": extract_verification_code(result),
        "registration_success": verify_registration_success(result),
        "login_success": verify_login_success(result),
        "message": extract_registration_message(result),
    }
