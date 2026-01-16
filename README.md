# AdWave Test Tools

Automated end-to-end testing tool for the AdWave platform using Browser Use.

## Overview

This repository contains automated tests for verifying AdWave platform functionality. It uses [Browser Use](https://github.com/browser-use/browser-use), an AI-powered browser automation framework, to test the platform like a real user would.

## Features

- **Campaign Tests**: Create campaigns with Push, Pop, Display, Native ad formats
- **Creative Tests**: Upload creatives for Push, Display, Native formats
- **Audience Tests**: Create audience segments
- **Multi-LLM Support**: OpenAI, Claude, Gemini providers
- **HTML Reports**: Detailed test reports with screenshots and checkpoints
- **Email Reports**: Send reports via email automatically

## Test Coverage

| Module | Tests | Description |
|--------|-------|-------------|
| Campaign | 4 | Push, Pop, Display, Native campaign creation |
| Creative Upload | 3 | Push, Display, Native creative upload |
| Creative Delete | 1 | Delete all test creatives in one task |
| Audience | 1 | Audience segment creation |

**Total: 9 tests**

## Requirements

- Python 3.11+
- LLM API key (OpenAI, Claude, or Gemini)
- AdWave test account credentials

## Local Setup

1. Clone the repository:
```bash
git clone https://github.com/anthropic-solutions/adwave-test-tools.git
cd adwave-test-tools
```

2. Create and activate conda environment:
```bash
conda create -n adwave-test python=3.11 -y
conda activate adwave-test
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials and API keys
```

## Running Tests

### Run all tests:
```bash
pytest tests/ -v
```

### Run with visible browser (headed mode):
```bash
pytest tests/ -v --headed
```

### Run with HTML report:
```bash
pytest tests/ -v --report
```

### Run and send report via email:
```bash
pytest tests/ -v --report --email=your@email.com
```

### Run specific test module:
```bash
pytest tests/test_campaign_push.py -v --headed
pytest tests/test_creative_display.py -v --headed
pytest tests/test_audience_create.py -v --headed
```

### Select LLM provider:
```bash
pytest tests/ -v --llm=gemini
pytest tests/ -v --llm=claude
pytest tests/ -v --llm=openai
```

### Run against staging environment:
```bash
pytest tests/ -v --env=staging
```

## Project Structure

```
adwave-test-tools/
├── .github/workflows/
│   └── run-tests.yml           # GitHub Actions workflow
├── assets/                     # Test images for creative upload
│   ├── icon_192x192.png
│   ├── display_250x250.png
│   └── main_492x328.png
├── core/
│   ├── __init__.py
│   ├── browser_agent.py        # Browser Use wrapper
│   ├── config.py               # Configuration management
│   ├── prompts.py              # Task prompts for automation
│   └── reporter.py             # HTML report generator
├── tests/
│   ├── conftest.py             # Pytest fixtures and hooks
│   ├── campaign_helpers.py     # Campaign test helpers
│   ├── creative_helpers.py     # Creative test helpers
│   ├── test_campaign_push.py
│   ├── test_campaign_pop.py
│   ├── test_campaign_display.py
│   ├── test_campaign_native.py
│   ├── test_creative_push.py
│   ├── test_creative_display.py
│   ├── test_creative_native.py
│   ├── test_creative_delete.py # Delete all test creatives
│   └── test_audience_create.py
├── reports/                    # Generated test reports
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
├── ISSUES.md                   # Known issues documentation
└── README.md
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ADWAVE_EMAIL` | Yes | AdWave test account email |
| `ADWAVE_PASSWORD` | Yes | AdWave test account password |
| `GOOGLE_API_KEY` | One of | Gemini API key |
| `ANTHROPIC_API_KEY` | these | Claude API key |
| `OPENAI_API_KEY` | three | OpenAI API key |
| `SMTP_USER` | No | Email sender address |
| `SMTP_PASSWORD` | No | Email password/app password |

### GitHub Secrets (for CI/CD)

| Secret | Description |
|--------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `ADWAVE_EMAIL` | Test account email |
| `ADWAVE_PASSWORD` | Test account password |

## Test Reports

Reports are generated in the `reports/` directory with:
- Test summary (pass/fail counts, duration)
- Checkpoints for each test step
- Screenshots on success/failure
- AI-powered error analysis

## GitHub Actions

### Manual Trigger

1. Go to Actions tab
2. Select "AdWave Tests" workflow
3. Click "Run workflow"
4. Configure options:
   - **Environment**: `production` or `staging`
   - **LLM provider**: `gemini`, `claude`, or `openai`
   - **Test scope**: Select specific tests to run
   - **Send email**: Optional email address for report
5. Click "Run workflow"

### Test Scope Options

| Scope | Tests | Description |
|-------|-------|-------------|
| `all` | 9 | Run all tests (default) |
| `campaign` | 4 | All campaign creation tests |
| `creative` | 4 | All creative tests (upload + delete) |
| `audience` | 1 | Audience creation test |
| `campaign_push` | 1 | Push campaign only |
| `campaign_pop` | 1 | Pop campaign only |
| `campaign_display` | 1 | Display campaign only |
| `campaign_native` | 1 | Native campaign only |
| `creative_push` | 1 | Push creative upload only |
| `creative_display` | 1 | Display creative upload only |
| `creative_native` | 1 | Native creative upload only |
| `creative_delete` | 1 | Delete all test creatives |

### Automatic Trigger (Cross-Repository)

Tests can be triggered automatically when AdWave main repository has new commits.

**Default behavior**: Runs **all tests** with `gemini` provider against `production` environment.

#### Setup Steps

1. Create a Personal Access Token (PAT) with `repo` scope
2. Add the PAT as `TEST_DISPATCH_TOKEN` secret in AdWave main repository
3. Add this workflow file to AdWave repo at `.github/workflows/trigger-tests.yml`:

```yaml
name: Trigger E2E Tests

on:
  push:
    branches: [main, develop]

jobs:
  trigger-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger test repository
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.TEST_DISPATCH_TOKEN }}
          repository: AviHuang/adwave-test-tools
          event-type: adwave-deploy
          client-payload: |
            {
              "environment": "production",
              "llm": "gemini",
              "scope": "all",
              "email": ""
            }
```

#### Customizing Auto-Trigger

Modify `client-payload` to customize automatic test runs:

```yaml
# Run only campaign tests
client-payload: '{"scope": "campaign"}'

# Run with email notification
client-payload: '{"scope": "all", "email": "team@example.com"}'

# Run specific test
client-payload: '{"scope": "campaign_push"}'
```

### Required GitHub Secrets

Configure these in repository Settings → Secrets and variables → Actions:

| Secret | Required | Description |
|--------|----------|-------------|
| `GOOGLE_API_KEY` | Yes* | Gemini API key |
| `ANTHROPIC_API_KEY` | Yes* | Claude API key |
| `OPENAI_API_KEY` | Yes* | OpenAI API key |
| `ADWAVE_EMAIL` | Yes | Test account email |
| `ADWAVE_PASSWORD` | Yes | Test account password |
| `SMTP_SERVER` | No | SMTP server (default: smtp.gmail.com) |
| `SMTP_PORT` | No | SMTP port (default: 465) |
| `SMTP_USER` | No | Email sender address |
| `SMTP_PASSWORD` | No | Email password/app password |

*At least one LLM API key is required based on selected provider.

## License

Internal use only - Anthropic Solutions
