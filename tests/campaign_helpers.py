"""
Shared helper functions for campaign tests.
"""
import re


def extract_campaign_list(result: str) -> list[str]:
    """Extract campaign names from agent result using CAMPAIGN_LIST markers."""
    result_lower = result.lower()

    # Try to find the campaign list between markers
    match = re.search(
        r'campaign_list_start\s*(.*?)\s*campaign_list_end',
        result_lower,
        re.DOTALL
    )

    if match:
        # Split by newlines and clean up
        names = [name.strip() for name in match.group(1).strip().split('\n') if name.strip()]
        return names

    return []


def verify_campaign_in_list(result: str, campaign_name: str) -> bool:
    """Check if campaign name exists in the extracted campaign list."""
    campaign_list = extract_campaign_list(result)
    campaign_name_lower = campaign_name.lower()

    # Check if any campaign in the list matches (partial match for truncation)
    for campaign in campaign_list:
        if campaign_name_lower in campaign or campaign in campaign_name_lower:
            return True

    # Also check if campaign name appears anywhere in the result
    return campaign_name_lower in result.lower()
