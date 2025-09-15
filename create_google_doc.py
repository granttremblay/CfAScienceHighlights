"""
Google Docs API Integration for CfA Science Highlights

This script creates a Google Doc containing the list of papers from NASA ADS
with hyperlinks to the original papers. It integrates with the existing
cfascience.py script to fetch the paper data.
"""

import os
import sys
from typing import List, Dict, Optional, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# Import our functionality
try:
    from cfascience import fetch_abstracts
    from utils import setup_environment, classify_authors, generate_summary
    from google_docs_formatter import (
        create_document_header, create_paper_content_requests,
        create_abstract_section_requests, create_summary_section_requests,
        create_separator_requests, create_justification_request
    )
except ImportError as e:
    print(f"Error: Could not import required dependencies: {e}")
    print("Make sure all required files are in the same directory.")
    sys.exit(1)

# Initialize environment and OpenAI client
_, openai_client = setup_environment()

# Google API scopes
SCOPES = ['https://www.googleapis.com/auth/documents']

class GoogleDocsCreator:
    """Handles Google Docs API operations for creating science highlights documents."""
    
    def __init__(self, credentials_file: str = 'credentials.json', 
                 token_file: str = 'token.json', 
                 config_file: str = 'google_doc_config.txt'):
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
    
    
    def generate_paper_summary(self, paper: Dict[str, Any]) -> str:
        """
        Generate a public-facing summary for a paper using OpenAI.
        
        Args:
            paper: Paper dictionary containing title, abstract, year, and authors_affiliations
            
        Returns:
            Generated summary string
        """
        try:
            # Classify authors for context
            authors_affiliations = paper.get('authors_affiliations', [])
            cfa_authors, non_cfa_authors = classify_authors(authors_affiliations)
            
            return generate_summary(
                client=openai_client,
                title=paper.get('title', ''),
                abstract=paper.get('abstract', ''),
                year=paper.get('year', ''),
                cfa_authors=cfa_authors,
                non_cfa_authors=non_cfa_authors
            )
        except Exception as e:
            print(f"Warning: Could not generate summary for '{paper.get('title', 'Unknown')}': {e}")
            return "Summary generation failed - please check your OpenAI API configuration."

    def add_content_to_document(self, document_id: str, papers: List[Dict[str, Any]]) -> Optional[Dict]:
        """
        Add paper content to the Google Doc with professional formatting and styling.
        Includes abstracts and AI-generated public summaries with enhanced readability.
        
        Args:
            document_id: ID of the Google Doc to update
            papers: List of paper dictionaries from cfascience.py
            
        Returns:
            Result from Google Docs API or None if error occurred
        """
        try:
            requests = []
            link_requests = []
            current_index = 1
            
            # Create document header
            header_requests, current_index = create_document_header(current_index)
            requests.extend(header_requests)
            
            # Add each paper
            for i, paper in enumerate(papers, 1):
                title = paper.get('title', 'No title available')
                print(f"Processing paper {i}: {title[:50]}..." if len(title) > 50 else f"Processing paper {i}: {title}")
                
                # Paper content (title, details)
                paper_requests, current_index, link_info = create_paper_content_requests(paper, i, current_index)
                requests.extend(paper_requests)
                
                # Store link info for later application
                if link_info:
                    link_requests.append({
                        'updateTextStyle': {
                            'range': {
                                'startIndex': link_info['start_index'],
                                'endIndex': link_info['end_index']
                            },
                            'textStyle': {
                                'link': {'url': link_info['url']}
                            },
                            'fields': 'link'
                        }
                    })
                
                # Abstract section
                abstract = paper.get('abstract', 'No abstract available')
                abstract_requests, current_index = create_abstract_section_requests(abstract, current_index)
                requests.extend(abstract_requests)
                
                # Generate and add public summary
                print(f"   Generating public summary...")
                summary = self.generate_paper_summary(paper)
                summary_requests, current_index = create_summary_section_requests(summary, current_index)
                requests.extend(summary_requests)
                
                # Add separator
                separator_requests, current_index = create_separator_requests(current_index)
                requests.extend(separator_requests)
            
            # Apply justified alignment to the entire document
            requests.append(create_justification_request(current_index))
            
            # Execute all content requests in batch
            result = self.service.documents().batchUpdate(
                documentId=document_id, body={'requests': requests}).execute()
            
            # Apply hyperlinks in a separate batch (after content is created)
            if link_requests:
                print("Applying hyperlinks...")
                self.service.documents().batchUpdate(
                    documentId=document_id, body={'requests': link_requests}).execute()
            
            print("Document formatting applied successfully!")
            return result
            
        except HttpError as error:
            print(f'An error occurred adding content: {error}')
            return None
    


