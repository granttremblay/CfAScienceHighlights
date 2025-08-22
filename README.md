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

To run the script, use the following command:
```bash
python cfascience.py
```

## Screenshots


After running `python cfascience.py`, the user should see something like this:

![Screenshot of the script in action](screenshots/1.png)

When the user then enters a comma-separated list of the abstracts to summarize (e.g. `3,4,8`), you will see something that looks like this:
![Screenshot of the script in action](screenshots/2.png)

The user may enter `n` should they not wish to see any summaries, and instead cleanly exit the script.

### Options (yet to come)

- I will add options to this code over time, but for now, a scrape from 2025 is hard-coded.