"""
CfA Science Highlights Generator

This script retrieves recent papers from Smithsonian-affiliated authors using the
NASA ADS API, allows users to select papers of interest, and generates
public-facing summaries using OpenAI. Smithsonian-affiliated authors are
highlighted in the output.
"""

# Standard library imports
import sys
import time
import threading
import itertools
import argparse
from datetime import datetime
from typing import List, Dict, Optional

# Third-party imports
import requests

# Local imports
from utils import (
    Color, setup_environment, is_cfa_affiliated, classify_authors,
    extract_authors_affiliations, generate_summary, format_author_list_for_display,
    get_search_preferences
)

# ADS API endpoint
ADS_API_URL = "https://api.adsabs.harvard.edu/v1/search/query"

def build_query(affiliation_string: Optional[str] = None, 
                start_year: Optional[int] = None, 
                end_year: Optional[int] = None,
                first_author_only: bool = False,
                refereed_only: bool = True) -> str:
    """
    Build the ADS query string with custom parameters.

    Args:
        affiliation_string: Custom affiliation string (default: CfA/Smithsonian)
        start_year: Start year for search (default: 2025)
        end_year: End year for search (default: same as start_year)
        first_author_only: If True, search only first author affiliations
        refereed_only: If True, include only refereed publications

    Returns:
        The formatted query string
    """
    if affiliation_string is None:
        if first_author_only:
            affiliation_string = 'pos(aff:"02138",1) pos(aff:"Smithsonian",1)'
        else:
            affiliation_string = 'aff:"02138" OR aff:"Smithsonian"'
    else:
        if first_author_only and not affiliation_string.startswith('pos('):
            affiliation_string = f'pos({affiliation_string},1)'

    if start_year is None:
        start_year = datetime.now().year
    if end_year is None:
        end_year = start_year

    if start_year == end_year:
        year_part = f'year:{start_year}'
    else:
        year_part = f'year:{start_year}-{end_year}'

    query_parts = [affiliation_string, year_part]
    
    if refereed_only:
        query_parts.append('property:refereed')

    return ' '.join(query_parts)


def print_authors_affiliations(authors_affiliations: List[Dict[str, str]]) -> None:
    """
    Print detailed author and affiliation information with color highlighting.

    Args:
        authors_affiliations: List of dictionaries with author names and affiliations
    """
    cfa_authors_with_aff = []
    other_authors_with_aff = []

    for entry in authors_affiliations:
        author = entry["author"]
        affiliation = entry["affiliation"]

        if is_cfa_affiliated(affiliation):
            cfa_authors_with_aff.append((author, affiliation))
        else:
            other_authors_with_aff.append((author, affiliation))

    if cfa_authors_with_aff:
        print(f"  {Color.BOLD}{Color.YELLOW}CfA Authors:{Color.END}")
        for author, affiliation in cfa_authors_with_aff:
            author_str = f"{Color.BOLD}{Color.MAGENTA}{author}{Color.END}"
            aff_str = f"{Color.GREEN}{affiliation}{Color.END}"
            print(f"    • {author_str} ({aff_str})")

    if other_authors_with_aff:
        if cfa_authors_with_aff:
            print()
        print(f"  {Color.BOLD}Other Authors:{Color.END}")
        for author, affiliation in other_authors_with_aff:
            author_str = f"{Color.CYAN}{author}{Color.END}"
            if affiliation:
                aff_str = f"{Color.GREEN}{affiliation}{Color.END}"
                print(f"    • {author_str} ({aff_str})")
            else:
                print(f"    • {author_str}")


