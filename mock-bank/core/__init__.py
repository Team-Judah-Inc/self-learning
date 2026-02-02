"""
Core Module for Mock Banking Application.

This module provides shared utilities, constants, and helper functions
used across both the API (app/) and data generation (data_gen/) modules.

Submodules:
    pagination: Shared pagination logic for API endpoints.
"""

from .pagination import (
    PaginationParams,
    parse_pagination_params,
    create_pagination_meta,
    paginate_list
)

__all__ = [
    'PaginationParams',
    'parse_pagination_params',
    'create_pagination_meta',
    'paginate_list'
]
