# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool that scrapes astronomical research papers from NASA ADS and generates public-facing summaries using OpenAI's GPT. It's designed for CfA (Center for Astrophysics) staff to create newsletter content by converting technical abstracts into accessible summaries.

The repository includes two main tools:
1. **cfascience.py** - Interactive terminal interface for exploring and summarizing papers
2. **create_google_doc.py** - Google Docs integration that automatically generates formatted documents with links to both NASA ADS and ArXiv (when available)

## Development Commands

### Setup and Installation
```bash
# Main dependencies
pip install -r requirements.txt

# For Google Docs integration (optional)
pip install -r requirements_google_docs.txt
```

All required dependencies are now included in requirements.txt.

### Running the Application

**Terminal Interface:**
```bash
# Default: CfA papers from 2025 (will prompt for search preferences)
python cfascience.py

# Custom year and affiliation examples (will prompt for search preferences)
python cfascience.py --start-year 2024
python cfascience.py --affiliation 'aff:"MIT"' --start-year 2023 --end-year 2024
python cfascience.py --help  # See all options
```

**Google Docs Integration:**
```bash
# Creates/updates a static Google Doc with papers and AI summaries (will prompt for search preferences)
python create_google_doc.py
```

**Interactive Search Options:**
Both scripts will prompt you to choose:
- **Author Position**: First author papers only vs. any author papers from the affiliation
- **Publication Type**: Refereed papers only vs. all papers (including preprints)

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

The codebase has been refactored for maintainability, reducing code duplication and improving modularity:

### Core Modules

#### utils.py (Shared Utilities)
Common functionality used across multiple scripts:
- **Environment Setup**: `setup_environment()` handles API key loading and OpenAI client initialization
- **Author Classification**: `is_cfa_affiliated()`, `classify_authors()` for institutional affiliation detection
- **Data Processing**: `extract_authors_affiliations()` parses NASA ADS author data
- **AI Integration**: `generate_summary()` provides unified OpenAI GPT-4o summary generation
- **UI Utilities**: `format_author_list_for_display()` for consistent terminal formatting
- **Color Constants**: Streamlined ANSI color codes for terminal output

#### cfascience.py (Terminal Interface)
The interactive terminal application with clean separation of concerns:
- **API Integration**: `fetch_abstracts()` handles NASA ADS queries with proper error handling
- **Query Building**: `build_query()` constructs flexible search parameters
- **UI Display**: `print_authors_affiliations()` for detailed author information display
- **User Interaction**: Interactive paper selection and summary generation with progress indicators
- **Command Line Interface**: Comprehensive argument parsing for custom searches

#### create_google_doc.py (Google Docs Integration)
Streamlined document generation system:
- **Document Management**: OAuth2 authentication and static document handling
- **Content Generation**: Integrates with shared utilities for consistent summary generation
- **Formatting**: Uses `google_docs_formatter.py` for clean document structure
- **Error Handling**: Robust error handling for API failures and authentication issues

#### google_docs_formatter.py (Document Formatting)
Dedicated module for Google Docs styling and structure:
- **Style Constants**: Centralized formatting definitions (fonts, colors, sizes)
- **Request Builders**: Modular functions for creating Google Docs API requests
- **Content Sections**: Specialized functions for headers, abstracts, summaries, and separators
- **Layout Management**: Professional document structure with consistent styling

### Key Functionality Flow

#### Shared Environment Setup
1. `utils.setup_environment()` loads API keys from `api_keys.env`
2. Initializes OpenAI client with error handling for missing keys
3. Returns configured clients for use across modules

#### Terminal Interface (cfascience.py)
1. Uses shared utilities to setup environment and classify authors
2. Queries NASA ADS with flexible search parameters (year range, custom affiliations)
3. Displays papers with consistent formatting (CfA authors highlighted in magenta)
4. User selects papers interactively
5. Generates summaries using shared `generate_summary()` function with author context
6. Displays results with detailed author affiliations and publication information

