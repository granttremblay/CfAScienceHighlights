# CfA Science Highlights for the Public
A script to scrape CfA-led papers from ADS and generate public-facing summaries of those results. This at least gives a decent starting point for newletter content, etc.

Use at your own risk, manually pick a great figure from the paper, and carefully vet the results before reporting out.

## Installation

1. Clone the repository in a parent directory of your choosing:
    ```bash
    git clone https://github.com/yourusername/CfAScienceHighlights.git
    cd CfAScienceHighlights
    ```

2. Create or switch to a virtual Python environment of your choosing (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a file called `api_keys.env` in the root directory of the project and add both a NASA ADS and OpenAI API key to it. The file contents should look like this:

    ```python
    NASA_ADS_API_KEY=your_nasa_ads_api_key
    OPENAI_API_KEY=your_openai_api_key
    ```

    You can [create a NASA ADS API token here ](https://ui.adsabs.harvard.edu/help/api/), and an [OpenAI Platform API key here](https://platform.openai.com/api-keys). The former is free, requiring only a NASA ADS account, while the latter requires a paid quanta of tokens for OpenAI ChatGPT chat completions. $10 should be enough for plenty of uses of this code. Contact Grant Tremblay if you need help with this key.



## Usage

### Basic Usage
```bash
python cfascience.py
```

### Command Line Options

The script now supports command line arguments to customize search parameters:

```bash
# Default: CfA papers from 2025
python cfascience.py

# Search papers from a specific year
python cfascience.py --start-year 2024

# Search papers from a year range
python cfascience.py --start-year 2023 --end-year 2024

# Search papers from a custom affiliation (MIT example)
python cfascience.py --affiliation 'aff:"MIT"'

# Combine options: MIT papers from 2024-2025
python cfascience.py --affiliation 'aff:"MIT"' --start-year 2024 --end-year 2025

# Get help and see all options
python cfascience.py --help
```

#### Available Options:
- `--start-year YEAR`: Start year for search (default: 2025)
- `--end-year YEAR`: End year for search (default: same as start year)
- `--affiliation STRING`: Custom affiliation string in ADS query format (default: CfA/Smithsonian)

#### Affiliation String Examples:
- CfA/Smithsonian (default): `pos(aff:"02138",1) pos(aff:"Smithsonian",1)`
- MIT: `aff:"MIT"`
- Harvard: `aff:"Harvard"`
- Multiple institutions: `aff:"MIT" OR aff:"Harvard"`

## Screenshots


After running `python cfascience.py`, the user should see something like this:

![Screenshot of the script in action](screenshots/1.png)

When the user then enters a comma-separated list of the abstracts to summarize (e.g. `3,4,8`), you will see something that looks like this:
![Screenshot of the script in action](screenshots/2.png)

The user may enter `n` should they not wish to see any summaries, and instead cleanly exit the script.

## Configuration Notes

The script now supports flexible configuration through command line arguments. Default values maintain backward compatibility:
- **Default year**: 2025 
- **Default affiliation**: CfA/Smithsonian affiliations
- **Paper type**: Only refereed papers are included
- **Result limit**: Maximum 10 most recent papers