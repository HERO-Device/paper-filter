"""
Moderator-related database queries
"""

from psycopg2.extras import RealDictCursor
from ._db import get_db


def get_disputed_papers(stage='title'):
    """
    Get papers where reviewers disagreed (1 keep, 1 reject) for a given stage
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
                            LEFT JOIN moderator_decisions md ON p.id = md.paper_id AND md.stage = %s
                            LEFT JOIN flagged_papers fp ON p.id = fp.paper_id
                   WHERE sd.stage = %s
                     AND md.id IS NULL
                     AND fp.id IS NULL
                   GROUP BY p.id
                   HAVING COUNT(sd.id) = 2
                      AND COUNT(CASE WHEN sd.decision = 'keep' THEN 1 END) = 1
                      AND COUNT(CASE WHEN sd.decision = 'reject' THEN 1 END) = 1
                   ORDER BY p.id
                   """, (stage, stage))

    papers = cursor.fetchall()
    conn.close()
    return papers


def save_moderator_decision(paper_id, decision, notes=None, stage='title'):
    """
    Save moderator's decision on a disputed paper for a given stage

    Returns:
        True if successful, False otherwise
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
                       INSERT INTO moderator_decisions (paper_id, decision, notes, stage)
                       VALUES (%s, %s, %s, %s) ON CONFLICT (paper_id, stage) DO
                       UPDATE
                           SET decision = EXCLUDED.decision, notes = EXCLUDED.notes, decided_at = NOW()
                       """, (paper_id, decision, notes, stage))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error saving moderator decision: {e}")
        return False


def get_moderator_stats(stage='title'):
    """
    Get statistics for moderator dashboard for a given stage

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
                            LEFT JOIN moderator_decisions md ON p.id = md.paper_id AND md.stage = %s
                   WHERE sd.stage = %s
                     AND md.id IS NULL
                   GROUP BY p.id
                   HAVING COUNT(sd.id) = 2
                      AND COUNT(CASE WHEN sd.decision = 'keep' THEN 1 END) = 1
                      AND COUNT(CASE WHEN sd.decision = 'reject' THEN 1 END) = 1
                   """, (stage, stage))

    pending = cursor.fetchone()
    pending_count = pending[0] if pending else 0

    # Count completed decisions
    cursor.execute("SELECT COUNT(*) FROM moderator_decisions WHERE stage = %s", (stage,))
    completed = cursor.fetchone()[0]

    conn.close()

    return {
        'pending': pending_count,
        'completed': completed
    }
