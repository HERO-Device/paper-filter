"""
Systems team (flagged papers) database queries
"""

from psycopg2.extras import RealDictCursor
from ._db import get_db


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


def get_flagged_papers_for_systems(stage='title', status='pending'):
    """
    Get all flagged papers for systems team review

    For title stage: All flagged papers not yet reviewed
    For abstract stage: Only papers from abstract_eligible_papers with source='systems_keep'

    Returns:
        list of dicts with paper data and flag info
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if stage == 'title':
        cursor.execute("""
                       SELECT fp.id                         as flag_id,
                              fp.flagged_at,
                              fp.reason,
                              p.id                          as paper_id,
                              p.title,
                              p.authors,
                              p.year,
                              p.abstract,
                              p.doi,
                              p.source,
                              u.display_name                as flagged_by_name,
                              COUNT(DISTINCT fp.flagged_by) as flag_count
                       FROM flagged_papers fp
                                JOIN papers p ON fp.paper_id = p.id
                                JOIN users u ON fp.flagged_by = u.id
                                LEFT JOIN systems_decisions sd ON fp.id = sd.flagged_paper_id
                       WHERE fp.status = %s
                         AND sd.id IS NULL
                       GROUP BY fp.id, p.id, u.display_name
                       ORDER BY fp.flagged_at DESC
                       """, (status,))

    elif stage == 'abstract':
        # For abstract stage, only show papers that were systems_keep from title stage
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
                              u.display_name as flagged_by_name
                       FROM abstract_eligible_papers aep
                                JOIN papers p ON aep.paper_id = p.id
                                JOIN flagged_papers fp ON p.id = fp.paper_id
                                JOIN users u ON fp.flagged_by = u.id
                       WHERE aep.source = 'systems_keep'
                         AND NOT EXISTS (SELECT 1
                                         FROM swipe_decisions sd
                                         WHERE sd.paper_id = p.id
                                           AND sd.stage = 'abstract')
                       ORDER BY fp.flagged_at DESC
                       """)

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
                           SET decision = EXCLUDED.decision, notes = EXCLUDED.notes, decided_at = NOW()
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


def get_systems_stats(stage='title'):
    """
    Get statistics for systems dashboard for a given stage

    Returns:
        dict with total flagged and reviewed counts
    """
    conn = get_db()
    cursor = conn.cursor()

    if stage == 'title':
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

    elif stage == 'abstract':
        # For abstract stage, only count papers in abstract_eligible_papers with systems_keep
        cursor.execute("""
                       SELECT COUNT(DISTINCT p.id)
                       FROM abstract_eligible_papers aep
                                JOIN papers p ON aep.paper_id = p.id
                       WHERE aep.source = 'systems_keep'
                       """)
        total_flagged = cursor.fetchone()[0]

        # Reviewed in abstract stage
        cursor.execute("""
                       SELECT COUNT(DISTINCT p.id)
                       FROM abstract_eligible_papers aep
                                JOIN papers p ON aep.paper_id = p.id
                                JOIN swipe_decisions sd ON p.id = sd.paper_id
                       WHERE aep.source = 'systems_keep'
                         AND sd.stage = 'abstract'
                       """)
        reviewed = cursor.fetchone()[0]

        # Pending
        pending = total_flagged - reviewed

    conn.close()

    return {
        'total_flagged': total_flagged,
        'reviewed': reviewed,
        'pending': pending
    }
