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

## Usage

To run the script, use the following command:
```bash
python cfascience.py
```

### Options (yet to come)

- I will add options to this code over time, but for now, a scrape from 2025 is hard-coded.