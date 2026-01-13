"""
Unit tests for cfascience.py

Tests the core functionality of the CfA Science Highlights Generator,
including author extraction, formatting, and API interaction logic.
"""

import pytest
from unittest.mock import Mock, patch
from cfascience import (
    print_authors_affiliations,
    fetch_abstracts,
    summarize_abstracts
)
from utils import (
    extract_authors_affiliations,
    format_author_list_for_display, 
    is_cfa_affiliated,
    classify_authors,
    Color
)


class TestExtractAuthorsAffiliations:
    """Test the extract_authors_affiliations function."""
    
    def test_extract_with_matching_authors_and_affiliations(self):
        """Test extraction when authors and affiliations have same length."""
        doc = {
            "author": ["Smith, John", "Doe, Jane"],
            "aff": ["Harvard University", "MIT"]
        }
        result = extract_authors_affiliations(doc)
        expected = [
            {"author": "Smith, John", "affiliation": "Harvard University"},
            {"author": "Doe, Jane", "affiliation": "MIT"}
        ]
        assert result == expected
    
    def test_extract_with_more_authors_than_affiliations(self):
        """Test extraction when there are more authors than affiliations."""
        doc = {
            "author": ["Smith, John", "Doe, Jane", "Brown, Bob"],
            "aff": ["Harvard University"]
        }
        result = extract_authors_affiliations(doc)
        expected = [
            {"author": "Smith, John", "affiliation": "Harvard University"},
            {"author": "Doe, Jane", "affiliation": ""},
            {"author": "Brown, Bob", "affiliation": ""}
        ]
        assert result == expected
    
    def test_extract_with_no_affiliations(self):
        """Test extraction when no affiliations are provided."""
        doc = {
            "author": ["Smith, John", "Doe, Jane"],
            "aff": []
        }
        result = extract_authors_affiliations(doc)
        expected = [
            {"author": "Smith, John", "affiliation": ""},
            {"author": "Doe, Jane", "affiliation": ""}
        ]
        assert result == expected
    
    def test_extract_with_empty_doc(self):
        """Test extraction with empty document."""
        doc = {}
        result = extract_authors_affiliations(doc)
        assert result == []
    
    def test_extract_with_missing_authors(self):
        """Test extraction when authors key is missing."""
        doc = {"aff": ["Harvard University"]}
        result = extract_authors_affiliations(doc)
        assert result == []


class TestFormatAuthorListForDisplay:
    """Test the format_author_list function."""
    
    def test_format_with_cfa_authors_only(self):
        """Test formatting with only CfA-affiliated authors."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": "Harvard-Smithsonian CfA"},
            {"author": "Doe, Jane", "affiliation": "Center for Astrophysics"}
        ]
        result = format_author_list_for_display(authors_affiliations)
        
        assert len(result) == 1
        assert "CfA Authors:" in result[0]
        assert "Smith, John, Doe, Jane" in result[0]
    
    def test_format_with_mixed_authors(self):
        """Test formatting with both CfA and non-CfA authors."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": "Harvard-Smithsonian CfA"},
            {"author": "Doe, Jane", "affiliation": "MIT"},
            {"author": "Brown, Bob", "affiliation": "Smithsonian Institution"}
        ]
        result = format_author_list_for_display(authors_affiliations)
        
        assert len(result) == 2
        assert any("CfA Authors:" in line for line in result)
        assert any("Other Authors:" in line for line in result)
        assert any("Smith, John, Brown, Bob" in line for line in result)
        assert any("Doe, Jane" in line for line in result)
    
    def test_format_with_no_cfa_authors(self):
        """Test formatting with no CfA-affiliated authors."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": "MIT"},
            {"author": "Doe, Jane", "affiliation": "Stanford University"}
        ]
        result = format_author_list_for_display(authors_affiliations)
        
        assert len(result) == 1
        assert "Other Authors:" in result[0]
        assert "Smith, John, Doe, Jane" in result[0]
    
    def test_format_with_empty_affiliations(self):
        """Test formatting with empty affiliations."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": ""},
            {"author": "Doe, Jane", "affiliation": None}
        ]
        result = format_author_list_for_display(authors_affiliations)
        
        assert len(result) == 1
        assert "Other Authors:" in result[0]
        assert "Smith, John, Doe, Jane" in result[0]
    
    def test_format_case_insensitive_affiliation_matching(self):
        """Test that affiliation matching is case insensitive."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": "SMITHSONIAN ASTROPHYSICAL OBSERVATORY"},
            {"author": "Doe, Jane", "affiliation": "center for astrophysics | harvard & smithsonian"}
        ]
        result = format_author_list_for_display(authors_affiliations)
        
        assert len(result) == 1
        assert "CfA Authors:" in result[0]
        assert "Smith, John, Doe, Jane" in result[0]


class TestPrintAuthorsAffiliations:
    """Test the print_authors_affiliations function."""
    
    @patch('cfascience.print')
    def test_print_cfa_authors_highlighted(self, mock_print):
        """Test that CfA authors are printed with highlighting."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": "Harvard-Smithsonian CfA"},
        ]
        
        print_authors_affiliations(authors_affiliations)
        
        # Check that print was called with CfA Authors header
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("CfA Authors:" in call for call in calls)
        # Check that magenta color code is used - look for both \x1b and \033 representations
        assert any("\\x1b[35m" in call or "\033[35m" in call for call in calls)
    
    @patch('cfascience.print')
    def test_print_mixed_authors(self, mock_print):
        """Test printing both CfA and other authors."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": "Harvard-Smithsonian CfA"},
            {"author": "Doe, Jane", "affiliation": "MIT"}
        ]
        
        print_authors_affiliations(authors_affiliations)
        
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("CfA Authors:" in call for call in calls)
        assert any("Other Authors:" in call for call in calls)
    
    @patch('cfascience.print')
    def test_print_authors_with_no_affiliation(self, mock_print):
        """Test printing authors with missing affiliations."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": ""},
            {"author": "Doe, Jane", "affiliation": None}
        ]
        
        print_authors_affiliations(authors_affiliations)
        
        calls = [str(call) for call in mock_print.call_args_list]
        # Should print as "Other Authors" without affiliation info
        assert any("Other Authors:" in call for call in calls)


