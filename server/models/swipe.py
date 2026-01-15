"""
Swipe decision and user progress queries
"""

from psycopg2.extras import RealDictCursor
from ._db import get_db
from .paper import get_total_papers


def save_swipe_decision(user_id, paper_id, decision, stage='title'):
    """Save user's swipe decision (keep or reject) with stage"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       INSERT INTO swipe_decisions (user_id, paper_id, decision, stage)
                       VALUES (%s, %s, %s, %s) ON CONFLICT (user_id, paper_id, stage) 
            DO
                       UPDATE SET decision = EXCLUDED.decision, decided_at = NOW()
                       """, (user_id, paper_id, decision, stage))

        conn.commit()
        conn.close()

        # Check for consensus after title swipe
        if stage == 'title':
            check_title_consensus(paper_id)

        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error saving swipe decision: {e}")
        return False



def get_user_decision(user_id, paper_id, stage='title'):
    """
    Get user's decision for a specific paper and stage

    Returns:
        'keep', 'reject', or None if not decided
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT decision
                   FROM swipe_decisions
                   WHERE user_id = %s
                     AND paper_id = %s
                     AND stage = %s
                   """, (user_id, paper_id, stage))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_paper_vote_counts(paper_id, stage='title'):
    """
    Get vote counts for a paper in a given stage

    Returns:
        dict with 'keep' and 'reject' counts
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT decision, COUNT(*) as count
                   FROM swipe_decisions
                   WHERE paper_id = %s
                     AND stage = %s
                   GROUP BY decision
                   """, (paper_id, stage))

    results = cursor.fetchall()
    conn.close()

    votes = {'keep': 0, 'reject': 0}
    for decision, count in results:
        votes[decision] = count

    return votes


def get_user_progress(user_id, stage='title'):
    """
    Get user's progress for a specific stage

    Returns:
        dict with current_paper_index, total_kept, total_rejected, total_papers
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
                   SELECT current_paper_index, total_kept, total_rejected, last_active
                   FROM user_progress
                   WHERE user_id = %s
                     AND stage = %s
                   """, (user_id, stage))
    progress = cursor.fetchone()

    # If no progress exists for this stage, create it
    if not progress:
        cursor.execute("""
                       INSERT INTO user_progress (user_id, stage, current_paper_index, total_kept, total_rejected)
                       VALUES (%s, %s, 0, 0, 0) RETURNING current_paper_index, total_kept, total_rejected, last_active
                       """, (user_id, stage))
        conn.commit()
        progress = cursor.fetchone()

    # Get total papers for this stage
    total = get_total_papers(stage)

    result = dict(progress) if progress else {}
    result['total_papers'] = total
    result['completion_percentage'] = (result.get('current_paper_index', 0) / total * 100) if total > 0 else 0

    conn.close()
    return result


def update_user_progress(user_id, current_index, total_kept, total_rejected, stage='title'):
    """Update user's progress for a specific stage"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
                   UPDATE user_progress
                   SET current_paper_index = %s,
                       total_kept          = %s,
                       total_rejected      = %s,
                       last_active         = NOW()
                   WHERE user_id = %s
                     AND stage = %s
                   """, (current_index, total_kept, total_rejected, user_id, stage))
    conn.commit()
    conn.close()


def get_all_user_progress(stage='title'):
    """
    Get progress for all reviewers in a given stage

    Returns:
        list of dicts with user info and progress
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT u.id,
                          u.username,
                          u.display_name,
                          u.role,
                          COALESCE(p.current_paper_index, 0) as current_paper_index,
                          COALESCE(p.total_kept, 0)          as total_kept,
                          COALESCE(p.total_rejected, 0)      as total_rejected,
                          p.last_active
                   FROM users u
                            LEFT JOIN user_progress p ON u.id = p.user_id AND p.stage = %s
                   WHERE u.role = 'reviewer'
                   ORDER BY u.username
                   """, (stage,))
    progress = cursor.fetchall()
    conn.close()
    return progress


def check_title_consensus(paper_id):
    """
    Check if paper reached consensus in title stage.
    If both reviewers kept it, add to abstract_eligible_papers.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get all title stage decisions for this paper
    cursor.execute("""
                   SELECT decision, COUNT(*) as count
                   FROM swipe_decisions
                   WHERE paper_id = %s AND stage = 'title'
                   GROUP BY decision
                   """, (paper_id,))

    results = cursor.fetchall()
    votes = {decision: count for decision, count in results}

    keep_count = votes.get('keep', 0)

    # Both kept it - add to abstract review
    if keep_count == 2:
        cursor.execute("""
                       INSERT INTO abstract_eligible_papers (paper_id, source)
                       VALUES (%s, 'reviewer_consensus') ON CONFLICT DO NOTHING
                       """, (paper_id,))
        conn.commit()
        conn.close()
        return 'consensus_keep'

    conn.close()
    return 'pending'


def check_title_consensus(paper_id):
    """
    Check if paper reached consensus in title stage.
    If both reviewers kept it, add to abstract_eligible_papers.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get all title stage decisions for this paper
    cursor.execute("""
                   SELECT decision, COUNT(*) as count
                   FROM swipe_decisions
                   WHERE paper_id = %s AND stage = 'title'
                   GROUP BY decision
                   """, (paper_id,))

    results = cursor.fetchall()
    votes = {decision: count for decision, count in results}

    keep_count = votes.get('keep', 0)

    # Both kept it - add to abstract review
    if keep_count == 2:
        cursor.execute("""
                       INSERT INTO abstract_eligible_papers (paper_id, source)
                       VALUES (%s, 'reviewer_consensus') ON CONFLICT (paper_id) DO NOTHING
                       """, (paper_id,))
        conn.commit()
        conn.close()
        return 'consensus_keep'

    conn.close()
    return 'pending'
