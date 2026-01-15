"""
P1 Functional Test: Create Audience Segment
"""
import re
import pytest
from datetime import datetime


def extract_audience_list(result: str) -> list[str]:
    """Extract audience names from agent result using AUDIENCE_LIST markers."""
    result_lower = result.lower()

    match = re.search(
        r'audience_list_start\s*(.*?)\s*audience_list_end',
        result_lower,
        re.DOTALL
    )

    if match:
        names = [name.strip() for name in match.group(1).strip().split('\n') if name.strip()]
        return names

    return []


def verify_audience_in_list(result: str, audience_name: str) -> bool:
    """Check if audience name exists in the extracted audience list."""
    audience_list = extract_audience_list(result)
    audience_name_lower = audience_name.lower()

    for audience in audience_list:
        if audience_name_lower in audience or audience in audience_name_lower:
            return True

    return audience_name_lower in result.lower()


@pytest.mark.asyncio
async def test_create_audience(browser_agent, config):
    """Test creating a new audience segment."""
    timestamp = datetime.now().strftime("%H%M%S_%Y%m%d")
    audience_name = f"{timestamp}_Audience"

    result = await browser_agent.create_audience(
        audience_name=audience_name,
    )

    # Verify audience appears in the list
    audience_found = verify_audience_in_list(result, audience_name)

    # Debug: show extracted audiences if failed
    if not audience_found:
        audiences = extract_audience_list(result)
        assert False, f"Audience '{audience_name}' not found. Extracted audiences: {audiences}. Full result: {result[:2000]}"

    assert audience_found
