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
        if role == 'groupmate':
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
                   WHERE u.role = 'groupmate'
                   ORDER BY u.username
                   """)
    progress = cursor.fetchall()
    conn.close()
    return progress


# ============================================================================
# CONSENSUS QUERIES
# ============================================================================

def get_consensus_papers(threshold=5):
    """
    Get papers that have reached consensus (threshold or more 'keep' votes)

    Args:
        threshold: Minimum number of 'keep' votes (default: 5 out of 8)

    Returns:
        list of dicts with paper data and vote counts
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT
                       p.id,
                       p.title,
                       p.authors,
                       p.year,
                       p.abstract,
                       p.doi,
                       p.source,
                       COUNT(CASE WHEN sd.decision = 'keep' THEN 1 END) as keep_votes,
                       COUNT(CASE WHEN sd.decision = 'reject' THEN 1 END) as reject_votes
                   FROM papers p
                            LEFT JOIN swipe_decisions sd ON p.id = sd.paper_id
                   GROUP BY p.id
                   HAVING COUNT(CASE WHEN sd.decision = 'keep' THEN 1 END) >= %s
                   ORDER BY keep_votes DESC, p.title
                   """, (threshold,))
    papers = cursor.fetchall()
    conn.close()
    return papers


def get_all_papers_with_votes():
    """
    Get all papers with their vote counts (for admin view)

    Returns:
        list of dicts with paper data and vote counts
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT
                       p.id,
                       p.title,
                       p.authors,
                       p.year,
                       p.abstract,
                       p.doi,
                       p.source,
                       COUNT(CASE WHEN sd.decision = 'keep' THEN 1 END) as keep_votes,
                       COUNT(CASE WHEN sd.decision = 'reject' THEN 1 END) as reject_votes,
                       COUNT(sd.id) as total_votes
                   FROM papers p
                            LEFT JOIN swipe_decisions sd ON p.id = sd.paper_id
                   GROUP BY p.id
                   ORDER BY keep_votes DESC, p.title
                   """)
    papers = cursor.fetchall()
    conn.close()
    return papers
