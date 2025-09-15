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
from typing import List, Dict, Optional

# Third-party imports
import requests

# Local imports
from utils import (
    Color, setup_environment, is_cfa_affiliated, classify_authors,
    extract_authors_affiliations, generate_summary, format_author_list_for_display
)


# Initialize environment and API clients
ADS_API_TOKEN, client = setup_environment()

# ADS API endpoint and headers
ADS_API_URL = "https://api.adsabs.harvard.edu/v1/search/query"
ADS_HEADERS = {
    "Authorization": f"Bearer {ADS_API_TOKEN}"
}

# Default query parameters - now handled dynamically in build_query()


def build_query(affiliation_string: Optional[str] = None, 
                start_year: Optional[int] = None, 
                end_year: Optional[int] = None) -> str:
    """
    Build the ADS query string with custom parameters.

    Args:
        affiliation_string: Custom affiliation string (default: CfA/Smithsonian)
        start_year: Start year for search (default: 2025)
        end_year: End year for search (default: same as start_year)

    Returns:
        The formatted query string
    """
    # Default affiliation string for CfA/Smithsonian
    if affiliation_string is None:
        affiliation_string = 'pos(aff:"02138",1) pos(aff:"Smithsonian",1)'

    # Default year range
    if start_year is None:
        start_year = 2025
    if end_year is None:
        end_year = start_year

    # Build year part of query
    if start_year == end_year:
        year_part = f'year:{start_year}'
    else:
        year_part = f'year:{start_year}-{end_year}'

    return f'{affiliation_string} {year_part} property:refereed'






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

    # Print CfA authors first, highlighted
    if cfa_authors_with_aff:
        print(f"  {Color.BOLD}{Color.YELLOW}CfA Authors:{Color.END}")
        for author, affiliation in cfa_authors_with_aff:
            author_str = f"{Color.BOLD}{Color.MAGENTA}{author}{Color.END}"
            aff_str = f"{Color.GREEN}{affiliation}{Color.END}"
            print(f"    • {author_str} ({aff_str})")

    # Print other authors
    if other_authors_with_aff:
        if cfa_authors_with_aff:  # Add separator if we have both types
            print()
        print(f"  {Color.BOLD}Other Authors:{Color.END}")
        for author, affiliation in other_authors_with_aff:
            author_str = f"{Color.CYAN}{author}{Color.END}"
            if affiliation:
                aff_str = f"{Color.GREEN}{affiliation}{Color.END}"
                print(f"    • {author_str} ({aff_str})")
            else:
                print(f"    • {author_str}")


def fetch_abstracts(affiliation_string: Optional[str] = None, 
                    start_year: Optional[int] = None, 
                    end_year: Optional[int] = None) -> List[Dict]:
    """
    Fetch abstracts from NASA ADS API with custom search parameters.

    Args:
        affiliation_string: Custom affiliation string (default: CfA/Smithsonian)
        start_year: Start year for search (default: 2025)
        end_year: End year for search (default: same as start_year)

    Returns:
        List of dictionaries containing abstract data
        
    Raises:
        requests.RequestException: If the API request fails
    """
    query = build_query(affiliation_string, start_year, end_year)
    params = {
        "q": query,
        "fl": "title,abstract,year,author,aff,journal,pub,pubdate,bibcode",
        "sort": "date desc",
        "rows": 10
    }

    response = requests.get(
        ADS_API_URL,
        headers=ADS_HEADERS,
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
        authors_affiliations = extract_authors_affiliations(doc)
        
        abstracts.append({
            "title": title,
            "abstract": abstract,
            "year": year,
            "journal": journal,
            "publication": publication,
            "pubdate": pubdate,
            "bibcode": bibcode,
            "authors_affiliations": authors_affiliations
        })
    
    return abstracts




def summarize_abstracts(abstracts: List[Dict]) -> List[Dict[str, str]]:
    """
    Generate public-facing summaries for abstracts using OpenAI's GPT model.

    Displays a spinner animation while waiting for the API response.

    Args:
        abstracts: List of abstract data dictionaries

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
        sys.stdout.write("\r" + " "*30 + "\r")  # Clear line

    for abs_data in abstracts:
        # Classify authors
        authors_affiliations = abs_data.get('authors_affiliations', [])
        cfa_authors, non_cfa_authors = classify_authors(authors_affiliations)
        
        # Generate summary with spinner
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=spinner_running, args=(stop_event,))
        spinner_thread.start()
        
        try:
            summary = generate_summary(
                client=client,
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
    args = parse_arguments()

    # Pass the command line arguments to fetch_abstracts
    abstracts = fetch_abstracts(
        affiliation_string=args.affiliation,
        start_year=args.start_year,
        end_year=args.end_year
    )

    if not abstracts:
        print("No abstracts found.")
        return

    # Show what search parameters were used
    year_display = f"{args.start_year or 2025}" + \
        (f"-{args.end_year}" if args.end_year and args.end_year !=
         (args.start_year or 2025) else "")
    affiliation_display = "CfA-affiliated" if not args.affiliation else "custom affiliation"

    # Print a numbered list of the most recent 10 papers with title and author list
    print(
        f"Most recent 10 papers from {affiliation_display} authors ({year_display}):")
    for idx, abs_data in enumerate(abstracts, 1):
        title = abs_data.get('title', '(no title)')
        print(f"{idx}. {Color.BOLD}{Color.CYAN}{title}{Color.END}")

        # Format and print authors with CfA authors highlighted
        author_lines = format_author_list_for_display(
            abs_data.get('authors_affiliations', []))
        for line in author_lines:
            print(line)

        print()  # Add an empty line between papers

    # Ask user which abstracts to summarize
    selection = input(
        "\nEnter the numbers of the abstracts to summarize (comma-separated, e.g. 1,3,5) or 'n' to exit: ")

    # Check if user wants to exit
    if selection.lower().strip() == 'n':
        print("Exiting without generating summaries.")
        return

    try:
        selected_indices = [
            int(x.strip())-1 for x in selection.split(',') if x.strip().isdigit()]
    except Exception:
        print("Invalid input. Exiting.")
        return
    selected_indices = [i for i in selected_indices if 0 <= i < len(abstracts)]
    if not selected_indices:
        print("No valid selections made. Exiting.")
        return

    selected_abstracts = [abstracts[i] for i in selected_indices]
    summaries = summarize_abstracts(selected_abstracts)
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
