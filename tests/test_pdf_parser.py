"""
Unit tests for utils/pdf_parser.py
Run with: pytest tests/test_pdf_parser.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import io
import pytest
from unittest.mock import patch, MagicMock
from utils.pdf_parser import extract_text_from_pdf


class TestExtractTextFromPdf:
    def test_bytes_input(self):
        """Should accept raw bytes."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "John Doe\nSoftware Engineer"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("utils.pdf_parser.PdfReader", return_value=mock_reader):
            result = extract_text_from_pdf(b"fake-pdf-bytes")

        assert "John Doe" in result
        assert "Software Engineer" in result

    def test_file_like_object(self):
        """Should accept a file-like object with .read()."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Jane Smith\nData Scientist"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        fake_file = io.BytesIO(b"fake-pdf")

        with patch("utils.pdf_parser.PdfReader", return_value=mock_reader):
            result = extract_text_from_pdf(fake_file)

        assert "Jane Smith" in result

    def test_multipage_concatenation(self):
        """Pages should be joined with double newlines."""
        page1 = MagicMock()
        page1.extract_text.return_value = "Page 1 content"
        page2 = MagicMock()
        page2.extract_text.return_value = "Page 2 content"
        mock_reader = MagicMock()
        mock_reader.pages = [page1, page2]

        with patch("utils.pdf_parser.PdfReader", return_value=mock_reader):
            result = extract_text_from_pdf(b"fake")

        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "\n\n" in result

    def test_empty_pages_handled(self):
        """Pages returning None or empty string should be skipped."""
        page1 = MagicMock()
        page1.extract_text.return_value = None
        page2 = MagicMock()
        page2.extract_text.return_value = "Real content"
        mock_reader = MagicMock()
        mock_reader.pages = [page1, page2]

        with patch("utils.pdf_parser.PdfReader", return_value=mock_reader):
            result = extract_text_from_pdf(b"fake")

        assert "Real content" in result

    def test_error_returns_message(self):
        """On exception, should return error string instead of raising."""
        with patch("utils.pdf_parser.PdfReader", side_effect=Exception("Corrupted PDF")):
            result = extract_text_from_pdf(b"bad-pdf")

        assert "Error" in result
        assert "Corrupted PDF" in result

    def test_all_empty_pages_returns_fallback(self):
        """All-empty extraction should return the fallback message."""
        page = MagicMock()
        page.extract_text.return_value = ""
        mock_reader = MagicMock()
        mock_reader.pages = [page]

        with patch("utils.pdf_parser.PdfReader", return_value=mock_reader):
            result = extract_text_from_pdf(b"fake")

        assert "Could not extract" in result
