import datetime
from flask import request, current_app

def parse_date(date_str):
    """
    Parses ISO date strings (YYYY-MM-DD). 
    Returns a date object or None on failure.
    """
    try:
        return datetime.datetime.fromisoformat(date_str).date()
    except (ValueError, TypeError):
        return None

def paginate(data_list):
    """
    Slices a list based on 'page' and 'limit' query parameters.
    Returns a tuple: (sliced_results, metadata_dict)
    """
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