class TestFetchAbstracts:
    """Test the fetch_abstracts function."""

    @patch('cfascience.requests.get')
    def test_fetch_abstracts_successful_response(self, mock_get):
        """Test successful API response handling."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "title": ["Test Paper Title"],
                        "abstract": "This is a test abstract",
                        "year": "2025",
                        "journal": "Test Journal",
                        "pub": "Test Publication",
                        "pubdate": "2025-01-01",
                        "bibcode": "2025TestJ...1..123S",
                        "identifier": ["arXiv:2501.12345"],
                        "author": ["Smith, John"],
                        "aff": ["Harvard-Smithsonian CfA"]
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = fetch_abstracts(ads_api_token="test_token")

        assert len(result) == 1
        assert result[0]["title"] == "Test Paper Title"
        assert result[0]["abstract"] == "This is a test abstract"
        assert result[0]["year"] == "2025"
        assert result[0]["bibcode"] == "2025TestJ...1..123S"
        assert result[0]["arxiv_id"] == "2501.12345"
        assert len(result[0]["authors_affiliations"]) == 1

        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://api.adsabs.harvard.edu/v1/search/query" in call_args[0]

    @patch('cfascience.requests.get')
    def test_fetch_abstracts_empty_response(self, mock_get):
        """Test handling of empty API response."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": {"docs": []}}
        mock_get.return_value = mock_response

        result = fetch_abstracts(ads_api_token="test_token")

        assert result == []

    @patch('cfascience.requests.get')
    def test_fetch_abstracts_missing_fields(self, mock_get):
        """Test handling of documents with missing fields."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "title": ["Minimal Paper"],
                        # Missing most fields
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = fetch_abstracts(ads_api_token="test_token")

        assert len(result) == 1
        assert result[0]["title"] == "Minimal Paper"
        assert result[0]["abstract"] == ""
        assert result[0]["year"] == ""
        assert result[0]["bibcode"] == ""
        assert result[0]["arxiv_id"] is None
        assert result[0]["authors_affiliations"] == []

    @patch('cfascience.requests.get')
    def test_fetch_abstracts_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response

        with pytest.raises(Exception):
            fetch_abstracts(ads_api_token="test_token")


class TestSummarizeAbstracts:
    """Test the summarize_abstracts function."""

    @patch('cfascience.threading.Thread')
    @patch('cfascience.threading.Event')
    def test_summarize_single_abstract(self, mock_event, mock_thread):
        """Test summarizing a single abstract."""
        # Setup mocks
        mock_event_instance = Mock()
        mock_event.return_value = mock_event_instance

        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test summary."
        mock_client.chat.completions.create.return_value = mock_response

        abstracts = [
            {
                "title": "Test Paper",
                "year": "2025",
                "abstract": "Test abstract content"
            }
        ]

        result = summarize_abstracts(abstracts, mock_client)

        assert len(result) == 1
        assert result[0]["title"] == "Test Paper"
        assert result[0]["year"] == "2025"
        assert result[0]["summary"] == "This is a test summary."

        # Verify OpenAI API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["model"] == "gpt-4o"
        assert call_args[1]["max_tokens"] == 400
        assert call_args[1]["temperature"] == 0.7

    @patch('cfascience.threading.Thread')
    @patch('cfascience.threading.Event')
    def test_summarize_multiple_abstracts(self, mock_event, mock_thread):
        """Test summarizing multiple abstracts."""
        # Setup mocks
        mock_event_instance = Mock()
        mock_event.return_value = mock_event_instance

        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test summary."
        mock_client.chat.completions.create.return_value = mock_response

        abstracts = [
            {"title": "Paper 1", "year": "2025", "abstract": "Abstract 1"},
            {"title": "Paper 2", "year": "2024", "abstract": "Abstract 2"}
        ]

        result = summarize_abstracts(abstracts, mock_client)

        assert len(result) == 2
        assert result[0]["title"] == "Paper 1"
        assert result[1]["title"] == "Paper 2"
        # Verify API was called twice (once per abstract)
        assert mock_client.chat.completions.create.call_count == 2

    def test_summarize_with_empty_list(self):
        """Test summarizing with empty abstracts list."""
        mock_client = Mock()
        result = summarize_abstracts([], mock_client)

        assert result == []
        # API should not be called
        mock_client.chat.completions.create.assert_not_called()


class TestColorConstants:
    """Test the Color class constants."""
    
    def test_color_constants_exist(self):
        """Test that all expected color constants exist."""
        expected_colors = [
            'CYAN', 'GREEN', 'YELLOW', 'RED', 'MAGENTA', 'PURPLE', 'BOLD', 'END'
        ]
        
        for color in expected_colors:
            assert hasattr(Color, color)
            assert isinstance(getattr(Color, color), str)
    
    def test_ansi_codes_format(self):
        """Test that color codes follow ANSI format."""
        # Most ANSI codes start with \033[
        colors_to_test = ['PURPLE', 'CYAN', 'RED', 'GREEN', 'BOLD', 'END']
        
        for color_name in colors_to_test:
            color_code = getattr(Color, color_name)
            assert color_code.startswith('\033[')
            assert color_code.endswith('m')


class TestIsCfaAffiliated:
    """Test the is_cfa_affiliated function."""
    
    def test_cfa_keywords(self):
        """Test recognition of CfA-related keywords."""
        assert is_cfa_affiliated("Harvard-Smithsonian Center for Astrophysics")
        assert is_cfa_affiliated("Smithsonian Astrophysical Observatory")
        assert is_cfa_affiliated("CfA")
        assert is_cfa_affiliated("center for astrophysics")
    
    def test_non_cfa_affiliations(self):
        """Test non-CfA affiliations return False."""
        assert not is_cfa_affiliated("MIT")
        assert not is_cfa_affiliated("Harvard University")
        assert not is_cfa_affiliated("Stanford University")
    
    def test_empty_affiliations(self):
        """Test empty or None affiliations return False."""
        assert not is_cfa_affiliated("")
        assert not is_cfa_affiliated(None)


class TestClassifyAuthors:
    """Test the classify_authors function."""
    
    def test_mixed_classification(self):
        """Test classification of mixed author list."""
        authors_affiliations = [
            {"author": "Smith, John", "affiliation": "Harvard-Smithsonian CfA"},
            {"author": "Doe, Jane", "affiliation": "MIT"},
            {"author": "Brown, Bob", "affiliation": "Smithsonian Institution"}
        ]
        
        cfa_authors, non_cfa_authors = classify_authors(authors_affiliations)
        
        assert "Smith, John" in cfa_authors
        assert "Brown, Bob" in cfa_authors
        assert "Doe, Jane" in non_cfa_authors
        assert len(cfa_authors) == 2
        assert len(non_cfa_authors) == 1


class TestArXivIntegration:
    """Test ArXiv ID extraction and processing."""

    @patch('cfascience.requests.get')
    def test_arxiv_id_extraction(self, mock_get):
        """Test extraction of ArXiv IDs from identifier field."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "title": ["Paper with ArXiv"],
                        "abstract": "Test abstract",
                        "year": "2025",
                        "identifier": ["arXiv:2501.12345", "doi:10.1234/example"],
                        "bibcode": "2025TestJ...1..123A",
                        "author": ["Test, Author"],
                        "aff": ["Test University"]
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = fetch_abstracts(ads_api_token="test_token")

        assert len(result) == 1
        assert result[0]["arxiv_id"] == "2501.12345"

    @patch('cfascience.requests.get')
    def test_no_arxiv_id(self, mock_get):
        """Test handling when no ArXiv ID is present."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "title": ["Paper without ArXiv"],
                        "abstract": "Test abstract",
                        "year": "2025",
                        "identifier": ["doi:10.1234/example"],
                        "bibcode": "2025TestJ...1..123B",
                        "author": ["Test, Author"],
                        "aff": ["Test University"]
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = fetch_abstracts(ads_api_token="test_token")

        assert len(result) == 1
        assert result[0]["arxiv_id"] is None


if __name__ == "__main__":
    pytest.main([__file__])