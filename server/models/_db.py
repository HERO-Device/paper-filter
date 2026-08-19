"""
Database connection utilities
"""

import psycopg2
from config import config


def get_db():
    """Get database connection"""
    return psycopg2.connect(**config.DB_CONFIG)