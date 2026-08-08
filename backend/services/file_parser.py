"""
File Parser Service
Extracts text content from various file formats
"""

import os
from typing import Optional
from datetime import datetime
from PyPDF2 import PdfReader
import docx2txt


def extract_text_from_file(file_path: str) -> Optional[str]:
    """
    Extract text content from a file based on its extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text content or None if extraction fails
    """
    if not os.path.exists(file_path):
        return None
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return extract_text_from_docx(file_path)
        elif file_extension == '.txt':
            return extract_text_from_txt(file_path)
        else:
            return None
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return None


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file using PyPDF2
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    text_content = []
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            
            # Extract text from all pages
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
        
        return '\n\n'.join(text_content)
    
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX file using docx2txt
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        Extracted text content
    """
    try:
        # Use docx2txt for simple text extraction
        text = docx2txt.process(file_path)
        return text if text else ""
    
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from plain text file
    
    Args:
        file_path: Path to TXT file
        
    Returns:
        File content as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading TXT {file_path}: {e}")
            return ""
    except Exception as e:
        print(f"Error reading TXT {file_path}: {e}")
        return ""


def get_file_info(file_path: str) -> dict:
    """
    Get basic information about a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    if not os.path.exists(file_path):
        return {}
    
    file_stats = os.stat(file_path)
    file_extension = os.path.splitext(file_path)[1].lower()
    
    return {
        "file_name": os.path.basename(file_path),
        "file_extension": file_extension,
        "file_size_bytes": file_stats.st_size,
        "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
        "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
    }
