# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that scrapes astronomical research papers from NASA ADS and generates public-facing summaries using OpenAI's GPT. It's designed for CfA (Center for Astrophysics) staff to create newsletter content by converting technical abstracts into accessible summaries.

## Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
```

**Important**: The requirements.txt is incomplete - you'll need to install `python-dotenv` which is used in the code:
```bash
pip install python-dotenv
```

### Running the Application
```bash
# Default: CfA papers from 2025
python cfascience.py

# Custom year and affiliation examples
python cfascience.py --start-year 2024
python cfascience.py --affiliation 'aff:"MIT"' --start-year 2023 --end-year 2024
python cfascience.py --help  # See all options
```

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_cfascience.py

# Run tests with coverage (requires pytest-cov)
pytest --cov=cfascience

# Run specific test class or method
pytest tests/test_cfascience.py::TestExtractAuthorsAffiliations
pytest tests/test_cfascience.py::TestExtractAuthorsAffiliations::test_extract_with_matching_authors_and_affiliations
```

### Configuration
Create `api_keys.env` file with required API keys:
- NASA ADS API token
- OpenAI API key

## Code Architecture

### Single-file Design
The entire application is contained in `cfascience.py` (435 lines) with a functional organization:

- **API Integration**: `fetch_abstracts()` handles NASA ADS queries
- **Data Processing**: `extract_authors_affiliations()` parses author data
- **UI Formatting**: Rich terminal output with ANSI colors, CfA authors highlighted in magenta
- **AI Integration**: `summarize_abstracts()` uses OpenAI GPT-4o for summary generation

### Key Functionality Flow
1. Queries NASA ADS for 2025 papers with CfA/Smithsonian affiliations
2. Displays papers with formatted author lists (CfA authors highlighted)
3. User selects papers to summarize
4. Generates public-friendly summaries via OpenAI API

### Configuration Constants
Hard-coded query parameters target specific institutional affiliations and date ranges. These are embedded in the code and may need updates for different time periods or institutions.

## Dependencies and APIs

### External APIs
- **NASA ADS**: Astrophysics database queries
- **OpenAI**: GPT-4o model for text summarization

### Missing Dependencies
If you encounter import errors, note that `python-dotenv` is used but not listed in requirements.txt.

## Testing

No formal testing framework is implemented. This is a utility script without automated tests.

## Branch Structure

- `main`: Production/stable branch
- `dev`: Development branch (currently active)