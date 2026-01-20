"""
Prompt templates for browser automation tasks.
Extract prompts here for easy modification and reuse.
"""

# =============================================================================
# Common Steps (Reusable)
# =============================================================================

LOGIN = """
STEP {step}: Login
- Go to {login_url}
- Wait for the login page to fully load
- Enter {{email}} in the email input field
- Enter {{password}} in the password input field
- Click the "Login" button to submit the form
- Wait for redirect to campaign page
CHECKPOINT: URL should change to contain "/campaign" after successful login
"""

SWITCH_PRODUCT = """
STEP {step}: Switch Product
- Click the product dropdown/selector in the top-left corner of the page
- From the dropdown list, select "browser-use-test - https://revosrge.com"
- Wait for the page to refresh with the new product context
CHECKPOINT: The product selector should now display "browser-use-test"
"""

NAVIGATE_TO_AUDIENCE = """
STEP {step}: Navigate to Audience
- Click "Audience" in the left sidebar menu
- Wait for the Audience page to load
CHECKPOINT: URL should contain "/audience"
"""

NAVIGATE_TO_CAMPAIGN = """
STEP {step}: Navigate to Campaign
- Click "Campaign" in the left sidebar menu
- Wait for the Campaign page to load
CHECKPOINT: URL should contain "/campaign"
"""

# =============================================================================
# Verification Steps
# =============================================================================

VERIFY_CAMPAIGN_LIST = """
STEP {step}: Verify Campaign Created
- Navigate to campaign list if not already there (click Campaign in sidebar if needed)
- Look at the campaign list table
- Read and list ALL campaign names visible in the first page of the table

IMPORTANT: You must report the campaign names you see in this exact format:
CAMPAIGN_LIST_START
[list each campaign name on a separate line]
CAMPAIGN_LIST_END

Example output format:
CAMPAIGN_LIST_START
campaign_name_1
campaign_name_2
campaign_name_3
CAMPAIGN_LIST_END
"""

VERIFY_AUDIENCE_LIST = """
STEP {step}: Verify Audience Created
- Navigate to audience list if not already there
- Look at the audience list table
- Read and list ALL audience names visible in the first page of the table

IMPORTANT: You must report the audience names you see in this exact format:
AUDIENCE_LIST_START
[list each audience name on a separate line]
AUDIENCE_LIST_END

Example output format:
AUDIENCE_LIST_START
audience_name_1
audience_name_2
audience_name_3
AUDIENCE_LIST_END
"""

# =============================================================================
# Task-Specific Steps
# =============================================================================

CREATE_CAMPAIGN_FORM = """
STEP {step}: Create Campaign
- Click the "+ Create Campaign" button
- Wait for the campaign creation form/wizard to load
CHECKPOINT: Campaign creation form should be visible with input fields
"""

FILL_CAMPAIGN_DETAILS = """
STEP {step}: Fill Campaign Details
- Find the Campaign Name input field and type: "{campaign_name}"
- For Target Event: click the dropdown to open it, then click on "{target_event}" option in the list
- For Ad Format: click the dropdown to open it, then click on "{ad_format}" option in the list
- For Location Targeting (IMPORTANT - do this slowly):
  1. Click the Location dropdown to open it
  2. Wait for the dropdown list to fully appear
  3. Click on "Aruba" option in the list
  4. Wait and verify "Aruba" shows a checkmark or is highlighted as selected
  5. Only after confirming selection, click outside the dropdown to close it
- Find Target Bid input field and type: "{target_bid}"
- Find Budget input field and type: "{budget}"
- For Schedule section:
  - Leave Start Date as default (today)
  - Click the End Date field to open calendar picker
  - In the calendar, click on tomorrow's date (the day after today)
- Click "Next" button to proceed to asset upload step
CHECKPOINT: All fields should be filled and Next button should be clickable
"""

UPLOAD_ASSETS_PUSH = """
STEP {step}: Upload Assets and Fill Details
Select assets for Push ad format from library:
1. Click "Add from Library" button
2. In the library popup, click on "Push Ad Set1" to select it
3. Click "Add" button to confirm
CHECKPOINT: Images should be selected and displayed

After images are loaded, fill in the ad details:
- Find the Title input field and type: "Test Push Ad Title"
- Find the Description input field and type: "Test push notification message"
- Leave Destination URL as default (do not modify it)
CHECKPOINT: Title and Description fields should be filled

- After all details are filled, click "Next" button to proceed to review step
CHECKPOINT: Should advance to review/summary page
"""

