"""
CfA Science Highlights Generator

This script retrieves recent papers from Smithsonian-affiliated authors using the
NASA ADS API, allows users to select papers of interest, and generates
public-facing summaries using OpenAI. Smithsonian-affiliated authors are
highlighted in the output.
"""

# Standard library imports
import os
import sys
import time
import threading
import itertools
import argparse

# Third-party imports
import requests
from openai import OpenAI
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv('api_keys.env')

# Set NASA ADS API token and OpenAI API key from environment variables
ADS_API_TOKEN = os.getenv("ADS_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


# ANSI color codes for terminal output
class Color:
    """ANSI color codes for terminal text formatting."""
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'  # Magenta for CfA authors
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# ADS API endpoint and headers
ADS_API_URL = "https://api.adsabs.harvard.edu/v1/search/query"
ADS_HEADERS = {
    "Authorization": f"Bearer {ADS_API_TOKEN}"
}

# Default query parameters - now handled dynamically in build_query()


def build_query(affiliation_string=None, start_year=None, end_year=None):
    """
    Build the ADS query string with custom parameters.

    Args:
        affiliation_string: Custom affiliation string (default: CfA/Smithsonian)
        start_year: Start year for search (default: 2025)
        end_year: End year for search (default: same as start_year)

    Returns:
        str: The formatted query string
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


def extract_authors_affiliations(doc):
    """
    Extract author and affiliation pairs from a document.

    Args:
        doc: Document dictionary from ADS API

    Returns:
        List of dictionaries with author names and affiliations
    """
    authors = doc.get("author", [])
    affiliations = doc.get("aff", [])
    # Pair authors with affiliations if possible
    author_aff_pairs = []
    for i, author in enumerate(authors):
        aff = affiliations[i] if i < len(affiliations) else ""
        author_aff_pairs.append({"author": author, "affiliation": aff})
    return author_aff_pairs


def format_author_list(authors_affiliations):
    """
    Format author list for initial display, highlighting CfA authors.

    Args:
        authors_affiliations: List of dictionaries with author names and
                             affiliations

    Returns:
        List of formatted strings ready for display
    """
    cfa_authors = []
    other_authors = []

    for entry in authors_affiliations:
        author = entry["author"]
        aff = entry["affiliation"]

        # Check if this is a Smithsonian-affiliated author
        if is_cfa_affiliated(aff):
            cfa_authors.append(author)
        else:
            other_authors.append(author)

    formatted_lines = []
    if cfa_authors:
        cfa_author_str = f"{Color.BOLD}{Color.MAGENTA}{', '.join(cfa_authors)}{Color.END}"
        formatted_lines.append(
            f"   {Color.BOLD}{Color.YELLOW}CfA Authors:{Color.END} {cfa_author_str}")

    if other_authors:
        other_author_str = f"{Color.CYAN}{', '.join(other_authors)}{Color.END}"
        formatted_lines.append(
            f"   {Color.YELLOW}Other Authors:{Color.END} {other_author_str}")

    return formatted_lines


def print_authors_affiliations(authors_affiliations):
    """
    Print detailed author and affiliation information with color highlighting.

    Args:
        authors_affiliations: List of dictionaries with author names and
                             affiliations
    """
    # Process all authors first to make a cleaner output
    smithsonian_authors = []
    other_authors = []

    for entry in authors_affiliations:
        author = entry["author"]
        aff = entry["affiliation"]

        # Check if this is a Smithsonian-affiliated author
        if is_cfa_affiliated(aff):
            smithsonian_authors.append((author, aff))
        else:
            other_authors.append((author, aff))

    # Print Smithsonian authors first, highlighted
    if smithsonian_authors:
        print(f"  {Color.BOLD}{Color.YELLOW}CfA Authors:{Color.END}")
        for author, aff in smithsonian_authors:
            author_str = f"{Color.BOLD}{Color.MAGENTA}{author}{Color.END}"
            aff_str = f"{Color.GREEN}{aff}{Color.END}"
            print(f"    • {author_str} ({aff_str})")

    # Print other authors
    if other_authors:
        if smithsonian_authors:  # Add separator if we have both types
            print()
        print(f"  {Color.BOLD}Other Authors:{Color.END}")
        for author, aff in other_authors:
            author_str = f"{Color.CYAN}{author}{Color.END}"
            if aff:
                aff_str = f"{Color.GREEN}{aff}{Color.END}"
                print(f"    • {author_str} ({aff_str})")
            else:
                print(f"    • {author_str}")


def fetch_abstracts(affiliation_string=None, start_year=None, end_year=None):
    """
    Fetch abstracts from NASA ADS API with custom search parameters.

    Args:
        affiliation_string: Custom affiliation string (default: CfA/Smithsonian)
        start_year: Start year for search (default: 2025)
        end_year: End year for search (default: same as start_year)

    Returns:
        List of dictionaries containing abstract data
    """
    query = build_query(affiliation_string, start_year, end_year)
    params = {
        "q": query,
        "fl": "title,abstract,year,author,aff,journal,pub,pubdate",
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
        title = doc.get("title", [""])[0]
        abstract = doc.get("abstract", "")
        year = doc.get("year", "")
        journal = doc.get("journal", "")
        publication = doc.get("pub", "")
        pubdate = doc.get("pubdate", "")
        authors_affiliations = extract_authors_affiliations(doc)
        abstracts.append({
            "title": title,
            "abstract": abstract,
            "year": year,
            "journal": journal,
            "publication": publication,
            "pubdate": pubdate,
            "authors_affiliations": authors_affiliations
        })
    return abstracts


def is_cfa_affiliated(affiliation):
    """
    Check if an affiliation is Smithsonian-affiliated.

    Args:
        affiliation: Author affiliation string

    Returns:
        Boolean indicating if the affiliation is Smithsonian-affiliated
    """
    smithsonian_keywords = ['smithsonian', 'cfa', 'center for astrophysics']
    has_keywords = affiliation and any(
        s in affiliation.lower() for s in smithsonian_keywords
    )
    return has_keywords


def summarize_abstracts(abstracts):
    """
    Generate public-facing summaries for abstracts using OpenAI's GPT model.

    Displays a spinner animation while waiting for the API response.

    Args:
        abstracts: List of abstract data dictionaries

    Returns:
        List of dictionaries containing title, year, and summary
    """
    summaries = []

    def spinner_running(stop_event):
        """Display a spinning animation in the terminal while processing."""
        spinner = itertools.cycle(['|', '/', '-', '\\'])
        while not stop_event.is_set():
            sys.stdout.write(f"\rGenerating summary... {next(spinner)}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " "*30 + "\r")  # Clear line

    for abs_data in abstracts:
        prompt = (
            f"Title: {abs_data['title']} (Year: {abs_data['year']})\n"
            f"Abstract: {abs_data['abstract']}\n\n"
            "Write a public-facing summary in two paragraphs for a "
            "general audience."
        )
        stop_event = threading.Event()
        spinner_thread = threading.Thread(
            target=spinner_running, args=(stop_event,))
        spinner_thread.start()
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
        finally:
            stop_event.set()
            spinner_thread.join()
        summary = response.choices[0].message.content.strip()
        summaries.append({
            "title": abs_data["title"],
            "year": abs_data["year"],
            "summary": summary
        })
    return summaries


def main():
    """
    Main function to run the CfA Science Highlights program.

    Fetches abstracts, displays them with author information,
    and allows user to select which abstracts to summarize.
    """
    abstracts = fetch_abstracts()
    if not abstracts:
        print("No abstracts found.")
        return

    # Print papers with title and author list
    print("Most recent 10 papers from CfA-affiliated authors:")
    for idx, abs_data in enumerate(abstracts, 1):
        title = abs_data.get('title', '(no title)')

        # Check if first author is Smithsonian-affiliated
        authors_affiliations = abs_data.get('authors_affiliations', [])
        first_author_badge = ""
        if authors_affiliations and len(authors_affiliations) > 0:
            first_author = authors_affiliations[0]
            if is_cfa_affiliated(first_author.get("affiliation", "")):
                first_author_badge = (
                    f" {Color.BOLD}[{Color.MAGENTA}CfA 1st Author"
                    f"{Color.END}{Color.BOLD}]{Color.END}"
                )

        # Print title with optional first author badge
        title_display = f"{idx}. {Color.BOLD}{Color.CYAN}{title}{Color.END}"
        print(f"{title_display}{first_author_badge}")

        # Format and print authors with CfA authors highlighted
        author_lines = format_author_list(
            abs_data.get('authors_affiliations', []))
        for line in author_lines:
            print(line)

        print()  # Add an empty line between papers

    # Ask user which abstracts to summarize
    selection_prompt = "\nEnter the numbers of the abstracts to summarize "
    selection_prompt += "(comma-separated, e.g. 1,3,5) or 'n' to exit: "
    selection = input(selection_prompt)

    # Check if user wants to exit
    if selection.lower().strip() == 'n':
        print("Exiting without generating summaries.")
        return

    try:
        # Process user selection into a list of indices
        selected_indices = [
            int(x.strip())-1 for x in selection.split(',')
            if x.strip().isdigit()
        ]
    except ValueError:
        print("Invalid input. Exiting.")
        return

    # Validate indices are in range
    selected_indices = [i for i in selected_indices if 0 <= i < len(abstracts)]
    if not selected_indices:
        print("No valid selections made. Exiting.")
        return

    # Generate summaries for selected abstracts
    selected_abstracts = [abstracts[i] for i in selected_indices]
    summaries = summarize_abstracts(selected_abstracts)

    # Display results
    for i, s in enumerate(summaries):
        abs_data = selected_abstracts[i]
        # Title and year
        title_year = (
            f"\n{Color.BOLD}{Color.CYAN}Title: {s['title']}{Color.END} "
            f"{Color.GREEN}(Year: {s['year']}){Color.END}"
        )
        print(title_year)

        # Journal and publication info
        journal = abs_data.get('journal')
        publication = abs_data.get('publication')
        if journal and publication and journal != publication:
            journal_pub = (
                f"{Color.YELLOW}Journal:{Color.END} {journal}\n"
                f"{Color.YELLOW}Publication:{Color.END} {publication}"
            )
            print(journal_pub)
        elif journal:
            print(f"{Color.YELLOW}Journal:{Color.END} {journal}")
        elif publication:
            print(f"{Color.YELLOW}Publication:{Color.END} {publication}")
        else:
            print(f"{Color.YELLOW}Journal/Publication:{Color.END} (none)")

        # Publication date
        pubdate = abs_data.get('pubdate', '(unknown)')
        print(f"{Color.YELLOW}Publication Date:{Color.END} {pubdate}")

        # Authors and affiliations
        print(f"{Color.YELLOW}Authors & Affiliations:{Color.END}")
        print_authors_affiliations(abs_data.get("authors_affiliations", []))
        print()

        # AI-generated summary
        summary_header = (
            f"{Color.BOLD}{Color.PURPLE}ChatGPT summary of abstract, "
            f"rewritten for a public audience:{Color.END}"
        )
        print(summary_header)
        print(s['summary'])
        print("\n" + "="*80 + "\n")


def summarize_abstracts(abstracts):
    """
    Generate public-facing summaries for abstracts using OpenAI's GPT model.

    Displays a spinner animation while waiting for the API response.

    Args:
        abstracts: List of abstract data dictionaries

    Returns:
        List of dictionaries containing title, year, and summary
    """
    summaries = []

    def spinner_running(stop_event):
        """Display a spinning animation in the terminal while processing."""
        spinner = itertools.cycle(['|', '/', '-', '\\'])
        while not stop_event.is_set():
            sys.stdout.write(f"\rGenerating summary... {next(spinner)}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " "*30 + "\r")  # Clear line

    for abs_data in abstracts:
        prompt = (
            f"Title: {abs_data['title']} (Year: {abs_data['year']})\n"
            f"Abstract: {abs_data['abstract']}\n\n"
            "Write a public-facing summary in two paragraphs for a "
            "general audience."
        )
        stop_event = threading.Event()
        spinner_thread = threading.Thread(
            target=spinner_running, args=(stop_event,))
        spinner_thread.start()
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
        finally:
            stop_event.set()
            spinner_thread.join()
        summary = response.choices[0].message.content.strip()
        summaries.append({
            "title": abs_data["title"],
            "year": abs_data["year"],
            "summary": summary
        })
    return summaries


def parse_arguments():
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


def main():
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
        author_lines = format_author_list(
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
