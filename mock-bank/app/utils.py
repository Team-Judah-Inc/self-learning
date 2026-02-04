"""
API Utility Functions Module.

This module provides helper functions for the Flask API,
including date parsing and legacy pagination support.

Functions:
    parse_date: Parse ISO date strings.
    paginate: Legacy in-memory list pagination (deprecated, use core.pagination).
"""

import datetime
from typing import Optional, List, Tuple, Dict, Any, TypeVar

from flask import request, current_app


T = TypeVar('T')


def parse_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """
    Parse an ISO date string (YYYY-MM-DD) to a date object.
    
    Args:
        date_str: Date string in ISO format (YYYY-MM-DD).
        
    Returns:
        datetime.date object if parsing succeeds, None otherwise.
        
    Example:
        >>> parse_date("2024-01-15")
        datetime.date(2024, 1, 15)
        >>> parse_date("invalid")
        None
        >>> parse_date(None)
        None
    """
    if not date_str:
        return None
    
    try:
        return datetime.datetime.fromisoformat(date_str).date()
    except (ValueError, TypeError):
        return None


def paginate(data_list: List[T]) -> Tuple[List[T], Dict[str, Any]]:
    """
    Paginate an in-memory list based on request query parameters.
    
    .. deprecated::
        Use `core.pagination.paginate_list()` instead for new code.
        This function is kept for backward compatibility.
    
    Args:
        data_list: The full list of items to paginate.
        
    Returns:
        Tuple of (paginated_items, metadata_dict).
        
    Example:
        >>> # In a Flask route:
        >>> items, meta = paginate(all_items)
        >>> return jsonify({"meta": meta, "items": items})
    """
    # Parse pagination parameters
    try:
        limit = int(request.args.get('limit', current_app.config['DEFAULT_PAGE_SIZE']))
        page = int(request.args.get('page', 1))
    except ValueError:
        limit = current_app.config['DEFAULT_PAGE_SIZE']
        page = 1
    
    # Enforce global limits from config
    max_limit = current_app.config['MAX_PAGE_SIZE']
    limit = max(1, min(limit, max_limit))
    page = max(1, page)

    # Calculate slicing indices
    total_items = len(data_list)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    
    # Slice the data
    results = data_list[start_index:end_index]
    
    # Generate pagination metadata
    total_pages = (total_items + limit - 1) // limit if limit > 0 else 0
    
    meta = {
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    return results, meta
