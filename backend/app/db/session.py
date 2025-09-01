# Database functionality disabled - no database integration required
# This module provides mock implementations for database-related functions

from typing import Generator, Any

# Mock Base class for compatibility
class MockBase:
    metadata = None

Base = MockBase()


def get_db() -> Generator[Any, None, None]:
    """
    Mock database session dependency.
    Returns None since no database is used.
    """
    yield None


def create_tables():
    """
    Mock function - no tables to create.
    """
    pass


def drop_tables():
    """
    Mock function - no tables to drop.
    """
    pass