def fetch_abstracts(ads_api_token: str,
                    affiliation_string: Optional[str] = None,
                    start_year: Optional[int] = None,
                    end_year: Optional[int] = None,
                    first_author_only: bool = False,
                    refereed_only: bool = True) -> List[Dict]:
    """
    Fetch abstracts from NASA ADS API with custom search parameters.

    Args:
        ads_api_token: NASA ADS API token for authentication
        affiliation_string: Custom affiliation string (default: CfA/Smithsonian)
        start_year: Start year for search (default: current year)
        end_year: End year for search (default: same as start_year)
        first_author_only: If True, search only first author affiliations
        refereed_only: If True, include only refereed publications

    Returns:
        List of dictionaries containing abstract data

    Raises:
        requests.RequestException: If the API request fails
    """
    headers = {"Authorization": f"Bearer {ads_api_token}"}
    query = build_query(affiliation_string, start_year, end_year, first_author_only, refereed_only)
    params = {
        "q": query,
        "fl": "title,abstract,year,author,aff,journal,pub,pubdate,bibcode,identifier",
        "sort": "date desc",
        "rows": 10
    }

    response = requests.get(
        ADS_API_URL,
        headers=headers,
        params=params,
        timeout=30
    )
    response.raise_for_status()
    
    docs = response.json().get("response", {}).get("docs", [])
    abstracts = []
    
    for doc in docs:
        title = doc.get("title", [""])[0] if doc.get("title") else ""
        abstract = doc.get("abstract", "")
        year = doc.get("year", "")
        journal = doc.get("journal", "")
        publication = doc.get("pub", "")
        pubdate = doc.get("pubdate", "")
        bibcode = doc.get("bibcode", "")
        identifiers = doc.get("identifier", [])
        authors_affiliations = extract_authors_affiliations(doc)
        
        arxiv_id = None
        if identifiers:
            for identifier in identifiers:
                if identifier.startswith("arXiv:"):
                    arxiv_id = identifier.replace("arXiv:", "")
                    break
        
        abstracts.append({
            "title": title,
            "abstract": abstract,
            "year": year,
            "journal": journal,
            "publication": publication,
            "pubdate": pubdate,
            "bibcode": bibcode,
            "arxiv_id": arxiv_id,
            "authors_affiliations": authors_affiliations
        })
    
    return abstracts


def summarize_abstracts(abstracts: List[Dict], openai_client) -> List[Dict[str, str]]:
    """
    Generate public-facing summaries for abstracts using OpenAI's GPT model.

    Displays a spinner animation while waiting for the API response.

    Args:
        abstracts: List of abstract data dictionaries
        openai_client: OpenAI client instance for generating summaries

    Returns:
        List of dictionaries containing title, year, and summary
    """
    summaries = []

    def spinner_running(stop_event: threading.Event) -> None:
        """Display a spinning animation in the terminal while processing."""
        spinner = itertools.cycle(['|', '/', '-', '\\'])
        while not stop_event.is_set():
            sys.stdout.write(f"\rGenerating summary... {next(spinner)}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " "*30 + "\r")

    for abs_data in abstracts:
        authors_affiliations = abs_data.get('authors_affiliations', [])
        cfa_authors, non_cfa_authors = classify_authors(authors_affiliations)

        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=spinner_running, args=(stop_event,))
        spinner_thread.start()

        try:
            summary = generate_summary(
                client=openai_client,
                title=abs_data['title'],
                abstract=abs_data['abstract'],
                year=abs_data['year'],
                cfa_authors=cfa_authors,
                non_cfa_authors=non_cfa_authors
            )
        finally:
            stop_event.set()
            spinner_thread.join()
            
        summaries.append({
            "title": abs_data["title"],
            "year": abs_data["year"],
            "summary": summary
        })
        
    return summaries



