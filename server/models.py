"""
Database Models and Query Functions
Handles all database operations for the Paper Filter application
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from config import config


def get_db():
    """Get database connection"""
    return psycopg2.connect(**config.DB_CONFIG)


# ============================================================================
# USER QUERIES
# ============================================================================

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

        # Initialize progress for groupmates
        if role == 'reviewer':
            cursor.execute("""
                           INSERT INTO user_progress (user_id, current_paper_index, total_kept, total_rejected)
                           VALUES (%s, 0, 0, 0)
                           """, (user_id,))

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


# ============================================================================
# PAPER QUERIES
# ============================================================================

def get_total_papers():
    """Get total number of papers"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM papers")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_paper_by_index(index):
    """
    Get paper by index (0-based)

    Returns:
        dict with paper data or None
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT id, title, authors, year, abstract, doi, source
                   FROM papers
                   ORDER BY id
                       LIMIT 1 OFFSET %s
                   """, (index,))
    paper = cursor.fetchone()
    conn.close()
    return paper


def get_paper_by_id(paper_id):
    """Get paper by ID"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT id, title, authors, year, abstract, doi, source
                   FROM papers
                   WHERE id = %s
                   """, (paper_id,))
    paper = cursor.fetchone()
    conn.close()
    return paper


# ============================================================================
# SWIPE DECISION QUERIES
# ============================================================================

def save_swipe_decision(user_id, paper_id, decision):
    """
    Save user's swipe decision (keep or reject)

    Returns:
        True if successful, False otherwise
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       INSERT INTO swipe_decisions (user_id, paper_id, decision)
                       VALUES (%s, %s, %s)
                           ON CONFLICT (user_id, paper_id) DO UPDATE SET decision = EXCLUDED.decision
                       """, (user_id, paper_id, decision))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error saving swipe decision: {e}")
        return False


def get_user_decision(user_id, paper_id):
    """
    Get user's decision for a specific paper

    Returns:
        'keep', 'reject', or None if not decided
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT decision FROM swipe_decisions
                   WHERE user_id = %s AND paper_id = %s
                   """, (user_id, paper_id))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_paper_vote_counts(paper_id):
    """
    Get vote counts for a paper

    Returns:
        dict with 'keep' and 'reject' counts
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT decision, COUNT(*) as count
                   FROM swipe_decisions
                   WHERE paper_id = %s
                   GROUP BY decision
                   """, (paper_id,))

    results = cursor.fetchall()
    conn.close()

    votes = {'keep': 0, 'reject': 0}
    for decision, count in results:
        votes[decision] = count

    return votes


# ============================================================================
# USER PROGRESS QUERIES
# ============================================================================

def get_user_progress(user_id):
    """
    Get user's progress

    Returns:
        dict with current_paper_index, total_kept, total_rejected
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT current_paper_index, total_kept, total_rejected, last_active
                   FROM user_progress
                   WHERE user_id = %s
                   """, (user_id,))
    progress = cursor.fetchone()
    conn.close()
    return progress


def update_user_progress(user_id, current_index, total_kept, total_rejected):
    """Update user's progress"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
                   UPDATE user_progress
                   SET current_paper_index = %s,
                       total_kept = %s,
                       total_rejected = %s,
                       last_active = NOW()
                   WHERE user_id = %s
                   """, (current_index, total_kept, total_rejected, user_id))
    conn.commit()
    conn.close()


def get_all_user_progress():
    """
    Get progress for all groupmates

    Returns:
        list of dicts with user info and progress
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT
                       u.id,
                       u.username,
                       u.display_name,
                       u.role,
                       COALESCE(p.current_paper_index, 0) as current_paper_index,
                       COALESCE(p.total_kept, 0) as total_kept,
                       COALESCE(p.total_rejected, 0) as total_rejected,
                       p.last_active
                   FROM users u
                            LEFT JOIN user_progress p ON u.id = p.user_id
                   WHERE u.role = 'reviewer'
                   ORDER BY u.username
                   """)
    progress = cursor.fetchall()
    conn.close()
    return progress


# ============================================================================
# MODERATOR QUERIES
# ============================================================================

def get_disputed_papers():
    """
    Get papers where reviewers disagreed (1 keep, 1 reject)
    Excludes any papers that have been flagged (those go to systems instead)
    Only returns papers not yet decided by moderator

    Returns:
        list of dicts with paper data and reviewer votes
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
                   SELECT p.id                                               as paper_id,
                          p.title,
                          p.authors,
                          p.year,
                          p.abstract,
                          p.doi,
                          p.source,
                          COUNT(CASE WHEN sd.decision = 'keep' THEN 1 END)   as keep_votes,
                          COUNT(CASE WHEN sd.decision = 'reject' THEN 1 END) as reject_votes
                   FROM papers p
                            INNER JOIN swipe_decisions sd ON p.id = sd.paper_id
                            LEFT JOIN moderator_decisions md ON p.id = md.paper_id
                            LEFT JOIN flagged_papers fp ON p.id = fp.paper_id -- Check for flags
                   WHERE md.id IS NULL -- Not yet decided by moderator
                     AND fp.id IS NULL -- NOT flagged (flagged papers go to systems)
                   GROUP BY p.id
                   HAVING COUNT(sd.id) = 2                                       -- Both reviewers voted
                      AND COUNT(CASE WHEN sd.decision = 'keep' THEN 1 END) = 1   -- 1 keep
                      AND COUNT(CASE WHEN sd.decision = 'reject' THEN 1 END) = 1 -- 1 reject
                   ORDER BY p.id
                   """)

    papers = cursor.fetchall()
    conn.close()
    return papers


