"""
Paper-related database queries
"""

from psycopg2.extras import RealDictCursor
from ._db import get_db


def get_total_papers(stage='title'):
    """Get total number of papers for a given stage"""
    conn = get_db()
    cursor = conn.cursor()

    if stage == 'title':
        cursor.execute("SELECT COUNT(*) FROM papers")
    elif stage == 'abstract':
        cursor.execute("""
                       SELECT COUNT(*)
                       FROM abstract_eligible_papers
                       WHERE source != 'systems_keep'
                       """)

    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_paper_by_index(index, stage='title'):
    """
    Get paper by index (0-based) for a given stage

    Returns:
        dict with paper data or None
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if stage == 'title':
        cursor.execute("""
                       SELECT id, title, authors, year, abstract, doi, source
                       FROM papers
                       ORDER BY id
                           LIMIT 1
                       OFFSET %s
                       """, (index,))
    elif stage == 'abstract':
        cursor.execute("""
                       SELECT p.id, p.title, p.authors, p.year, p.abstract, p.doi, p.source
                       FROM papers p
                                JOIN abstract_eligible_papers aep ON p.id = aep.paper_id
                       WHERE aep.source != 'systems_keep'
                       ORDER BY p.id
                           LIMIT 1
                       OFFSET %s
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


def get_all_papers_with_votes(stage='title'):
    """
    Get every paper with its reviewer vote counts for a given stage.

    Returns:
        list of dicts with paper fields plus keep_votes, reject_votes, total_votes
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT p.id,
                          p.title,
                          p.authors,
                          p.year,
                          p.doi,
                          p.source,
                          COUNT(sd.id) FILTER (WHERE sd.decision = 'keep')   AS keep_votes,
                          COUNT(sd.id) FILTER (WHERE sd.decision = 'reject') AS reject_votes,
                          COUNT(sd.id)                                       AS total_votes
                   FROM papers p
                            LEFT JOIN swipe_decisions sd
                                      ON sd.paper_id = p.id AND sd.stage = %s
                   GROUP BY p.id, p.title, p.authors, p.year, p.doi, p.source
                   ORDER BY p.id
                   """, (stage,))
    papers = cursor.fetchall()
    conn.close()
    return papers