def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate public-facing summaries of CfA research papers from NASA ADS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Default: CfA papers from 2025
  %(prog)s --start-year 2024                 # CfA papers from 2024
  %(prog)s --start-year 2023 --end-year 2024 # CfA papers from 2023-2024
  %(prog)s --affiliation 'aff:"MIT"'          # MIT papers from 2025
  %(prog)s --affiliation 'aff:"MIT"' --start-year 2024 --end-year 2025
        """
    )

    parser.add_argument(
        '--start-year',
        type=int,
        help='Start year for search (default: 2025)'
    )

    parser.add_argument(
        '--end-year',
        type=int,
        help='End year for search (default: same as start year)'
    )

    parser.add_argument(
        '--affiliation',
        type=str,
        help='Custom affiliation string in ADS query format (default: CfA/Smithsonian affiliations)'
    )

    return parser.parse_args()


def main() -> None:
    # Initialize environment and API clients
    ads_api_token, openai_client = setup_environment()

    args = parse_arguments()

    # Get user preferences for search type
    first_author_only, refereed_only = get_search_preferences()

    # Pass the command line arguments and user preferences to fetch_abstracts
    abstracts = fetch_abstracts(
        ads_api_token=ads_api_token,
        affiliation_string=args.affiliation,
        start_year=args.start_year,
        end_year=args.end_year,
        first_author_only=first_author_only,
        refereed_only=refereed_only
    )

    if not abstracts:
        print("No abstracts found.")
        return

    current_year = datetime.now().year
    start_year = args.start_year or current_year
    if args.end_year and args.end_year != start_year:
        year_display = f"{start_year}-{args.end_year}"
    else:
        year_display = str(start_year)
    affiliation_display = "CfA-affiliated" if not args.affiliation else "custom affiliation"

    print(
        f"Most recent 10 papers from {affiliation_display} authors ({year_display}):")
    for idx, abs_data in enumerate(abstracts, 1):
        title = abs_data.get('title', '(no title)')
        print(f"{idx}. {Color.BOLD}{Color.CYAN}{title}{Color.END}")

        author_lines = format_author_list_for_display(
            abs_data.get('authors_affiliations', []))
        for line in author_lines:
            print(line)

        print()

    selection = input(
        "\nEnter the numbers of the abstracts to summarize (comma-separated, e.g. 1,3,5) or 'n' to exit: ")

    if selection.lower().strip() == 'n':
        print("Exiting without generating summaries.")
        return

    try:
        selected_indices = [
            int(part) - 1 for part in (x.strip() for x in selection.split(',')) if part.isdigit()
        ]
    except ValueError:
        print("Invalid input. Exiting.")
        return
    selected_indices = [i for i in selected_indices if 0 <= i < len(abstracts)]
    if not selected_indices:
        print("No valid selections made. Exiting.")
        return

    selected_abstracts = [abstracts[i] for i in selected_indices]
    summaries = summarize_abstracts(selected_abstracts, openai_client)
    for i, s in enumerate(summaries):
        abs_data = selected_abstracts[i]
        print(
            f"\n{Color.BOLD}{Color.CYAN}Title: {s['title']}{Color.END} {Color.GREEN}(Year: {s['year']}){Color.END}")
        journal = abs_data.get('journal')
        publication = abs_data.get('publication')
        if journal and publication and journal != publication:
            print(
                f"{Color.YELLOW}Journal:{Color.END} {journal}\n{Color.YELLOW}Publication:{Color.END} {publication}")
        elif journal:
            print(f"{Color.YELLOW}Journal:{Color.END} {journal}")
        elif publication:
            print(f"{Color.YELLOW}Publication:{Color.END} {publication}")
        else:
            print(f"{Color.YELLOW}Journal/Publication:{Color.END} (none)")
        pubdate = abs_data.get('pubdate', '(unknown)')
        print(f"{Color.YELLOW}Publication Date:{Color.END} {pubdate}")
        authors_affiliations = abs_data.get("authors_affiliations", [])
        print(f"{Color.YELLOW}Authors & Affiliations:{Color.END}")
        print_authors_affiliations(authors_affiliations)
        print()
        print(f"{Color.BOLD}{Color.PURPLE}ChatGPT summary of abstract, rewritten for a public audience:{Color.END}")
        print(s['summary'])
        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