def save_moderator_decision(paper_id, decision, notes=None):
    """
    Save moderator's decision on a disputed paper

    Returns:
        True if successful, False otherwise
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       INSERT INTO moderator_decisions (paper_id, decision, notes)
                       VALUES (%s, %s, %s) ON CONFLICT (paper_id) DO
                       UPDATE
                           SET decision = EXCLUDED.decision, notes = EXCLUDED.notes
                       """, (paper_id, decision, notes))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error saving moderator decision: {e}")
        return False


def get_moderator_stats():
    """
    Get statistics for moderator dashboard

    Returns:
        dict with pending and completed counts
    """
    conn = get_db()
    cursor = conn.cursor()

    # Count disputed papers
    cursor.execute("""
                   SELECT COUNT(DISTINCT p.id)
                   FROM papers p
                            INNER JOIN swipe_decisions sd ON p.id = sd.paper_id
                            LEFT JOIN moderator_decisions md ON p.id = md.paper_id
                   WHERE md.id IS NULL
                   GROUP BY p.id
                   HAVING COUNT(sd.id) = 2
                      AND COUNT(CASE WHEN sd.decision = 'keep' THEN 1 END) = 1
                      AND COUNT(CASE WHEN sd.decision = 'reject' THEN 1 END) = 1
                   """)

    pending = cursor.fetchone()
    pending_count = pending[0] if pending else 0

    # Count completed decisions
    cursor.execute("SELECT COUNT(*) FROM moderator_decisions")
    completed = cursor.fetchone()[0]

    conn.close()

    return {
        'pending': pending_count,
        'completed': completed
    }

# ============================================================================
# FLAGGED PAPERS QUERIES
# ============================================================================

def flag_paper(user_id, paper_id, reason=None):
    """Flag a paper for systems team review"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       INSERT INTO flagged_papers (paper_id, flagged_by, reason)
                       VALUES (%s, %s, %s) ON CONFLICT (paper_id, flagged_by) DO
                       UPDATE
                           SET reason = EXCLUDED.reason, flagged_at = CURRENT_TIMESTAMP
                           RETURNING id
                       """, (paper_id, user_id, reason))

        result = cursor.fetchone()
        conn.commit()
        conn.close()
        return result is not None

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error flagging paper: {e}")
        return False

def get_flagged_papers_for_systems(status='pending'):
    """
    Get all flagged papers for systems team review
    Only returns papers not yet reviewed by systems

    Returns:
        list of dicts with paper data and flag info
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
                   SELECT fp.id          as flag_id,
                          fp.flagged_at,
                          fp.reason,
                          p.id           as paper_id,
                          p.title,
                          p.authors,
                          p.year,
                          p.abstract,
                          p.doi,
                          p.source,
                          u.display_name as flagged_by_name,
                          COUNT(DISTINCT fp.flagged_by) as flag_count
                   FROM flagged_papers fp
                            JOIN papers p ON fp.paper_id = p.id
                            JOIN users u ON fp.flagged_by = u.id
                            LEFT JOIN systems_decisions sd ON fp.id = sd.flagged_paper_id
                   WHERE fp.status = %s
                     AND sd.id IS NULL -- Not yet reviewed
                   GROUP BY fp.id, p.id, u.display_name
                   ORDER BY fp.flagged_at DESC
                   """, (status,))

    papers = cursor.fetchall()
    conn.close()
    return papers


def save_systems_decision(flagged_paper_id, decision, notes=None):
    """
    Save systems team decision on a flagged paper

    Returns:
        True if successful, False otherwise
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       INSERT INTO systems_decisions (flagged_paper_id, decision, notes)
                       VALUES (%s, %s, %s) ON CONFLICT (flagged_paper_id) DO
                       UPDATE
                           SET decision = EXCLUDED.decision, notes = EXCLUDED.notes
                       """, (flagged_paper_id, decision, notes))

        # Update flagged paper status
        cursor.execute("""
                       UPDATE flagged_papers
                       SET status = 'reviewed'
                       WHERE id = %s
                       """, (flagged_paper_id,))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error saving systems decision: {e}")
        return False


def get_systems_stats():
    """
    Get statistics for systems dashboard

    Returns:
        dict with total flagged and reviewed counts
    """
    conn = get_db()
    cursor = conn.cursor()

    # Total ever flagged
    cursor.execute("SELECT COUNT(DISTINCT id) FROM flagged_papers")
    total_flagged = cursor.fetchone()[0]

    # Reviewed (have a systems decision)
    cursor.execute("SELECT COUNT(*) FROM systems_decisions")
    reviewed = cursor.fetchone()[0]

    # Pending (flagged but no systems decision yet)
    cursor.execute("""
        SELECT COUNT(DISTINCT fp.id)
        FROM flagged_papers fp
        LEFT JOIN systems_decisions sd ON fp.id = sd.flagged_paper_id
        WHERE sd.id IS NULL
    """)
    pending = cursor.fetchone()[0]

    conn.close()

    return {
        'total_flagged': total_flagged,
        'reviewed': reviewed,
        'pending': pending
    }