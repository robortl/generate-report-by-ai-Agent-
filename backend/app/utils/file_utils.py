"""
File utility functions for the report generation system.
This module provides functions for file processing and validation.
"""

import os
import mimetypes
import magic
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Initialize mimetypes
mimetypes.init()

# Supported file types
SUPPORTED_FILE_TYPES = {
    # Text files
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.csv': 'text/csv',
    
    # Document files
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    
    # Web files
    '.html': 'text/html',
    '.htm': 'text/html',
    '.json': 'application/json',
    '.xml': 'application/xml',
}

def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension (including the dot)
    """
    return os.path.splitext(filename)[1].lower()

def is_valid_file_type(filename: str) -> bool:
    """
    Check if the file type is supported.
    
    Args:
        filename: Name of the file
        
    Returns:
        Boolean indicating if the file type is supported
    """
    extension = get_file_extension(filename)
    return extension in SUPPORTED_FILE_TYPES

def get_mime_type(file_path: str) -> str:
    """
    Get the MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type of the file
    """
    try:
        # First try to use python-magic for more accurate detection
        mime_type = magic.from_file(file_path, mime=True)
        if mime_type:
            return mime_type
    except (ImportError, IOError) as e:
        logger.warning(f"Could not determine MIME type using python-magic: {e}")
    
    # Fall back to mimetypes module
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    
    # If all else fails, use the extension mapping
    extension = get_file_extension(file_path)
    return SUPPORTED_FILE_TYPES.get(extension, 'application/octet-stream')

def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Size of the file in bytes
    """
    return os.path.getsize(file_path)

def get_file_categories() -> List[Dict[str, str]]:
    """
    Get the list of supported file categories.
    
    Returns:
        List of dictionaries with category ID and name
    """
    return [
        {"id": "meeting", "name": "Meeting Minutes"},
        {"id": "report", "name": "Business Report"},
        {"id": "contract", "name": "Contract Document"},
        {"id": "email", "name": "Email Communication"},
        {"id": "general", "name": "General Document"}
    ]

def create_temp_file(content: bytes, prefix: str = "temp", suffix: str = "") -> str:
    """
    Create a temporary file with the given content.
    
    Args:
        content: Content to write to the file
        prefix: Prefix for the temporary file name
        suffix: Suffix for the temporary file name (e.g., file extension)
        
    Returns:
        Path to the created temporary file
    """
    import tempfile
    
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
        return path
    except Exception as e:
        os.unlink(path)
        raise e