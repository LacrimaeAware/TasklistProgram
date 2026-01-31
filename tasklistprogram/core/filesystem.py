"""Filesystem utilities for creating task-related folders."""
import re
from pathlib import Path


def sanitize_folder_name(name: str) -> str:
    """
    Sanitize a string to be safe for use as a folder name.
    
    This function properly handles special characters without mangling
    normal letters like 'n' and 't'.
    
    Args:
        name: The original name (e.g., task title or group name)
        
    Returns:
        A sanitized version safe for filesystem use
    """
    if not name:
        return "Untitled"
    
    # Replace unsafe filesystem characters with spaces
    # Only replace actual problematic characters, NOT normal letters
    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(unsafe_chars, ' ', name)
    
    # Collapse multiple spaces/underscores
    sanitized = re.sub(r'[ _]+', ' ', sanitized)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    
    # Limit length (Windows has 255 char limit for paths)
    if len(sanitized) > 100:
        sanitized = sanitized[:100].rstrip('. ')
    
    # Ensure we have a valid name
    if not sanitized:
        return "Untitled"
        
    return sanitized


def create_task_document_folder(base_path: Path, folder_name: str) -> Path:
    """
    Create a folder for task documents with proper name sanitization.
    
    Args:
        base_path: Parent directory where the folder should be created
        folder_name: Desired folder name (will be sanitized)
        
    Returns:
        Path to the created folder
    """
    safe_name = sanitize_folder_name(folder_name)
    folder_path = base_path / safe_name
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path
