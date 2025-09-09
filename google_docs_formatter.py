"""
Google Docs formatting utilities for CfA Science Highlights.

This module contains functions for formatting and styling Google Docs content,
including text styling, hyperlink creation, and document structure management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class GoogleDocsStyle:
    """Constants for Google Docs formatting styles."""
    
    # Font sizes (in points)
    TITLE_SIZE = 18
    SECTION_SIZE = 14
    PAPER_TITLE_SIZE = 13
    HEADER_SIZE = 11
    CONTENT_SIZE = 11
    DETAIL_SIZE = 10
    TIMESTAMP_SIZE = 12
    
    # Colors (RGB values 0-1)
    COLORS = {
        'title': {'red': 0.1, 'green': 0.1, 'blue': 0.1},
        'section': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'header': {'red': 0.6, 'green': 0.2, 'blue': 0.8},
        'content': {'red': 0.1, 'green': 0.1, 'blue': 0.1},
        'details': {'red': 0.3, 'green': 0.3, 'blue': 0.3},
        'timestamp': {'red': 0.5, 'green': 0.5, 'blue': 0.5},
        'separator': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
    }
    
    # Font family
    FONT_FAMILY = 'Roboto'


def create_text_request(text: str, index: int) -> Dict[str, Any]:
    """
    Create a request to insert text at a specific index.
    
    Args:
        text: Text to insert
        index: Character index where to insert the text
        
    Returns:
        Google Docs API request dictionary
    """
    return {
        'insertText': {
            'location': {'index': index},
            'text': text
        }
    }


def create_style_request(start_index: int, end_index: int, 
                        bold: bool = False, italic: bool = False,
                        font_size: Optional[int] = None, 
                        color: Optional[Dict[str, float]] = None,
                        font_weight: int = 400) -> Dict[str, Any]:
    """
    Create a request to style text in a specific range.
    
    Args:
        start_index: Start character index
        end_index: End character index
        bold: Whether text should be bold
        italic: Whether text should be italic
        font_size: Font size in points
        color: RGB color dictionary
        font_weight: Font weight (400=normal, 700=bold)
        
    Returns:
        Google Docs API request dictionary
    """
    text_style = {}
    fields = []
    
    if bold:
        text_style['bold'] = True
        fields.append('bold')
    
    if italic:
        text_style['italic'] = True
        fields.append('italic')
    
    if font_size:
        text_style['fontSize'] = {'magnitude': font_size, 'unit': 'PT'}
        fields.append('fontSize')
    
    if color:
        text_style['foregroundColor'] = {'color': {'rgbColor': color}}
        fields.append('foregroundColor')
    
    # Always set font family
    text_style['weightedFontFamily'] = {
        'fontFamily': GoogleDocsStyle.FONT_FAMILY, 
        'weight': font_weight
    }
    fields.append('weightedFontFamily')
    
    return {
        'updateTextStyle': {
            'range': {'startIndex': start_index, 'endIndex': end_index},
            'textStyle': text_style,
            'fields': ','.join(fields)
        }
    }


def create_document_header(current_index: int) -> tuple[List[Dict[str, Any]], int]:
    """
    Create document header with title and timestamp.
    
    Args:
        current_index: Current character index in the document
        
    Returns:
        Tuple of (requests list, new current index)
    """
    requests = []
    
    # Add title
    title_text = "Recent CfA-affiliated Science Publications\n"
    requests.append(create_text_request(title_text, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(title_text) - 1,
        bold=True, font_size=GoogleDocsStyle.TITLE_SIZE, 
        color=GoogleDocsStyle.COLORS['title'], font_weight=700
    ))
    current_index += len(title_text)
    
    # Add timestamp
    now = datetime.now()
    timestamp = now.strftime("Generated on %A, %B %d, %Y at %I:%M%p")
    timestamp_text = timestamp + "\n\n"
    requests.append(create_text_request(timestamp_text, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(timestamp),
        italic=True, font_size=GoogleDocsStyle.TIMESTAMP_SIZE, 
        color=GoogleDocsStyle.COLORS['timestamp']
    ))
    current_index += len(timestamp_text)
    
    # Add section header
    section_text = "Recent papers from CfA-affiliated authors (Top 10)\n\n"
    requests.append(create_text_request(section_text, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(section_text) - 3,
        bold=True, font_size=GoogleDocsStyle.SECTION_SIZE, 
        color=GoogleDocsStyle.COLORS['section'], font_weight=700
    ))
    current_index += len(section_text)
    
    return requests, current_index


def format_publication_date(pubdate: str) -> str:
    """
    Format publication date for better readability.
    
    Args:
        pubdate: Raw publication date string
        
    Returns:
        Formatted publication date string
    """
    if not pubdate or pubdate == 'Unknown date':
        return 'Unknown date'
    
    # Clean up pubdate formatting (remove -00 endings)
    clean_pubdate = pubdate.replace('-00', '').replace('--', '-')
    
    # Convert YYYY-MM to more readable format
    if len(clean_pubdate.split('-')) == 2:
        try:
            year, month = clean_pubdate.split('-')
            month_names = {
                '01': 'January', '02': 'February', '03': 'March',
                '04': 'April', '05': 'May', '06': 'June',
                '07': 'July', '08': 'August', '09': 'September',
                '10': 'October', '11': 'November', '12': 'December'
            }
            if month in month_names:
                return f"{month_names[month]} {year}"
        except (ValueError, IndexError):
            pass  # Keep original format if parsing fails
    
    return clean_pubdate


def create_paper_content_requests(paper: Dict[str, Any], paper_index: int, 
                                current_index: int) -> tuple[List[Dict[str, Any]], int]:
    """
    Create requests for a single paper's content.
    
    Args:
        paper: Paper dictionary containing title, year, authors, etc.
        paper_index: Index of the paper (1-based)
        current_index: Current character index in the document
        
    Returns:
        Tuple of (requests list, new current index)
    """
    requests = []
    
    title = paper.get('title', 'No title available')
    year = paper.get('year', 'Unknown year')
    journal = paper.get('journal', '')
    publication = paper.get('publication', '')
    pubdate = paper.get('pubdate', 'Unknown date')
    authors_affiliations = paper.get('authors_affiliations', [])
    abstract = paper.get('abstract', 'No abstract available')
    
    # Paper title
    paper_title_text = f"{paper_index}. {title}"
    if year:
        paper_title_text += f" ({year})"
    paper_title_text += "\n"
    
    requests.append(create_text_request(paper_title_text, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(paper_title_text) - 1,
        bold=True, font_size=GoogleDocsStyle.PAPER_TITLE_SIZE, 
        color=GoogleDocsStyle.COLORS['title'], font_weight=700
    ))
    current_index += len(paper_title_text)
    
    # Publication details
    details_text = _build_publication_details(journal, publication, pubdate, authors_affiliations)
    if details_text:
        requests.append(create_text_request(details_text, current_index))
        requests.append(create_style_request(
            current_index, current_index + len(details_text),
            font_size=GoogleDocsStyle.CONTENT_SIZE
        ))
        current_index += len(details_text)
    
    return requests, current_index


def create_abstract_section_requests(abstract: str, current_index: int) -> tuple[List[Dict[str, Any]], int]:
    """
    Create requests for the abstract section.
    
    Args:
        abstract: Abstract text
        current_index: Current character index in the document
        
    Returns:
        Tuple of (requests list, new current index)
    """
    requests = []
    
    # Abstract header
    abstract_header_text = "ABSTRACT\n"
    requests.append(create_text_request(abstract_header_text, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(abstract_header_text) - 1,
        bold=True, font_size=GoogleDocsStyle.HEADER_SIZE, 
        color=GoogleDocsStyle.COLORS['header'], font_weight=700
    ))
    current_index += len(abstract_header_text)
    
    # Abstract content (indented)
    indented_abstract = "    " + abstract.replace('\n', '\n    ') + "\n\n"
    requests.append(create_text_request(indented_abstract, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(indented_abstract),
        font_size=GoogleDocsStyle.DETAIL_SIZE, 
        color=GoogleDocsStyle.COLORS['details']
    ))
    current_index += len(indented_abstract)
    
    return requests, current_index


def create_summary_section_requests(summary: str, current_index: int) -> tuple[List[Dict[str, Any]], int]:
    """
    Create requests for the summary section.
    
    Args:
        summary: Summary text
        current_index: Current character index in the document
        
    Returns:
        Tuple of (requests list, new current index)
    """
    requests = []
    
    # Summary header
    summary_header_text = "PUBLIC SUMMARY\n"
    requests.append(create_text_request(summary_header_text, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(summary_header_text) - 1,
        bold=True, font_size=GoogleDocsStyle.HEADER_SIZE, 
        color=GoogleDocsStyle.COLORS['header'], font_weight=700
    ))
    current_index += len(summary_header_text)
    
    # Summary content (indented)
    indented_summary = "    " + summary.replace('\n', '\n    ') + "\n\n"
    requests.append(create_text_request(indented_summary, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(indented_summary),
        font_size=GoogleDocsStyle.CONTENT_SIZE, 
        color=GoogleDocsStyle.COLORS['content']
    ))
    current_index += len(indented_summary)
    
    return requests, current_index


def create_separator_requests(current_index: int) -> tuple[List[Dict[str, Any]], int]:
    """
    Create requests for a section separator.
    
    Args:
        current_index: Current character index in the document
        
    Returns:
        Tuple of (requests list, new current index)
    """
    requests = []
    
    separator_text = "─" * 60 + "\n\n"
    requests.append(create_text_request(separator_text, current_index))
    requests.append(create_style_request(
        current_index, current_index + len(separator_text) - 2,
        color=GoogleDocsStyle.COLORS['separator']
    ))
    current_index += len(separator_text)
    
    return requests, current_index


def create_justification_request(end_index: int) -> Dict[str, Any]:
    """
    Create request to justify text alignment for the entire document.
    
    Args:
        end_index: End character index of the document
        
    Returns:
        Google Docs API request dictionary
    """
    return {
        'updateParagraphStyle': {
            'range': {'startIndex': 1, 'endIndex': end_index},
            'paragraphStyle': {'alignment': 'JUSTIFIED'},
            'fields': 'alignment'
        }
    }


def _build_publication_details(journal: str, publication: str, pubdate: str, 
                             authors_affiliations: List[Dict[str, str]]) -> str:
    """
    Build the publication details text section.
    
    Args:
        journal: Journal name
        publication: Publication name
        pubdate: Publication date
        authors_affiliations: List of author-affiliation pairs
        
    Returns:
        Formatted details text
    """
    details_text = ""
    
    if journal:
        details_text += f"Journal: {journal}\n"
    elif publication:
        details_text += f"Publication: {publication}\n"
    
    formatted_pubdate = format_publication_date(pubdate)
    if formatted_pubdate != 'Unknown date':
        details_text += f"Publication Date: {formatted_pubdate}\n"
    
    # Authors
    if authors_affiliations:
        authors = [entry["author"] for entry in authors_affiliations]
        if len(authors) > 5:
            author_text = f"Authors: {', '.join(authors[:3])}, et al. ({len(authors)} total authors)\n"
        else:
            author_text = f"Authors: {', '.join(authors)}\n"
        details_text += author_text
    
    # NASA ADS link placeholder
    details_text += "Link: [View on NASA ADS]\n\n"
    
    return details_text