UPLOAD_ASSETS_POP = """
STEP {step}: Upload Assets
Pop ad format does not require image uploads.
CHECKPOINT: Proceed directly, no upload areas should be required
- Click "Next" button to proceed to review step
CHECKPOINT: Should advance to review/summary page
"""

UPLOAD_ASSETS_DISPLAY = """
STEP {step}: Upload Assets
Select assets for Display ad format from library:
1. Click "Add from Library" button
2. In the library popup, click on the first available image to select it
3. Click "Add" button to confirm
CHECKPOINT: Image should be selected and displayed

After image is loaded:
- Leave Destination URL as default (do not modify it)
- Click "Next" button to proceed to review step
CHECKPOINT: Should advance to review/summary page
"""

UPLOAD_ASSETS_NATIVE = """
STEP {step}: Upload Assets and Fill Details
Select assets for Native ad format from library:
1. Click "Add from Library" button
2. In the library popup, click on the first available image to select it
3. Click "Add" button to confirm
CHECKPOINT: Image should be selected and displayed

After image is loaded, fill in the ad details:
- Find the Title input field and type: "Test Native Ad Title"
- Find the Description input field and type: "Test native ad description text"
- Leave Destination URL as default (do not modify it)
CHECKPOINT: Title and Description fields should be filled

- After all details are filled, click "Next" button to proceed to review step
CHECKPOINT: Should advance to review/summary page
"""

REVIEW_AND_PUBLISH = """
STEP {step}: Review and Publish
- Review the campaign summary showing all entered details
- Verify campaign name "{campaign_name}" is displayed correctly
- Click "Publish" or "Create Campaign" or "Submit" button to finalize
- Wait for success confirmation or redirect
CHECKPOINT: Should see success message or be redirected to campaign list
"""

CREATE_AUDIENCE_FORM = """
STEP {step}: Create New Audience
- Click the "+ Create Audience" button
- Wait for the New Segment form to load
CHECKPOINT: New Segment form should be visible with Name field
"""

FILL_AUDIENCE_DETAILS = """
STEP {step}: Fill Audience Details
- Find the Name input field and type: "{audience_name}"
- In Audience Segments section:
  1. Click the checkbox before "Ad Impression" (one click only)
  2. Wait for "Recency" section to expand below
  3. Click "Last 3 Days" in the Recency dropdown
  4. Click the "Run" button
CHECKPOINT: Name filled and Run clicked
"""

CREATE_AUDIENCE_SUBMIT = """
STEP {step}: Create Audience Segment
- Click the "Create Audience Segment" button at the bottom right
- Wait for success confirmation or redirect
CHECKPOINT: Should see success message or be redirected to audience list
"""


# =============================================================================
# Task Builders
# =============================================================================

def build_create_campaign_task(
    login_url: str,
    campaign_name: str,
    ad_format: str,
    target_event: str,
    target_bid: str,
    budget: str,
) -> str:
    """Build complete prompt for creating a campaign."""

    # Select asset upload step based on ad format
    asset_steps = {
        "Push": UPLOAD_ASSETS_PUSH,
        "Pop": UPLOAD_ASSETS_POP,
        "Display": UPLOAD_ASSETS_DISPLAY,
        "Native": UPLOAD_ASSETS_NATIVE,
    }
    upload_step = asset_steps.get(ad_format, UPLOAD_ASSETS_PUSH)

    task = (
        LOGIN.format(step=1, login_url=login_url) +
        SWITCH_PRODUCT.format(step=2) +
        CREATE_CAMPAIGN_FORM.format(step=3) +
        FILL_CAMPAIGN_DETAILS.format(
            step=4,
            campaign_name=campaign_name,
            target_event=target_event,
            ad_format=ad_format,
            target_bid=target_bid,
            budget=budget,
        ) +
        upload_step.format(step=5) +
        REVIEW_AND_PUBLISH.format(step=6, campaign_name=campaign_name) +
        VERIFY_CAMPAIGN_LIST.format(step=7)
    )

    return task


