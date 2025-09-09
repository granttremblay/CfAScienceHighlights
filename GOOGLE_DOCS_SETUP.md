# Google Docs Integration Setup

This guide explains how to set up and use the Google Docs integration for CfA Science Highlights.

## Prerequisites

1. **Existing setup**: Make sure you have the main `cfascience.py` working with both:
   - NASA ADS API token in `api_keys.env`
   - OpenAI API key in `api_keys.env` (for generating public summaries)

2. **Google Cloud Account**: You need a Google account with access to Google Cloud Console

## Setup Steps

### 1. Install Additional Dependencies

```bash
pip install -r requirements_google_docs.txt
```

### 2. Google Cloud Console Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Create or Select Project**:
   - Create a new project or select an existing one
   - Project name suggestion: "CfA Science Highlights"

3. **Enable Google Docs API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Docs API"
   - Click on it and press "Enable"

4. **Create Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - If prompted, configure the OAuth consent screen first:
     - Choose "External" user type
     - Fill in required fields (App name, User support email, Developer email)
     - Add your email to test users
   - For Application type, choose "Desktop application"
   - Name it something like "CfA Highlights Docs Creator"
   - Click "Create"

5. **Download Credentials**:
   - After creating, click the download button (⬇️) next to your new credential
   - Save the downloaded JSON file as `credentials.json` in your project directory

### 3. First Run Authentication

The first time you run the script, it will:
1. Open your web browser
2. Ask you to sign in to Google
3. Ask for permission to create and edit Google Docs
4. Save an access token for future use

## Usage

### Basic Usage

```bash
python create_google_doc.py
```

This will:
- Fetch the 10 most recent CfA papers from 2025
- Use a **single, static Google Doc** that never changes URL
- Clear the existing content and add fresh data each run
- Include paper titles, authors, journals, publication dates, abstracts, and AI summaries
- Add clickable links to search for each paper on NASA ADS

**Important**: The first time you run the script, it will create a new document and save the document ID to `google_doc_config.txt`. All subsequent runs will reuse the same document, simply updating its content.

### The Created Document Will Include

- **Document title**: "CfA Science Highlights - [Month Year]"
- **For each paper**:
  - Paper title and year
  - Journal/publication information
  - Publication date
  - Author list (simplified for readability)
  - Clickable link to search for the paper on NASA ADS
  - **Full abstract** from the original paper
  - **AI-generated public summary** (2 paragraphs, written for general audience)

### Example Output

The script will output something like:

**First Run:**
```
CfA Science Highlights - Google Docs Creator
==================================================
Authenticating with Google...
Fetching papers from NASA ADS...
Found 10 papers
Getting static Google Doc...
Created new static document: 1AbCdEfG123...
This document ID will be reused for all future runs.
Clearing existing content...
Adding content to document (this may take several minutes for AI summaries)...

Processing paper 1: A Revolutionary Discovery in Exoplanet Atmospheres...
   Generating public summary...
...

✅ Success! Google Doc updated with abstracts and AI summaries:
📄 Title: CfA Science Highlights - January 2025
🔗 Static URL: https://docs.google.com/document/d/1AbCdEfG123.../edit
📊 Papers included: 10
💾 Document ID saved to google_doc_config.txt - this URL will never change!
```

**Subsequent Runs:**
```
CfA Science Highlights - Google Docs Creator
==================================================
Authenticating with Google...
Fetching papers from NASA ADS...
Found 10 papers
Getting static Google Doc...
Using existing static document: 1AbCdEfG123...
Clearing existing content...
Adding content to document (this may take several minutes for AI summaries)...
...
✅ Success! Google Doc updated with abstracts and AI summaries:
🔗 Static URL: https://docs.google.com/document/d/1AbCdEfG123.../edit
💾 Document ID saved to google_doc_config.txt - this URL will never change!
```

## Customization

You can modify the `create_google_doc.py` script to:

- Change the document title format
- Modify the paper information included
- Adjust the formatting style
- Add custom search parameters (by modifying the `fetch_abstracts()` call)

## Troubleshooting

### Common Issues

1. **"credentials.json not found"**:
   - Make sure you downloaded the credentials file from Google Cloud Console
   - Ensure it's named exactly `credentials.json` and in the project directory

2. **"Authentication failed"**:
   - Check that the Google Docs API is enabled in your Google Cloud project
   - Make sure you're using OAuth 2.0 Client ID credentials (not Service Account)

3. **"No papers found"**:
   - Verify your NASA ADS API token in `api_keys.env`
   - Check that `cfascience.py` works independently

4. **Permission denied errors**:
   - Make sure you granted permission when the browser opened during first run
   - Delete `token.json` and run again to re-authenticate

### File Structure

After setup, you should have:

```
CfAScienceHighlights/
├── cfascience.py
├── create_google_doc.py
├── credentials.json        # From Google Cloud Console
├── token.json             # Auto-created after first auth
├── google_doc_config.txt  # Auto-created, stores static document ID
├── api_keys.env           # Your existing NASA ADS API key
├── requirements.txt       # Original requirements
├── requirements_google_docs.txt
└── GOOGLE_DOCS_SETUP.md   # This file
```

### Static Document Behavior

- **First run**: Creates a new Google Doc and saves its ID to `google_doc_config.txt`
- **Subsequent runs**: Reuses the same document, clearing and updating content
- **URL never changes**: Bookmark the URL from the first run - it's permanent!
- **Lost config file?**: If you delete `google_doc_config.txt`, the script will create a new document

## Security Notes

- Never commit `credentials.json` or `token.json` to version control
- These files contain sensitive authentication information
- The `credentials.json` file allows access to create/edit Google Docs in your account
- Consider adding these files to your `.gitignore`