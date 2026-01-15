"""
Abstract stage-specific database queries
"""

from ._db import get_db


def populate_abstract_eligible_papers():
    """
    Populate abstract_eligible_papers table from title stage results.
    Call this when title stage is complete or when initializing abstract stage.

    Returns:
        Number of papers added to abstract pool
    """
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Reviewer consensus (2 keeps, not flagged)
        cursor.execute("""
                       INSERT INTO abstract_eligible_papers (paper_id, source)
                       SELECT DISTINCT p.id, 'reviewer_consensus'
                       FROM papers p
                       WHERE (SELECT COUNT(*)
                              FROM swipe_decisions sd
                              WHERE sd.paper_id = p.id
                                AND sd.decision = 'keep'
                                AND sd.stage = 'title') = 2
                         AND NOT EXISTS (SELECT 1
                                         FROM flagged_papers fp
                                         WHERE fp.paper_id = p.id)
                           ON CONFLICT (paper_id) DO NOTHING
                       """)

        # Moderator keeps
        cursor.execute("""
                       INSERT INTO abstract_eligible_papers (paper_id, source)
                       SELECT DISTINCT md.paper_id, 'moderator_keep'
                       FROM moderator_decisions md
                       WHERE md.decision = 'keep'
                         AND md.stage = 'title' ON CONFLICT (paper_id) DO NOTHING
                       """)

        # Systems keeps (flagged papers)
        cursor.execute("""
                       INSERT INTO abstract_eligible_papers (paper_id, source)
                       SELECT DISTINCT fp.paper_id, 'systems_keep'
                       FROM flagged_papers fp
                                JOIN systems_decisions sd ON sd.flagged_paper_id = fp.id
                       WHERE sd.decision = 'keep' ON CONFLICT (paper_id) DO NOTHING
                       """)

        conn.commit()

        # Return count
        cursor.execute("SELECT COUNT(*) FROM abstract_eligible_papers")
        count = cursor.fetchone()[0]

        conn.close()
        return count

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error populating abstract eligible papers: {e}")
        return 0


def get_abstract_stage_status():
    """
    Check if abstract stage has been initialized and get counts

    Returns:
        dict with initialized status and paper counts
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM abstract_eligible_papers")
    total = cursor.fetchone()[0]

    cursor.execute("""
                   SELECT COUNT(*)
                   FROM abstract_eligible_papers
                   WHERE source != 'systems_keep'
                   """)
    reviewer_pool = cursor.fetchone()[0]

    cursor.execute("""
                   SELECT COUNT(*)
                   FROM abstract_eligible_papers
                   WHERE source = 'systems_keep'
                   """)
    systems_pool = cursor.fetchone()[0]

    conn.close()

    return {
        'initialized': total > 0,
        'total_papers': total,
        'reviewer_pool': reviewer_pool,
        'systems_pool': systems_pool
    }
