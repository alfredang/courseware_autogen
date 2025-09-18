"""
Common Utility Functions

This module provides shared utility functions used across multiple modules
in the Courseware AutoGen system.

Author: Derrick Lim
Date: 3 March 2025
"""

import os
import re
import json
from typing import Any, Optional, Dict


def parse_json_content(content: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON content from various formats including markdown code blocks.
    
    Args:
        content: Raw content that may contain JSON
        
    Returns:
        Parsed JSON dictionary or None if parsing fails
    """
    # Check if the content is wrapped in markdown json blocks
    json_pattern = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)
    match = json_pattern.search(content)
    
    if match:
        # If ```json ``` is present, extract the JSON content
        json_str = match.group(1)
    else:
        # If no markdown blocks, assume the entire content is JSON
        json_str = content
    
    # Remove any leading/trailing whitespace
    json_str = json_str.strip()
    
    try:
        # Parse the JSON string
        parsed_json = json.loads(json_str)
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None


def save_uploaded_file(uploaded_file, save_dir: str) -> str:
    """
    Save uploaded Streamlit file to specified directory.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        save_dir: Directory to save the file
        
    Returns:
        Full path to the saved file
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, create if it doesn't.
    
    Args:
        directory: Directory path to ensure exists
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON data from a file with error handling.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        JSON data as dictionary or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return None


def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """
    Save data to JSON file with error handling.
    
    Args:
        data: Dictionary to save as JSON
        file_path: Path where to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving JSON file {file_path}: {e}")
        return False