def build_create_audience_task(
    login_url: str,
    audience_name: str,
) -> str:
    """Build complete prompt for creating an audience."""

    task = (
        LOGIN.format(step=1, login_url=login_url) +
        NAVIGATE_TO_AUDIENCE.format(step=2) +
        CREATE_AUDIENCE_FORM.format(step=3) +
        FILL_AUDIENCE_DETAILS.format(step=4, audience_name=audience_name) +
        CREATE_AUDIENCE_SUBMIT.format(step=5) +
        VERIFY_AUDIENCE_LIST.format(step=6)
    )

    return task


# =============================================================================
# Creative Upload Steps
# =============================================================================

NAVIGATE_TO_CREATIVES = """
STEP {step}: Navigate to Creatives and Count
- Click "Creatives" in the left sidebar menu
- Wait for the Creatives page to load
- Count the total number of creative items currently in the list/grid
- Remember this count as BEFORE_COUNT
CHECKPOINT: URL should contain "/creatives", note the current count
"""

CREATE_CREATIVE_START = """
STEP {step}: Start Add New Creative
- Click the "+ Add New Creative(s)" button
- Wait for the "Upload Creative(s)" page to load
CHECKPOINT: "Choose ad format" window should appear
"""

CHOOSE_AD_FORMAT = """
STEP {step}: Choose Ad Format
- In the "Choose ad format" window, click on "{ad_format}"
- Click the "Next" button at bottom right
CHECKPOINT: Should proceed to upload area
"""

UPLOAD_CREATIVE_PUSH = """
STEP {step}: Upload Push Creative Images
IMPORTANT: Upload ONLY ONE set of images. Do NOT repeat or upload multiple times!

- Find the 192x192 Icon upload area and use upload_file action to upload: {icon_path}
- Find the 492x328 Main Image upload area and use upload_file action to upload: {main_path}
- Wait for both images to finish uploading
- After both uploads complete, click the "upload" button outside the upload areas (secondary confirmation)
- Wait for upload confirmation
- Click the "Add" button at bottom right

WARNING: After clicking "Add", do NOT upload again. One upload is sufficient.
CHECKPOINT: Creative should be added successfully
"""

UPLOAD_CREATIVE_DISPLAY = """
STEP {step}: Upload Display Creative Image
IMPORTANT: Upload ONLY ONE image. Do NOT repeat or upload multiple times!

- Find the 250x250 Main Image upload area and use upload_file action to upload: {image_path}
- Wait for image to finish uploading
- Click the "Add" button at bottom right

WARNING: After clicking "Add", do NOT upload again. One upload is sufficient.
CHECKPOINT: Creative should be added successfully
"""

UPLOAD_CREATIVE_NATIVE = """
STEP {step}: Upload Native Creative Image
IMPORTANT: Upload ONLY ONE image. Do NOT repeat or upload multiple times!

- Find the 492x328 Main Image upload area and use upload_file action to upload: {image_path}
- Wait for image to finish uploading
- Click the "Add" button at bottom right

WARNING: After clicking "Add", do NOT upload again. One upload is sufficient.
CHECKPOINT: Creative should be added successfully
"""

VERIFY_CREATIVE_UPLOAD = """
STEP {step}: Verify Upload Success
- After clicking "Add", wait for redirect back to creatives list
- Count the total number of creative items now in the list/grid (AFTER_COUNT)
- Compare with BEFORE_COUNT from earlier

IMPORTANT: Report the counts in this exact format:
CREATIVE_COUNT_BEFORE: [number]
CREATIVE_COUNT_AFTER: [number]
"""

# =============================================================================
# Creative Delete Steps
# =============================================================================

DELETE_MULTIPLE_CREATIVES = """
STEP {step}: Delete Multiple Creatives
You need to delete 3 creatives one by one. For each creative:
1. Find the creative with EXACT name in the "Creative Name" column
2. Click the trash/delete icon on the far right of that row
3. In the "Confirm Delete" dialog, click "Confirm"
4. Wait for the list to refresh before deleting the next one

IMPORTANT: Match names EXACTLY - do not delete items with similar names!

Creatives to delete (in order):
{creative_list}

Delete each one carefully, waiting for confirmation before proceeding to the next.
CHECKPOINT: All 3 creatives should be deleted
"""

