"""
PDF Downloader Module

Functions for downloading PDF files.
"""

import requests


def download_pdf(pdf_url: str, session: requests.Session, headers: dict) -> bytes:
    """
    Download a PDF file from URL.
    
    Args:
        pdf_url: The URL of the PDF to download
        session: requests Session object
        headers: HTTP headers to use
        
    Returns:
        The PDF content as bytes
        
    Raises:
        requests.RequestException: If download fails
    """
    response = session.get(pdf_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    # Verify it's actually a PDF
    content_type = response.headers.get('Content-Type', '')
    if 'pdf' not in content_type.lower():
        raise ValueError(f"Downloaded file is not a PDF (Content-Type: {content_type})")
    
    return response.content
