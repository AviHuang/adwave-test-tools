# AdWave Test Tools

Automated end-to-end testing tool for the AdWave platform using Browser Use.

## Overview

This repository contains automated tests for verifying AdWave platform functionality. It uses [Browser Use](https://github.com/browser-use/browser-use), an AI-powered browser automation framework, to test the platform like a real user would.

## Features

- **Campaign Tests**: Create campaigns with Push, Pop, Display, Native ad formats
- **Creative Tests**: Upload creatives for Push, Display, Native formats
- **Audience Tests**: Create audience segments
- **Registration Tests**: Full registration flow with email verification
- **Multi-LLM Support**: Gemini (recommended), OpenAI, Claude, Ollama (experimental)
- **HTML Reports**: Detailed test reports with screenshots and checkpoints
- **Slack/Email Reports**: Send reports automatically

## Test Coverage

| Module | Tests | Description |
|--------|-------|-------------|
| Registration | 1 | Full registration flow with email verification |
| Campaign | 4 | Push, Pop, Display, Native campaign creation |
| Creative Upload | 3 | Push, Display, Native creative upload |
| Creative Delete | 1 | Delete all test creatives in one task |
| Audience | 1 | Audience segment creation |

**Total: 10 tests**

---

## Quick Start

### 1. Install Dependencies

```bash
# Create conda environment
conda create -n browser-use python=3.11 -y
conda activate browser-use

# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Copy the `.env` file provided by your team, or create from template:

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Tests

```bash
# Run all tests with Gemini (recommended)
pytest tests/ -v --headed

# Run specific test
pytest tests/test_creative.py -v --headed
```

---

## LLM Provider Configuration

### Gemini API (Recommended)

Gemini is the default and most stable option.

**Configuration (.env):**
```bash
GOOGLE_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3-flash-preview
```

**Run tests:**
```bash
# Auto-detect (uses Gemini if GOOGLE_API_KEY is set)
pytest tests/ -v --headed

# Explicit
pytest tests/ -v --headed --llm=gemini
```

### Ollama Local Model (Experimental)

> ⚠️ **Warning**: Local models have limited support for browser-use's structured output format. Test success rate is lower than cloud APIs.

**Prerequisites:**
```bash
# Install Ollama
# Download from: https://ollama.ai/

# Start Ollama server
ollama serve

# Pull model
ollama pull qwen2.5:7b
```

**Configuration (.env):**
```bash
# Optional - defaults shown
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:7b
```

**Run tests:**
```bash
pytest tests/ -v --headed --llm=ollama

# With specific model
pytest tests/ -v --headed --llm=ollama --model=qwen2.5:7b
```

**Local Model Limitations:**
- Cannot reliably produce JSON structured output
- May output incorrect action formats
- `sensitive_data` placeholder mechanism may not work (types `{email}` literally)
- Recommended only for experimentation

### Other Providers

**OpenAI:**
```bash
OPENAI_API_KEY=your-openai-key
pytest tests/ -v --llm=openai
```

**Claude:**
```bash
ANTHROPIC_API_KEY=your-anthropic-key
pytest tests/ -v --llm=claude
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests (headless)
pytest tests/ -v

# Run with visible browser (headed mode)
pytest tests/ -v --headed

# Run with HTML report
pytest tests/ -v --report

# Run with Slack notification
pytest tests/ -v --report --slack
```

### Run Specific Tests

```bash
# Campaign tests
pytest tests/test_campaign.py -v --headed

# Specific campaign format
pytest "tests/test_campaign.py::test_create_campaign[Campaign_Push]" -v --headed
pytest "tests/test_campaign.py::test_create_campaign[Campaign_Display]" -v --headed

# Creative tests
pytest tests/test_creative.py -v --headed

# Specific creative format
pytest "tests/test_creative.py::test_upload_creative[Upload_Push]" -v --headed
pytest "tests/test_creative.py::test_upload_creative[Upload_Display]" -v --headed

# Audience test
pytest tests/test_audience_create.py -v --headed

# Registration test (requires Gmail config)
pytest tests/test_registration.py -v --headed
```

### Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--headed` | Show browser window | `pytest -v --headed` |
| `--llm=` | Select LLM provider | `--llm=gemini` |
| `--model=` | Select specific model | `--model=qwen2.5:7b` |
| `--report` | Generate HTML report | `pytest -v --report` |
| `--slack` | Send to Slack | `pytest -v --report --slack` |
| `--email=` | Send email report | `--email=you@example.com` |
| `--env=` | Test environment | `--env=staging` |

---

## Project Structure

```
adwave-test-tools/
├── core/                           # Core modules
│   ├── browser_agent.py            # Browser Use wrapper with LLM configuration
│   ├── config.py                   # Environment and LLM configuration
│   ├── gmail_helper.py             # Gmail IMAP for verification codes
│   ├── prompts.py                  # Task prompts for automation
│   └── reporter.py                 # HTML/Slack/Email report generator
│
├── tests/                          # Test files
│   ├── conftest.py                 # Pytest fixtures and hooks
│   ├── test_campaign.py            # Campaign creation tests
│   ├── test_creative.py            # Creative upload/delete tests
│   ├── test_audience_create.py     # Audience segment tests
│   ├── test_registration.py        # Registration with email verification
│   │
│   └── helpers/                    # Test helper functions
│       ├── campaign_helpers.py     # Extract campaign data from results
│       ├── creative_helpers.py     # Verify creative counts
│       └── registration_helpers.py # Parse registration results
│
├── assets/                         # Test images
│   ├── icon_192x192.png
│   ├── display_250x250.png
│   └── main_492x328.png
│
├── reports/                        # Generated HTML reports
├── .env.example                    # Environment template
├── requirements.txt
└── README.md
```

## Helper Modules

### `core/gmail_helper.py`
Gmail IMAP helper for registration tests. Uses Gmail's `+` alias feature to generate unlimited test email addresses:
- `yourname@gmail.com` → Main inbox
- `yourname+test123@gmail.com` → Also delivers to main inbox

Extracts verification codes automatically via IMAP.

### `tests/creative_helpers.py`
Parses agent output to extract creative counts:
```python
extract_creative_counts(result)  # Returns (before_count, after_count)
verify_creative_upload(result)   # Returns True if count increased
```

### `tests/campaign_helpers.py`
Extracts campaign list from agent output:
```python
extract_campaign_list(result)           # Returns list of campaign names
verify_campaign_in_list(result, name)   # Returns True if found
```

### `tests/registration_helpers.py`
Parses registration test results:
```python
extract_registration_email(result)   # Get email used
verify_registration_success(result)  # Check if registration succeeded
verify_login_success(result)         # Check if login succeeded
```

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `ADWAVE_EMAIL` | AdWave test account email |
| `ADWAVE_PASSWORD` | AdWave test account password |
| `GOOGLE_API_KEY` | Gemini API key (or other LLM key) |

### Optional - Email Reports

| Variable | Description |
|----------|-------------|
| `SMTP_SERVER` | SMTP server (default: smtp.gmail.com) |
| `SMTP_PORT` | SMTP port (default: 465) |
| `SMTP_USER` | Email sender address |
| `SMTP_PASSWORD` | Email password or app password |

### Optional - Slack Reports

| Variable | Description |
|----------|-------------|
| `SLACK_BOT_TOKEN` | Slack Bot Token (xoxb-...) |
| `SLACK_CHANNEL` | Channel ID or User ID for DM |

### Optional - Registration Tests

| Variable | Description |
|----------|-------------|
| `GMAIL_ADDRESS` | Gmail address (or reuse SMTP_USER) |
| `GMAIL_APP_PASSWORD` | Gmail App Password (or reuse SMTP_PASSWORD) |

### Optional - Ollama Local Model

| Variable | Description |
|----------|-------------|
| `OLLAMA_BASE_URL` | Ollama API endpoint (default: http://localhost:11434/v1) |
| `OLLAMA_MODEL` | Model name (default: qwen2.5:7b) |

---

## GitHub Actions

### Manual Trigger

1. Go to Actions tab
2. Select "AdWave Tests" workflow
3. Click "Run workflow"
4. Configure:
   - **Environment**: `production` or `staging`
   - **LLM provider**: `gemini`, `claude`, or `openai`
   - **Test scope**: Select tests to run
   - **Send email**: Optional email for report
5. Click "Run workflow"

### Test Scope Options

| Scope | Tests | Description |
|-------|-------|-------------|
| `all` | 10 | All tests |
| `registration` | 1 | Registration flow |
| `campaign` | 4 | All campaign tests |
| `creative` | 4 | All creative tests |
| `audience` | 1 | Audience creation |
| `campaign_push` | 1 | Push campaign only |
| `creative_display` | 1 | Display creative only |

---

## Troubleshooting

### Gemini API Errors

```
Error: API key not valid
```
→ Check `GOOGLE_API_KEY` in `.env`

### Ollama Connection Errors

```
Error: Connection refused
```
→ Ensure Ollama is running: `ollama serve`

### Ollama JSON Errors

```
validation errors for AgentOutput
action: Field required
```
→ This is a known limitation of local models. They struggle with structured JSON output. Use Gemini instead for reliable tests.

### Browser Not Visible

→ Add `--headed` flag: `pytest -v --headed`

---

## License

Internal use only - RevoSurge
