"""
ScholarGuard Services Package
Contains business logic for file parsing, analysis, and report generation
"""

from .file_parser import extract_text_from_file
from .analyzer import analyze_document

__all__ = ['extract_text_from_file', 'analyze_document']