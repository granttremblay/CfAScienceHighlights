# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that scrapes astronomical research papers from NASA ADS and generates public-facing summaries using OpenAI's GPT. It's designed for CfA (Center for Astrophysics) staff to create newsletter content by converting technical abstracts into accessible summaries.

The repository includes two main tools:
1. **cfascience.py** - Interactive terminal interface for exploring and summarizing papers
2. **create_google_doc.py** - Google Docs integration that automatically generates formatted documents

## Development Commands

### Setup and Installation
```bash
# Main dependencies
pip install -r requirements.txt

# For Google Docs integration (optional)
pip install -r requirements_google_docs.txt
```

**Important**: The requirements.txt is incomplete - you'll need to install `python-dotenv` which is used in the code:
```bash
pip install python-dotenv
```

### Running the Application

**Terminal Interface:**
```bash
# Default: CfA papers from 2025
python cfascience.py

# Custom year and affiliation examples
python cfascience.py --start-year 2024
python cfascience.py --affiliation 'aff:"MIT"' --start-year 2023 --end-year 2024
python cfascience.py --help  # See all options
```

**Google Docs Integration:**
```bash
# Creates/updates a static Google Doc with all papers, abstracts, and AI summaries
python create_google_doc.py
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

For Google Docs integration, additional setup is required:
- Google Cloud Console project with Google Docs API enabled
- OAuth2 credentials downloaded as `credentials.json`
- See `GOOGLE_DOCS_SETUP.md` for complete instructions

## Code Architecture

### Main Components

#### cfascience.py (Terminal Interface)
The interactive terminal application (435 lines) with a functional organization:

- **API Integration**: `fetch_abstracts()` handles NASA ADS queries
- **Data Processing**: `extract_authors_affiliations()` parses author data
- **UI Formatting**: Rich terminal output with ANSI colors, CfA authors highlighted in magenta
- **AI Integration**: `summarize_abstracts()` uses OpenAI GPT-4o for summary generation

#### create_google_doc.py (Google Docs Integration)
Automated document generation system that:
- **Static Document Management**: Creates and maintains a single, permanent Google Doc
- **Content Management**: Clears and updates document content with each run
- **Image Processing**: Handles logo insertion with automatic resizing (currently disabled)
- **API Integration**: Uses Google Docs API for document creation and formatting
- **Data Integration**: Imports functionality from `cfascience.py` for paper fetching and processing

### Key Functionality Flow

#### Terminal Interface (cfascience.py)
1. Queries NASA ADS for 2025 papers with CfA/Smithsonian affiliations
2. Displays papers with formatted author lists (CfA authors highlighted)
3. User selects papers to summarize
4. Generates public-friendly summaries via OpenAI API

#### Google Docs Integration (create_google_doc.py)
1. Authenticates with Google Docs API (OAuth2 flow)
2. Gets or creates a static document (permanent URL)
3. Fetches all 10 recent papers from NASA ADS
4. Generates AI summaries for all papers automatically
5. Clears existing document content
6. Populates document with formatted content including abstracts and summaries
7. Provides permanent shareable link

### Configuration Constants
Hard-coded query parameters target specific institutional affiliations and date ranges. These are embedded in the code and may need updates for different time periods or institutions.

## Dependencies and APIs

### External APIs
- **NASA ADS**: Astrophysics database queries
- **OpenAI**: GPT-4o model for text summarization

### Missing Dependencies
If you encounter import errors, note that `python-dotenv` is used but not listed in requirements.txt.

## Testing

No formal testing framework is implemented for the Google Docs integration. The original cfascience.py has basic testing infrastructure.

## Branch Structure

- `main`: Production/stable branch
- `dev`: Development branch (currently active)