"""
Google Docs API Integration for CfA Science Highlights

This script creates a Google Doc containing the list of papers from NASA ADS
with hyperlinks to the original papers. It integrates with the existing
cfascience.py script to fetch the paper data.
"""

import os
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from datetime import datetime

# Import our existing cfascience functionality
try:
    from cfascience import fetch_abstracts, format_author_list
    from openai import OpenAI
    from dotenv import load_dotenv
except ImportError:
    print("Error: Could not import cfascience.py or required dependencies.")
    print("Make sure cfascience.py is in the same directory and openai/dotenv are installed.")
    sys.exit(1)

# Load environment variables and initialize OpenAI client
load_dotenv('api_keys.env')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Google API scopes
SCOPES = ['https://www.googleapis.com/auth/documents']

class GoogleDocsCreator:
    """Handles Google Docs API operations for creating science highlights documents."""
    
    def __init__(self, credentials_file='credentials.json', token_file='token.json', 
                 config_file='google_doc_config.txt'):
        """
        Initialize the Google Docs creator.
        
        Args:
            credentials_file: Path to the OAuth2 credentials JSON file
            token_file: Path to store the access token
            config_file: Path to store the static document ID
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.config_file = config_file
        self.service = None
        self.static_doc_id = self.load_document_id()
        
    def authenticate(self):
        """Authenticate with Google API and build the docs service."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no (valid) credentials available, prompt user to log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"Error: {self.credentials_file} not found.")
                    print("Please download your OAuth2 credentials from Google Cloud Console.")
                    print("See setup instructions in the script comments.")
                    return False
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('docs', 'v1', credentials=creds)
            return True
        except HttpError as error:
            print(f'An error occurred: {error}')
            return False
    
    def load_document_id(self):
        """Load the static document ID from config file."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    
    def save_document_id(self, doc_id):
        """Save the static document ID to config file."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write(doc_id)
        self.static_doc_id = doc_id
    
    def create_document(self, title="CfA Science Highlights"):
        """
        Create a new Google Doc.
        
        Args:
            title: Title for the document
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            document = {
                'title': title
            }
            doc = self.service.documents().create(body=document).execute()
            return doc.get('documentId')
        except HttpError as error:
            print(f'An error occurred creating document: {error}')
            return None
    
    def clear_document_content(self, document_id):
        """
        Clear all content from an existing Google Doc.
        
        Args:
            document_id: ID of the Google Doc to clear
        """
        try:
            # Get current document to find the end index
            doc = self.service.documents().get(documentId=document_id).execute()
            content = doc.get('body').get('content', [])
            
            # Find the actual end index by looking at the last element with content
            end_index = 1
            for element in content:
                if 'paragraph' in element:
                    # Check if paragraph has actual content (not just empty)
                    paragraph = element['paragraph']
                    if 'elements' in paragraph:
                        for elem in paragraph['elements']:
                            if 'textRun' in elem and elem.get('endIndex'):
                                end_index = max(end_index, elem['endIndex'])
                elif 'endIndex' in element:
                    end_index = max(end_index, element['endIndex'])
            
            # Only delete content if there's actually content to delete (more than just the initial empty paragraph)
            if end_index > 2:  # Changed from > 1 to > 2 to account for initial empty paragraph
                requests = [{
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': end_index - 1
                        }
                    }
                }]
                
                self.service.documents().batchUpdate(
                    documentId=document_id, body={'requests': requests}).execute()
                print("Document content cleared successfully.")
            else:
                print("Document is already empty or has minimal content.")
            
            return True
            
        except HttpError as error:
            # If the error is about empty range, that's actually fine - document is already empty
            if "The range should not be empty" in str(error):
                print("Document is already empty - no content to clear.")
                return True
            else:
                print(f'An error occurred clearing document: {error}')
                return False
    
    def get_or_create_static_document(self, title="CfA Science Highlights"):
        """
        Get the static document ID or create a new one if it doesn't exist.
        
        Args:
            title: Title for the document if creating new
            
        Returns:
            Document ID of the static document
        """
        if self.static_doc_id:
            # Verify the document still exists
            try:
                self.service.documents().get(documentId=self.static_doc_id).execute()
                print(f"Using existing static document: {self.static_doc_id}")
                return self.static_doc_id
            except HttpError:
                print("Static document no longer exists, creating new one...")
                self.static_doc_id = None
        
        # Create new document
        doc_id = self.create_document(title)
        if doc_id:
            self.save_document_id(doc_id)
            print(f"Created new static document: {doc_id}")
            print("This document ID will be reused for all future runs.")
        return doc_id
    
    
    def generate_summary(self, title, abstract, year):
        """
        Generate a public-facing summary using OpenAI, similar to cfascience.py.
        
        Args:
            title: Paper title
            abstract: Paper abstract
            year: Publication year
            
        Returns:
            Generated summary string
        """
        try:
            prompt = (
                f"Title: {title} (Year: {year})\n"
                f"Abstract: {abstract}\n\n"
                "Write a public-facing summary in two paragraphs for a "
                "general audience."
            )
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Warning: Could not generate summary for '{title}': {e}")
            return "Summary generation failed - please check your OpenAI API configuration."

    def add_content_to_document(self, document_id, papers):
        """
        Add paper content to the Google Doc with formatting and hyperlinks.
        Includes abstracts and AI-generated public summaries.
        
        Args:
            document_id: ID of the Google Doc to update
            papers: List of paper dictionaries from cfascience.py
        """
        try:
            # Generate timestamp
            now = datetime.now()
            timestamp = now.strftime("Generated on %A, %B %d, %Y at %I:%M%p")
            
            # Prepare the requests for batch update
            requests = []
            
            # Add title and introduction
            intro_text = f"Recent CfA-affiliated Science Publications\n"
            intro_text += f"{timestamp}\n\n"
            intro_text += f"Recent papers from CfA-affiliated authors (Top 10)\n\n"
            
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': intro_text
                }
            })
            
            # Keep track of current position in document
            current_index = len(intro_text) + 1
            
            # Add each paper with abstracts and summaries
            for i, paper in enumerate(papers, 1):
                title = paper.get('title', 'No title available')
                year = paper.get('year', 'Unknown year')
                journal = paper.get('journal', '')
                publication = paper.get('publication', '')
                pubdate = paper.get('pubdate', 'Unknown date')
                authors_affiliations = paper.get('authors_affiliations', [])
                abstract = paper.get('abstract', 'No abstract available')
                
                print(f"Processing paper {i}: {title[:50]}..." if len(title) > 50 else f"Processing paper {i}: {title}")
                
                # Create the paper entry text
                paper_text = f"{i}. {title}"
                if year:
                    paper_text += f" ({year})"
                paper_text += "\n"
                
                # Add journal/publication info
                if journal:
                    paper_text += f"   Journal: {journal}\n"
                elif publication:
                    paper_text += f"   Publication: {publication}\n"
                
                if pubdate and pubdate != 'Unknown date':
                    paper_text += f"   Publication Date: {pubdate}\n"
                
                # Add authors (simplified format for Google Docs)
                if authors_affiliations:
                    authors = [entry["author"] for entry in authors_affiliations]
                    if len(authors) > 5:
                        author_text = f"   Authors: {', '.join(authors[:3])}, et al. ({len(authors)} total authors)\n"
                    else:
                        author_text = f"   Authors: {', '.join(authors)}\n"
                    paper_text += author_text
                
                # Add NASA ADS link placeholder
                paper_text += f"   Link: [View on NASA ADS]\n\n"
                
                # Add abstract section
                paper_text += f"   ABSTRACT:\n   {abstract}\n\n"
                
                # Generate and add public summary
                print(f"   Generating public summary...")
                summary = self.generate_summary(title, abstract, year)
                paper_text += f"   PUBLIC SUMMARY:\n   {summary}\n\n"
                paper_text += "-" * 80 + "\n\n"
                
                # Insert the text
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': paper_text
                    }
                })
                
                # Update current index
                current_index += len(paper_text)
            
            # Execute all requests in batch
            result = self.service.documents().batchUpdate(
                documentId=document_id, body={'requests': requests}).execute()
            
            # Now add hyperlinks (this requires a second pass since we need the text to be inserted first)
            self._add_hyperlinks_to_document(document_id, papers)
            
            return result
            
        except HttpError as error:
            print(f'An error occurred adding content: {error}')
            return None
    
    def _add_hyperlinks_to_document(self, document_id, papers):
        """
        Add hyperlinks to NASA ADS for each paper.
        
        Args:
            document_id: ID of the Google Doc to update
            papers: List of paper dictionaries
        """
        try:
            # Get current document content to find link positions
            doc = self.service.documents().get(documentId=document_id).execute()
            content = doc.get('body').get('content')
            
            requests = []
            
            # Search for "[View on NASA ADS]" text and replace with hyperlinks
            for element in content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    if 'elements' in paragraph:
                        for elem in paragraph['elements']:
                            if 'textRun' in elem:
                                text = elem['textRun']['content']
                                if '[View on NASA ADS]' in text:
                                    start_index = elem['startIndex']
                                    # Find the position of the link text
                                    link_start = start_index + text.find('[View on NASA ADS]')
                                    link_end = link_start + len('[View on NASA ADS]')
                                    
                                    # Create a generic NASA ADS search URL (since we don't have bibcode)
                                    # This will search for the paper title
                                    paper_index = self._find_paper_index_for_position(doc, link_start)
                                    if paper_index < len(papers):
                                        title = papers[paper_index]['title'].replace(' ', '+')
                                        ads_url = f"https://ui.adsabs.harvard.edu/search/q={title}"
                                        
                                        requests.append({
                                            'updateTextStyle': {
                                                'range': {
                                                    'startIndex': link_start,
                                                    'endIndex': link_end
                                                },
                                                'textStyle': {
                                                    'link': {
                                                        'url': ads_url
                                                    }
                                                },
                                                'fields': 'link'
                                            }
                                        })
            
            if requests:
                self.service.documents().batchUpdate(
                    documentId=document_id, body={'requests': requests}).execute()
                    
        except HttpError as error:
            print(f'An error occurred adding hyperlinks: {error}')
    
    def _find_paper_index_for_position(self, doc, position):
        """
        Helper method to determine which paper a given text position belongs to.
        
        Args:
            doc: Document object from Google Docs API
            position: Character position in the document
            
        Returns:
            Index of the paper (0-based)
        """
        # This is a simplified approach - in practice you might want to be more precise
        # For now, we'll estimate based on position
        content = doc.get('body').get('content', [])
        paper_count = 0
        current_pos = 0
        
        for element in content:
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        text = elem['textRun']['content']
                        if text.strip().startswith(f"{paper_count + 1}."):
                            if current_pos <= position < current_pos + len(text):
                                return paper_count
                            paper_count += 1
                        current_pos += len(text)
        
        return min(paper_count, 9)  # Cap at 9 since we have 10 papers (0-indexed)


def main():
    """Main function to create Google Doc with CfA papers."""
    print("CfA Science Highlights - Google Docs Creator")
    print("=" * 50)
    
    # Check for credentials file
    if not os.path.exists('credentials.json'):
        print("Setup Required:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Google Docs API")
        print("4. Create credentials (OAuth 2.0 Client IDs) for Desktop application")
        print("5. Download the credentials JSON file and save it as 'credentials.json'")
        print("6. Run this script again")
        return
    
    # Initialize Google Docs creator
    docs_creator = GoogleDocsCreator()
    
    print("Authenticating with Google...")
    if not docs_creator.authenticate():
        print("Authentication failed. Please check your credentials.")
        return
    
    print("Fetching papers from NASA ADS...")
    # Fetch papers using the existing cfascience functionality
    try:
        papers = fetch_abstracts()  # This will get the default CfA papers from 2025
        if not papers:
            print("No papers found. Please check your NASA ADS API configuration.")
            return
    except Exception as e:
        print(f"Error fetching papers: {e}")
        print("Make sure your api_keys.env file is configured with ADS_API_TOKEN")
        return
    
    print(f"Found {len(papers)} papers")
    
    # Get or create the static document
    print("Getting static Google Doc...")
    doc_title = "Recent CfA-affiliated Science Publications"
    document_id = docs_creator.get_or_create_static_document(doc_title)
    
    if not document_id:
        print("Failed to get or create document")
        return
    
    # Clear existing content
    print("Clearing existing content...")
    if not docs_creator.clear_document_content(document_id):
        print("Failed to clear document content")
        return
    
    print("Adding content to document (this may take several minutes for AI summaries)...")
    print("Progress will be shown for each paper as it's processed.\n")
    result = docs_creator.add_content_to_document(document_id, papers)
    
    if result:
        doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
        # Generate timestamp for display
        now = datetime.now()
        timestamp = now.strftime("Generated on %A, %B %d, %Y at %I:%M%p")
        
        print(f"\n✅ Success! Google Doc updated with abstracts and AI summaries:")
        print(f"📄 Title: {doc_title}")
        print(f"🕒 {timestamp}")
        print(f"🔗 Static URL: {doc_url}")
        print(f"📊 Papers included: {len(papers)}")
        print("📝 Document includes: Timestamp, Paper Details, Full Abstracts, and AI Summaries")
        print(f"💾 Document ID saved to {docs_creator.config_file} - this URL will never change!")
        
        # Also print a summary of what was included
        print("\nPapers processed:")
        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'No title')[:60]
            if len(paper.get('title', '')) > 60:
                title += "..."
            year = paper.get('year', 'Unknown')
            print(f"  {i}. {title} ({year})")
    else:
        print("Failed to add content to document")


if __name__ == "__main__":
    main()