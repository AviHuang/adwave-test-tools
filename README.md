# AdWave Test Tools

Automated end-to-end testing tool for the AdWave platform using Browser Use.

## Overview

This repository contains automated tests for verifying AdWave platform functionality. It uses [Browser Use](https://github.com/browser-use/browser-use), an AI-powered browser automation framework, to test the platform like a real user would.

## Features

- **Login Tests**: Verify authentication flow
- **Campaign Tests**: Test campaign module functionality
- **Analytics Tests**: Verify analytics dashboard
- **Creative Library Tests**: Test asset management
- **Audience Tests**: Verify audience management

## Requirements

- Python 3.11+
- DeepSeek API key
- AdWave test account credentials

## Local Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/adwave-test-tools.git
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
# Edit .env with your credentials
```

## Running Tests

### Run all tests:
```bash
pytest tests/ -v
```

### Run specific module tests:
```bash
pytest tests/test_login.py -v
pytest tests/test_campaign.py -v
```

### Run with headed browser (for debugging):
```bash
pytest tests/ -v --headed
```

### Run against staging environment:
```bash
pytest tests/ -v --env=staging
```

## GitHub Actions

### Manual Trigger

1. Go to Actions tab
2. Select "AdWave Tests" workflow
3. Click "Run workflow"
4. Select environment and options
5. Click "Run workflow"

### Automatic Trigger

Tests automatically run when:
- AdWave main repository pushes to main/develop branch
- A `repository_dispatch` event is received

### Setting Up Cross-Repo Trigger

To enable automatic testing when AdWave repo has new commits:

1. Create a Personal Access Token (PAT) with `repo` scope
2. Add the PAT as `TEST_DISPATCH_TOKEN` secret in AdWave repo
3. Add this workflow to AdWave repo at `.github/workflows/trigger-tests.yml`:

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
          repository: your-org/adwave-test-tools
          event-type: adwave-deploy
          client-payload: '{"ref": "${{ github.ref }}", "sha": "${{ github.sha }}"}'
```

## Project Structure

```
adwave-test-tools/
├── .github/workflows/
│   └── run-tests.yml       # Test workflow
├── core/
│   ├── __init__.py
│   ├── browser_agent.py    # Browser Use wrapper
│   └── config.py           # Configuration
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_login.py
│   ├── test_campaign.py
│   ├── test_analytics.py
│   ├── test_creative.py
│   └── test_audience.py
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key for LLM |
| `ADWAVE_EMAIL` | Test account email |
| `ADWAVE_PASSWORD` | Test account password |