def main() -> None:
    """Main function to create Google Doc with CfA papers."""
    print("CfA Science Highlights - Google Docs Creator")
    print("=" * 50)
    
    # Check for credentials file
    if not os.path.exists('credentials.json'):
        _print_setup_instructions()
        return
    
    # Initialize Google Docs creator
    docs_creator = GoogleDocsCreator()
    
    print("Authenticating with Google...")
    if not docs_creator.authenticate():
        print("Authentication failed. Please check your credentials.")
        return
    
    # Fetch papers
    papers = _fetch_papers()
    if not papers:
        return
    
    # Process document
    document_id = _process_document(docs_creator, papers)
    if document_id:
        _print_success_summary(docs_creator, document_id, papers)
    else:
        print("Failed to process document")


def _print_setup_instructions() -> None:
    """Print setup instructions for Google Cloud Console."""
    print("Setup Required:")
    print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Google Docs API")
    print("4. Create credentials (OAuth 2.0 Client IDs) for Desktop application")
    print("5. Download the credentials JSON file and save it as 'credentials.json'")
    print("6. Run this script again")


def _fetch_papers() -> Optional[List[Dict[str, Any]]]:
    """Fetch papers from NASA ADS."""
    print("Fetching papers from NASA ADS...")
    try:
        papers = fetch_abstracts()  # Default CfA papers from 2025
        if not papers:
            print("No papers found. Please check your NASA ADS API configuration.")
            return None
        print(f"Found {len(papers)} papers")
        return papers
    except Exception as e:
        print(f"Error fetching papers: {e}")
        print("Make sure your api_keys.env file is configured with ADS_API_TOKEN")
        return None


def _process_document(docs_creator: GoogleDocsCreator, papers: List[Dict[str, Any]]) -> Optional[str]:
    """Process the Google Doc with paper content."""
    # Get or create the static document
    print("Getting static Google Doc...")
    doc_title = "Recent CfA-affiliated Science Publications"
    document_id = docs_creator.get_or_create_static_document(doc_title)
    
    if not document_id:
        print("Failed to get or create document")
        return None
    
    # Clear existing content
    print("Clearing existing content...")
    if not docs_creator.clear_document_content(document_id):
        print("Failed to clear document content")
        return None
    
    # Add content
    print("Adding content to document (this may take several minutes for AI summaries)...")
    print("Progress will be shown for each paper as it's processed.\n")
    result = docs_creator.add_content_to_document(document_id, papers)
    
    return document_id if result else None


def _print_success_summary(docs_creator: GoogleDocsCreator, document_id: str, papers: List[Dict[str, Any]]) -> None:
    """Print success summary with document details."""
    doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
    doc_title = "Recent CfA-affiliated Science Publications"
    
    # Generate timestamp for display
    now = datetime.now()
    timestamp = now.strftime("Generated on %A, %B %d, %Y at %I:%M%p")
    
    print(f"\n✅ Success! Google Doc updated with abstracts and AI summaries:")
    print(f"📄 Title: {doc_title}")
    print(f"🕒 {timestamp}")
    print(f"🔗 Static URL: {doc_url}")
    print(f"📊 Papers included: {len(papers)}")
    print("📝 Document includes: Professional Formatting, Timestamps, Paper Details, Styled Abstracts, and Enhanced AI Summaries")
    print(f"💾 Document ID saved to {docs_creator.config_file} - this URL will never change!")
    
    # Print summary of processed papers
    print("\nPapers processed:")
    for i, paper in enumerate(papers, 1):
        title = paper.get('title', 'No title')[:60]
        if len(paper.get('title', '')) > 60:
            title += "..."
        year = paper.get('year', 'Unknown')
        print(f"  {i}. {title} ({year})")


if __name__ == "__main__":
    main()