VERIFY_CREATIVES_DELETED = """
STEP {step}: Verify All Deletions
- After all deletions complete, count the total number of creative items now in the list/grid (AFTER_COUNT)
- Compare with BEFORE_COUNT from earlier

IMPORTANT: Report the counts in this exact format:
CREATIVE_COUNT_BEFORE: [number]
CREATIVE_COUNT_AFTER: [number]
"""


def build_delete_creatives_task(
    login_url: str,
    creative_names: list[str],
) -> str:
    """Build complete prompt for deleting multiple creatives in one task."""

    # Format creative list
    creative_list = "\n".join([f"  - {name}" for name in creative_names])

    task = (
        LOGIN.format(step=1, login_url=login_url) +
        NAVIGATE_TO_CREATIVES.format(step=2) +
        DELETE_MULTIPLE_CREATIVES.format(step=3, creative_list=creative_list) +
        VERIFY_CREATIVES_DELETED.format(step=4)
    )

    return task


def build_create_creative_task(
    login_url: str,
    ad_format: str,
    icon_path: str = "",
    main_path: str = "",
    image_path: str = "",
) -> str:
    """Build complete prompt for uploading a creative."""

    # Select upload step based on ad format
    if ad_format == "Push":
        upload_step = UPLOAD_CREATIVE_PUSH.format(
            step=5,
            icon_path=icon_path,
            main_path=main_path,
        )
    elif ad_format == "Display":
        upload_step = UPLOAD_CREATIVE_DISPLAY.format(
            step=5,
            image_path=image_path,
        )
    elif ad_format == "Native":
        upload_step = UPLOAD_CREATIVE_NATIVE.format(
            step=5,
            image_path=image_path,
        )
    else:
        raise ValueError(f"Unknown ad format: {ad_format}")

    task = (
        LOGIN.format(step=1, login_url=login_url) +
        NAVIGATE_TO_CREATIVES.format(step=2) +
        CREATE_CREATIVE_START.format(step=3) +
        CHOOSE_AD_FORMAT.format(step=4, ad_format=ad_format) +
        upload_step +
        VERIFY_CREATIVE_UPLOAD.format(step=6)
    )

    return task


# =============================================================================
# Registration Steps (Multi-step Wizard)
# =============================================================================

# Single-flow registration prompt (Agent calls get_verification_code action when needed)
SINGLE_FLOW_REGISTRATION = """
Complete the full registration process on AdWave platform.

STEP 1: Navigate to Sign Up Page
- Go to {base_url}
- Click the "Sign Up" link/button
- Wait for the registration form to appear

STEP 2: Enter Email
- Enter email: {email_alias}
- Click "Next" button
- Wait for verification code page

STEP 3: Get and Enter Verification Code
- Use the "get_verification_code" action to retrieve the code from email
- Enter the verification code in the input field
- Click "Confirm" button (NOT "Resend"!)

STEP 4: Set Password
- Enter password: {{password}}
- Enter confirm password: {{password}}
- Click "Next" button

STEP 5: Fill Profile Information
Fill text fields:
- Full Name: Test
- Last Name: User
- Company Legal Name: Test Company LLC
- Company Business Address Line 1: 123 Test Street
- Company Business Address Line 2: Suite 100

For dropdown fields (CLICK to open, then CLICK an option):
- Country of Registration: Click the dropdown, then click "Aruba" from the list
- Industry: Click the dropdown, then click "Advertising and Marketing" from the list

⛔⛔⛔ CRITICAL: CLICK "NEXT" BUTTON ONLY! NEVER CLICK "BACK"! ⛔⛔⛔

STEP 6: Complete Registration
- Look for "It is all set!" message
- Click "Let's Start Your Journey" button

STEP 7: Login with New Account
- Enter email: {{email_alias}}
- Enter password: {{password}}
- Click "Login" button (NOT "Sign up"!)

SUCCESS: When you see the welcome page with "Link your first Product", use "done" action with message: "Registration and login successful"
"""


def build_single_flow_registration_task(
    base_url: str,
    email_alias: str,
) -> str:
    """Build prompt for single-flow registration."""
    return SINGLE_FLOW_REGISTRATION.format(
        base_url=base_url,
        email_alias=email_alias,
    )