#### Google Docs Integration (create_google_doc.py)
1. Authenticates with Google Docs API using OAuth2 flow
2. Gets or creates a static document with persistent URL
3. Fetches papers using shared `fetch_abstracts()` function
4. Uses modular formatting functions from `google_docs_formatter.py`:
   - Document headers with timestamps
   - Paper titles and publication details with CfA authors highlighted separately
   - AI-generated public summaries with CfA author highlighting
   - Professional horizontal rule separators between papers
5. Adds hyperlinks to NASA ADS and ArXiv (when available) for each paper
6. Provides permanent shareable link with document statistics

### Configuration and Customization

**Flexible Search Parameters**: Both terminal and Google Docs interfaces support:
- Custom year ranges (`--start-year`, `--end-year`)
- Custom institution affiliations (`--affiliation`)
- Default CfA/Smithsonian queries with ZIP code targeting

**Styling Configuration**: `google_docs_formatter.py` centralizes:
- Font families, sizes, and weights
- Color schemes for different content types
- Document structure and spacing
- Professional formatting standards

**Environment Configuration**: All API keys and settings in `api_keys.env`:
- NASA ADS API token
- OpenAI API key
- Google Cloud OAuth2 credentials (separate file)

## Dependencies and APIs

### External APIs
- **NASA ADS**: Astrophysics database queries with proper error handling
- **OpenAI**: GPT-4o model for context-aware text summarization
- **Google Docs**: Document creation and formatting via Google API

### Dependency Management
All dependencies are properly specified in `requirements.txt`:
- `requests`: NASA ADS API calls
- `openai`: GPT model integration
- `python-dotenv`: Environment variable management
- `pytest` & `pytest-mock`: Testing framework

## Testing

**Comprehensive Test Suite** (`tests/test_cfascience.py`):
- Unit tests for all utility functions
- Author classification and affiliation detection
- API response handling and error conditions
- Color formatting and display functions
- Mock-based testing for external API calls
- Type checking and edge case coverage

**Test Coverage**: Core functionality including:
- Author-affiliation extraction and pairing
- CfA affiliation detection (case-insensitive)
- Author list formatting for terminal display
- NASA ADS API response processing
- OpenAI summary generation (mocked)
- Error handling for missing data

## Project Structure

```
├── cfascience.py              # Interactive terminal interface
├── create_google_doc.py       # Google Docs integration
├── utils.py                   # Shared utilities and common functions
├── google_docs_formatter.py   # Google Docs formatting utilities
├── tests/
│   ├── __init__.py
│   └── test_cfascience.py     # Comprehensive test suite
├── requirements.txt           # Core dependencies
├── requirements_google_docs.txt # Additional Google API dependencies
├── api_keys.env              # Environment variables (user-created)
├── credentials.json          # Google OAuth2 credentials (user-created)
└── CLAUDE.md                 # This documentation file
```

## Branch Structure

- `main`: Production/stable branch
- `dev`: Development branch (currently active)

## Code Quality Standards

The codebase follows strict quality standards to ensure maintainability, readability, and reliability:

**Type Safety**: All functions include comprehensive type hints for parameters and return values, improving IDE support and reducing runtime errors.

**Error Handling**: Robust exception handling with informative error messages throughout all modules, ensuring graceful failure modes.

**Documentation**: Detailed docstrings following Google style guide for every function, with clear parameter descriptions and return value specifications.

**Modularity**: Code organized into focused modules with single responsibilities, enabling easy testing and maintenance.

**Testing**: Comprehensive unit test suite with 28 passing tests covering core functionality, edge cases, and error conditions.

**Consistency**: Uniform naming conventions, formatting standards, and code structure throughout the entire codebase.

**Clean Code Principles**: Minimal redundancy, clear variable names, and optimized imports for better performance and readability.

## Recent Refactoring Benefits

The codebase has undergone significant refactoring to achieve:
- **Eliminated Code Duplication**: Common functionality consolidated into shared `utils.py` module
- **Enhanced Modularity**: Clear separation between terminal interface, Google Docs integration, and formatting utilities
- **Improved Maintainability**: Consistent patterns and reduced complexity across all modules
- **Better Error Handling**: Comprehensive input validation and graceful error recovery
- **Streamlined Dependencies**: Optimized imports and removed unnecessary code bloat