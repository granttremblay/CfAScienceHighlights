# CfA Science Highlights for the Public

A Python CLI tool that scrapes recent astronomical research papers from NASA ADS (Astrophysics Data System) and generates accessible, public-facing summaries using OpenAI's GPT-4. Designed specifically for CfA (Center for Astrophysics | Harvard & Smithsonian) staff to create newsletter content by transforming technical abstracts into engaging summaries for general audiences.

## Features

- **Smart Paper Discovery**: Automatically queries NASA ADS for recent papers (2025) with CfA/Smithsonian affiliations
- **Visual Author Highlighting**: CfA-affiliated authors are highlighted in magenta for easy identification
- **Interactive Selection**: Browse and select papers of interest through an intuitive terminal interface
- **AI-Powered Summaries**: Generate public-friendly summaries using OpenAI's GPT-4o model
- **Rich Terminal Output**: Clean, colorful formatting with ANSI colors for better readability
- **Testing Suite**: Comprehensive unit tests using pytest

## Important Notes

⚠️ **Use at your own risk** - Always manually vet AI-generated content before publication  
📸 **Manual Figure Selection** - Remember to pick compelling figures from papers manually  
✅ **Review Required** - Carefully review all generated summaries before using in newsletters

## Prerequisites

- Python 3.7+
- NASA ADS API token (free with ADS account)
- OpenAI API key (paid service)

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/CfAScienceHighlights.git
    cd CfAScienceHighlights
    ```

2. **Set up virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure API keys**:
    Create `api_keys.env` in the project root:
    ```env
    ADS_API_TOKEN=your_nasa_ads_api_key
    OPENAI_API_KEY=your_openai_api_key
    ```

### Getting API Keys

- **NASA ADS API Token**: [Create free account and token](https://ui.adsabs.harvard.edu/help/api/)
- **OpenAI API Key**: [Get paid API access](https://platform.openai.com/api-keys) (~$10 covers extensive usage)

For assistance with OpenAI API keys, contact Grant Tremblay.



## Usage

### Basic Usage
```bash
python cfascience.py
```

### How It Works

1. **Paper Discovery**: The tool queries NASA ADS for recent papers (currently hardcoded to 2025) from authors affiliated with CfA/Smithsonian
2. **Paper Display**: Results are displayed with:
   - Paper titles, authors, and publication details
   - CfA-affiliated authors highlighted in magenta
   - Numbered list for easy selection
3. **Interactive Selection**: Enter comma-separated numbers (e.g., `3,4,8`) to select papers for summarization
4. **AI Summary Generation**: Selected papers are processed through OpenAI's GPT-4o to create public-friendly summaries
5. **Exit Options**: Enter `n` to exit without generating summaries

## Screenshots


After running `python cfascience.py`, the user should see something like this:

![Screenshot of the script in action](screenshots/1.png)

When the user then enters a comma-separated list of the abstracts to summarize (e.g. `3,4,8`), you will see something that looks like this:
![Screenshot of the script in action](screenshots/2.png)

The user may enter `n` should they not wish to see any summaries, and instead cleanly exit the script.

## Development

### Testing

The project includes a comprehensive test suite using pytest:

```bash
# Run all tests
pytest

# Run with verbose output  
pytest -v

# Run specific test file
pytest tests/test_cfascience.py

# Run with coverage (requires pytest-cov)
pytest --cov=cfascience

# Run specific test class or method
pytest tests/test_cfascience.py::TestExtractAuthorsAffiliations
```

### Code Architecture

- **Single-file design**: Core functionality contained in `cfascience.py` (435 lines)
- **Functional organization**: Clear separation of concerns
  - `fetch_abstracts()`: NASA ADS API integration
  - `extract_authors_affiliations()`: Author data parsing
  - `summarize_abstracts()`: OpenAI GPT-4o integration
  - Rich terminal formatting with ANSI colors

### Dependencies

- `requests`: HTTP client for NASA ADS API
- `openai`: OpenAI API client
- `python-dotenv`: Environment variable management
- `pytest`: Testing framework
- `pytest-mock`: Mock utilities for testing

## Configuration

### Customization Options

Current configuration is hardcoded but can be modified in `cfascience.py`:
- **Year filter**: Currently set to 2025 papers
- **Institution affiliations**: Targets CfA/Smithsonian authors
- **Color schemes**: ANSI color codes for terminal output
- **API models**: Uses OpenAI GPT-4o for summaries

### Future Enhancements

- Command-line argument support for year selection
- Configurable institution filtering
- Multiple output formats (JSON, markdown, etc.)
- Batch processing capabilities

## Troubleshooting

### Common Issues

1. **Missing python-dotenv**: Install with `pip install python-dotenv`
2. **API key errors**: Ensure `api_keys.env` file exists with correct keys
3. **Network issues**: Check NASA ADS and OpenAI API service status
4. **Rate limiting**: OpenAI API has usage limits; monitor your quota

### Getting Help

- Check existing issues and documentation
- For OpenAI API key assistance, contact Grant Tremblay
- Ensure all requirements are installed before reporting bugs

## License

This project is designed for internal CfA use. Please verify appropriate licensing before external distribution.