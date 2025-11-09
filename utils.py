"""Utility functions for queuectl."""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from tabulate import tabulate


def generate_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())


def current_timestamp() -> str:
    """Get current timestamp as ISO format string."""
    return datetime.utcnow().isoformat()


def print_table(data: List[Dict[str, Any]], headers: List[str] = None) -> None:
    """Print data in a formatted table."""
    if not data:
        print("No data to display.")
        return
    
    if headers is None:
        headers = list(data[0].keys()) if data else []
    
    rows = []
    for item in data:
        row = [str(item.get(header, "")) for header in headers]
        rows.append(row)
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))

