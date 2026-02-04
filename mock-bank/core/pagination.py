"""
Pagination Utilities Module.

This module provides shared pagination logic for API endpoints,
eliminating code duplication across route handlers.

Classes:
    PaginationParams: Dataclass holding parsed pagination parameters.

Functions:
    parse_pagination_params: Extract and validate pagination from Flask request.
    create_pagination_meta: Generate pagination metadata for API responses.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, TypeVar, Optional
from flask import request, current_app


T = TypeVar('T')


@dataclass
class PaginationParams:
    """
    Container for parsed and validated pagination parameters.
    
    Attributes:
        page: Current page number (1-indexed).
        limit: Maximum number of items per page.
        offset: Number of items to skip (calculated from page and limit).
        
    Example:
        >>> params = PaginationParams(page=2, limit=20, offset=20)
        >>> items = all_items[params.offset:params.offset + params.limit]
    """
    page: int
    limit: int
    offset: int
    
    @property
    def slice_end(self) -> int:
        """Calculate the end index for slicing."""
        return self.offset + self.limit


def parse_pagination_params(
    default_page_size: Optional[int] = None,
    max_page_size: Optional[int] = None
) -> PaginationParams:
    """
    Extract and validate pagination parameters from the current Flask request.
    
    Reads 'page' and 'limit' query parameters, applies defaults and constraints,
    and returns a validated PaginationParams object.
    
    Args:
        default_page_size: Default items per page. If None, uses app config.
        max_page_size: Maximum allowed items per page. If None, uses app config.
        
    Returns:
        PaginationParams with validated page, limit, and calculated offset.
        
    Example:
        >>> # In a Flask route handler:
        >>> params = parse_pagination_params()
        >>> items = repo.get_items(limit=params.limit, offset=params.offset)
        
    Note:
        - Page numbers are 1-indexed (first page is 1, not 0).
        - Invalid values default to page=1 and the configured default limit.
        - Limit is clamped between 1 and max_page_size.
    """
    # Get defaults from app config if not provided
    if default_page_size is None:
        default_page_size = current_app.config.get('DEFAULT_PAGE_SIZE', 20)
    if max_page_size is None:
        max_page_size = current_app.config.get('MAX_PAGE_SIZE', 100)
    
    # Parse query parameters with error handling
    try:
        limit = int(request.args.get('limit', default_page_size))
    except (ValueError, TypeError):
        limit = default_page_size
        
    try:
        page = int(request.args.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    
    # Apply constraints
    limit = max(1, min(limit, max_page_size))
    page = max(1, page)
    
    # Calculate offset
    offset = (page - 1) * limit
    
    return PaginationParams(page=page, limit=limit, offset=offset)


def create_pagination_meta(
    params: PaginationParams,
    items_returned: int,
    total_items: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate pagination metadata for API responses.
    
    Creates a standardized metadata dictionary that can be included in
    paginated API responses.
    
    Args:
        params: The PaginationParams used for the query.
        items_returned: Number of items actually returned in this page.
        total_items: Total count of all items (optional, enables total_pages).
        
    Returns:
        Dictionary containing pagination metadata:
            - page: Current page number
            - limit: Items per page
            - has_next: Whether more pages exist
            - has_prev: Whether previous pages exist
            - total_items: Total count (if provided)
            - total_pages: Total pages (if total_items provided)
            
    Example:
        >>> params = parse_pagination_params()
        >>> items = repo.get_items(limit=params.limit, offset=params.offset)
        >>> meta = create_pagination_meta(params, len(items), total_count)
        >>> return jsonify({"meta": meta, "items": items})
    """
    meta: Dict[str, Any] = {
        "page": params.page,
        "limit": params.limit,
        "has_prev": params.page > 1
    }
    
    if total_items is not None:
        # We know the total, so we can calculate exact pagination
        total_pages = (total_items + params.limit - 1) // params.limit if params.limit > 0 else 0
        meta["total_items"] = total_items
        meta["total_pages"] = total_pages
        meta["has_next"] = params.page < total_pages
    else:
        # Approximate: if we got a full page, there might be more
        meta["has_next"] = items_returned == params.limit
    
    return meta


def paginate_list(
    data_list: List[T],
    params: Optional[PaginationParams] = None
) -> tuple[List[T], Dict[str, Any]]:
    """
    Paginate an in-memory list and return results with metadata.
    
    Convenience function that combines slicing and metadata generation
    for in-memory list pagination.
    
    Args:
        data_list: The full list of items to paginate.
        params: Pagination parameters. If None, parses from current request.
        
    Returns:
        Tuple of (paginated_items, metadata_dict).
        
    Example:
        >>> all_users = repo.get_all_users()
        >>> users, meta = paginate_list(all_users)
        >>> return jsonify({"meta": meta, "users": users})
    """
    if params is None:
        params = parse_pagination_params()
    
    total_items = len(data_list)
    results = data_list[params.offset:params.slice_end]
    meta = create_pagination_meta(params, len(results), total_items)
    
    return results, meta
