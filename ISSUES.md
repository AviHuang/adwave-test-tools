# AdWave Platform Issues

This document records issues encountered during automated testing that need to be communicated with the development team.

---

## Issue #1: Audience data not syncing across sessions

**Date:** 2025-01-15

**Description:**
After creating an Audience Segment in the browser, the data is only visible in the current browser session. It does not appear when:
- Logging in with the same account from a different Chrome profile
- Logging in with the same account from a different device
- Only visible in the browser session where it was created

**Steps to Reproduce:**
1. Login to AdWave platform
2. Navigate to Audience page
3. Click "+ Create Audience"
4. Fill in Name, select "Ad Impression" under Behavioural, select "Last 3 Days" for Recency
5. Click "Run", then click "Create Audience Segment"
6. Audience appears in the list (in current browser)
7. Login with the same account from another browser/device
8. The created Audience is not visible

**Expected Behavior:**
Created Audience should be visible across all sessions when logged in with the same account.

**Questions for Dev Team:**
1. Is the Audience data being correctly written to the database?
2. Can you check if these records exist in the database?
3. Is the frontend fetching data from API or from local cache?
4. Please check the Network panel to see the API request/response when creating Audience.

**Status:** Open

---

## Issue #2: Registration Test Agent Does Not Auto-Stop After Login (RESOLVED)

**Date:** 2025-01-19
**Resolved:** 2025-01-19

**Description:**
The registration test used a multi-phase approach where the Agent would not automatically terminate after completing the login step.

**Root Cause:**
The multi-phase architecture (Phase 1: Enter email → IMAP wait → Phase 2: Complete registration) made it difficult for the Agent to understand when the task was complete. The `register_should_stop_callback` mechanism did not work reliably.

**Solution:**
Refactored to a **single-flow architecture** using a custom action:

1. **Single Agent executes all steps** - No more splitting into Phase 1/Phase 2
2. **Custom `get_verification_code` action** - Agent calls this action when it needs the verification code
3. **Clear success indicator** - Prompt tells Agent to use "done" action when seeing "Link your first Product" page

```python
# New approach: Single flow with custom action
tools = Tools()

@tools.action("Get verification code from email")
def get_verification_code():
    return gmail_helper.wait_for_verification_code(...)

agent = Agent(task=task, tools=tools, sensitive_data=...)
await agent.run()
```

**Key Changes:**
- `core/browser_agent.py`: New `register_account()` method using single-flow approach
- `core/prompts.py`: New `SINGLE_FLOW_REGISTRATION` prompt template
- Agent now correctly calls "done" action when task is complete

**Status:** ✅ Resolved

---
