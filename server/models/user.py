"""
User-related database queries
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from ._db import get_db


def get_user_by_username(username):
    """
    Get user by username

    Returns:
        dict with user data or None if not found
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT id, username, password_hash, display_name, role FROM users WHERE username = %s",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT id, username, display_name, role FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(username, password_hash, display_name, role, invite_code):
    """
    Create new user

    Returns:
        user_id if successful, None if username exists
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       INSERT INTO users (username, password_hash, display_name, role, invite_code)
                       VALUES (%s, %s, %s, %s, %s)
                           RETURNING id
                       """, (username, password_hash, display_name, role, invite_code))

        user_id = cursor.fetchone()[0]

        # Initialize progress for both title and abstract stages
        if role == 'reviewer':
            cursor.execute("""
                           INSERT INTO user_progress (user_id, stage, current_paper_index, total_kept, total_rejected)
                           VALUES (%s, 'title', 0, 0, 0), (%s, 'abstract', 0, 0, 0)
                           """, (user_id, user_id))

        conn.commit()
        conn.close()
        return user_id

    except psycopg2.IntegrityError:
        conn.rollback()
        conn.close()
        return None


def check_invite_code_used(invite_code):
    """Check if invite code has been used"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE invite_code = %s", (invite_code,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0
