"""
Shared utilities for CfA Science Highlights project.

This module contains common functionality used across multiple scripts,
including author classification, OpenAI client setup, and formatting utilities.
"""

import os
from typing import List, Dict, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv


class Color:
    """ANSI color codes for terminal text formatting."""
    # Core colors used in the application
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'  # For CfA authors
    PURPLE = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'


def setup_environment() -> tuple[str, OpenAI]:
    """
    Load environment variables and initialize OpenAI client.
    
    Returns:
        tuple: (ADS_API_TOKEN, OpenAI client instance)
        
    Raises:
        ValueError: If required API keys are missing
    """
    load_dotenv('api_keys.env')
    
    ads_token = os.getenv("ADS_API_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not ads_token:
        raise ValueError("ADS_API_TOKEN not found in environment variables")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    client = OpenAI(api_key=openai_key)
    return ads_token, client


def is_cfa_affiliated(affiliation: Optional[str]) -> bool:
    """
    Check if an affiliation is Smithsonian-affiliated.

    Args:
        affiliation: Author affiliation string (can be None or empty)

    Returns:
        Boolean indicating if the affiliation is Smithsonian-affiliated
    """
    if not affiliation:
        return False
    
    smithsonian_keywords = ['smithsonian', 'cfa', 'center for astrophysics']
    return any(keyword in affiliation.lower() for keyword in smithsonian_keywords)


def classify_authors(authors_affiliations: List[Dict[str, str]]) -> tuple[List[str], List[str]]:
    """
    Classify authors into CfA-affiliated and non-CfA groups.
    
    Args:
        authors_affiliations: List of dictionaries with 'author' and 'affiliation' keys
        
    Returns:
        tuple: (cfa_authors, non_cfa_authors) - both as lists of author names
    """
    cfa_authors = []
    non_cfa_authors = []
    
    for entry in authors_affiliations:
        author = entry["author"]
        affiliation = entry["affiliation"]
        
        if is_cfa_affiliated(affiliation):
            cfa_authors.append(author)
        else:
            non_cfa_authors.append(author)
    
    return cfa_authors, non_cfa_authors


def extract_authors_affiliations(doc: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract author and affiliation pairs from an ADS API document.

    Args:
        doc: Document dictionary from ADS API

    Returns:
        List of dictionaries with 'author' and 'affiliation' keys
    """
    authors = doc.get("author", [])
    affiliations = doc.get("aff", [])
    
    author_aff_pairs = []
    for i, author in enumerate(authors):
        affiliation = affiliations[i] if i < len(affiliations) else ""
        author_aff_pairs.append({"author": author, "affiliation": affiliation})
    
    return author_aff_pairs


def build_author_context_for_summary(cfa_authors: List[str], non_cfa_authors: List[str]) -> str:
    """
    Build author context string for OpenAI prompts.
    
    Args:
        cfa_authors: List of CfA-affiliated author names
        non_cfa_authors: List of non-CfA author names
        
    Returns:
        Formatted author context string for use in prompts
    """
    author_context = ""
    
    if cfa_authors:
        if len(cfa_authors) == 1:
            author_context += f"CfA Author: {cfa_authors[0]}\n"
        else:
            author_context += f"CfA Authors: {', '.join(cfa_authors)}\n"
    
    if non_cfa_authors:
        if len(non_cfa_authors) <= 3:
            author_context += f"Other Authors: {', '.join(non_cfa_authors)}\n"
        else:
            author_context += f"Other Authors: {', '.join(non_cfa_authors[:3])}, and {len(non_cfa_authors) - 3} others\n"
    
    return author_context


def generate_summary(client: OpenAI, title: str, abstract: str, year: str, 
                    cfa_authors: Optional[List[str]] = None, 
                    non_cfa_authors: Optional[List[str]] = None) -> str:
    """
    Generate a public-facing summary using OpenAI GPT.
    
    Args:
        client: OpenAI client instance
        title: Paper title
        abstract: Paper abstract
        year: Publication year
        cfa_authors: List of CfA-affiliated authors (optional)
        non_cfa_authors: List of other authors (optional)
        
    Returns:
        Generated summary string
        
    Raises:
        Exception: If OpenAI API call fails
    """
    # Build author context if authors are provided
    author_context = ""
    if cfa_authors is not None and non_cfa_authors is not None:
        author_context = build_author_context_for_summary(cfa_authors, non_cfa_authors)
    
    prompt_parts = [
        f"Title: {title} (Year: {year})",
        f"Abstract: {abstract}"
    ]
    
    if author_context:
        prompt_parts.append(author_context)
    
    # Build the instruction part
    instruction = "Write a public-facing summary in two paragraphs for a general audience."
    if cfa_authors:
        instruction += (" If there are CfA authors listed, specifically highlight their contribution "
                       "by mentioning them by name in the summary (e.g., 'A team including CfA astronomers "
                       "Jane Doe and John Smith have discovered...' or 'CfA researcher Dr. Jane Doe led a study that...'). ")
    instruction += " Make the summary accessible and engaging for the public."
    
    prompt_parts.append(instruction)
    prompt = "\n\n".join(prompt_parts)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()


def get_search_preferences() -> tuple[bool, bool]:
    """
    Prompt user for search preferences.
    
    Returns:
        Tuple of (first_author_only, refereed_only)
    """
    print(f"\n{Color.BOLD}{Color.CYAN}Search Configuration{Color.END}")
    print("=" * 50)
    
    # First author vs any author
    print(f"\n{Color.YELLOW}Author Position Preference:{Color.END}")
    print("1. FIRST author papers only (papers where the affiliation appears as first author)")
    print("2. ANY author papers (papers with any author from the affiliation)")
    
    while True:
        author_choice = input(f"\n{Color.BOLD}Choose option (1 or 2): {Color.END}").strip().lower()
        if author_choice in ["1", "first", "f"]:
            first_author_only = True
            print(f"{Color.GREEN}✓ Searching for FIRST author papers only{Color.END}")
            break
        elif author_choice in ["2", "any", "a"]:
            first_author_only = False
            print(f"{Color.GREEN}✓ Searching for ANY author papers{Color.END}")
            break
        else:
            print(f"{Color.RED}Invalid choice '{author_choice}'. Please enter 1 or 2.{Color.END}")
    
    # Refereed vs all papers
    print(f"\n{Color.YELLOW}Publication Type:{Color.END}")
    print("1. Refereed papers only (peer-reviewed)")
    print("2. All papers (including preprints, conference proceedings, etc.)")
    
    while True:
        ref_choice = input(f"\n{Color.BOLD}Choose option (1 or 2): {Color.END}").strip().lower()
        if ref_choice in ["1", "refereed", "ref", "r"]:
            refereed_only = True
            print(f"{Color.GREEN}✓ Searching for refereed papers only{Color.END}")
            break
        elif ref_choice in ["2", "all", "any", "a"]:
            refereed_only = False
            print(f"{Color.GREEN}✓ Searching for all papers (including non-refereed){Color.END}")
            break
        else:
            print(f"{Color.RED}Invalid choice '{ref_choice}'. Please enter 1 or 2.{Color.END}")
    
    print()  # Add spacing
    return first_author_only, refereed_only


def format_author_list_for_display(authors_affiliations: List[Dict[str, str]]) -> List[str]:
    """
    Format author list for terminal display, highlighting CfA authors.

    Args:
        authors_affiliations: List of dictionaries with author names and affiliations

    Returns:
        List of formatted strings ready for display
    """
    cfa_authors, non_cfa_authors = classify_authors(authors_affiliations)
    
    formatted_lines = []
    
    if cfa_authors:
        cfa_author_str = f"{Color.BOLD}{Color.MAGENTA}{', '.join(cfa_authors)}{Color.END}"
        formatted_lines.append(
            f"   {Color.BOLD}{Color.YELLOW}CfA Authors:{Color.END} {cfa_author_str}"
        )
    
    if non_cfa_authors:
        other_author_str = f"{Color.CYAN}{', '.join(non_cfa_authors)}{Color.END}"
        formatted_lines.append(
            f"   {Color.YELLOW}Other Authors:{Color.END} {other_author_str}"
        )
    
    return formatted_lines