import requests
import os
from openai import OpenAI


# Set your NASA ADS API token and OpenAI API key
ADS_API_TOKEN = os.getenv("ADS_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Only query for refereed articles by adding 'property:refereed' to the query

client = OpenAI(api_key=OPENAI_API_KEY)

# ADS API endpoint and headers
ADS_API_URL = "https://api.adsabs.harvard.edu/v1/search/query"
ADS_HEADERS = {
    "Authorization": f"Bearer {ADS_API_TOKEN}"
}

# Query parameters
QUERY = 'pos(aff:"02138",1) pos(aff:"Smithsonian",1) year:2025 property:refereed'
PARAMS = {
    "q": QUERY,
    "fl": "title,abstract,year,author,aff,journal,pub,pubdate",
    "sort": "date desc",
    "rows": 3
}


def extract_authors_affiliations(doc):
    authors = doc.get("author", [])
    affiliations = doc.get("aff", [])
    # Pair authors with affiliations if possible
    author_aff_pairs = []
    for i, author in enumerate(authors):
        aff = affiliations[i] if i < len(affiliations) else ""
        author_aff_pairs.append({"author": author, "affiliation": aff})
    return author_aff_pairs


def fetch_abstracts():
    response = requests.get(ADS_API_URL, headers=ADS_HEADERS, params=PARAMS)
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


def print_authors_affiliations(authors_affiliations):
    for entry in authors_affiliations:
        author = entry["author"]
        aff = entry["affiliation"]
        print(f"  - {author} ({aff})" if aff else f"  - {author}")


def main():
    abstracts = fetch_abstracts()
    if not abstracts:
        print("No abstracts found.")
        return
    summaries = summarize_abstracts(abstracts)
    for i, s in enumerate(summaries):
        abs_data = abstracts[i]
        print(f"Title: {s['title']} (Year: {s['year']})")
        journal = abs_data.get('journal')
        publication = abs_data.get('publication')
        if journal and publication and journal != publication:
            print(f"Journal: {journal}\nPublication: {publication}")
        elif journal:
            print(f"Journal: {journal}")
        elif publication:
            print(f"Publication: {publication}")
        else:
            print("Journal/Publication: (none)")
        pubdate = abs_data.get('pubdate', '(unknown)')
        print(f"Publication Date: {pubdate}")
        authors_affiliations = abs_data.get("authors_affiliations", [])
        print("Authors & Affiliations:")
        print_authors_affiliations(authors_affiliations)
        print()
        print("ChatGPT summary of abstract, rewritten for a public audience:")
        print(s['summary'])
        print("\n" + "="*80 + "\n")


def summarize_abstracts(abstracts):
    import threading
    import itertools
    import sys
    import time
    summaries = []

    def spinner_running(stop_event):
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
            "Write a public-facing summary in two paragraphs for a general audience."
        )
        stop_event = threading.Event()
        spinner_thread = threading.Thread(
            target=spinner_running, args=(stop_event,))
        spinner_thread.start()
        try:
            response = client.chat.completions.create(model="gpt-4o",
                                                      messages=[
                                                          {"role": "user", "content": prompt}],
                                                      max_tokens=400,
                                                      temperature=0.7)
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


if __name__ == "__main__":
    main()
    # The following code replaces the duplicate main() and fetch_abstracts() above.
    # To print author names, affiliations, and journal info, update main() as below:
