"""
Supervisor Routes
Handles API endpoints for supervisor to view consensus papers
"""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import get_db
from psycopg2.extras import RealDictCursor

supervisor_bp = Blueprint('supervisor', __name__)


@supervisor_bp.route('/api/supervisor/consensus-papers', methods=['GET'])
@login_required
def get_consensus_papers_api():
    """Get all consensus papers (2 reviewer yes OR moderator yes OR systems yes)"""
    if not current_user.is_supervisor() and not current_user.is_admin():
        return jsonify({'error': 'Supervisor access required'}), 403

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get papers with automatic consensus (2 yes votes from reviewers, NOT flagged)
    cursor.execute("""
        SELECT
            p.id,
            p.title,
            p.authors,
            p.year,
            p.doi,
            p.source,
            'auto' as decision_type
        FROM papers p
        INNER JOIN swipe_decisions sd ON p.id = sd.paper_id
        LEFT JOIN flagged_papers fp ON p.id = fp.paper_id
        WHERE sd.decision = 'keep' AND fp.id IS NULL
        GROUP BY p.id
        HAVING COUNT(sd.id) = 2
    """)

    auto_consensus = cursor.fetchall()

    # Get papers decided by moderator (keep only)
    cursor.execute("""
        SELECT 
            p.id,
            p.title,
            p.authors,
            p.year,
            p.doi,
            p.source,
            'moderator' as decision_type
        FROM papers p
        INNER JOIN moderator_decisions md ON p.id = md.paper_id
        WHERE md.decision = 'keep'
    """)

    moderator_keeps = cursor.fetchall()

    # Get papers approved by systems team (keep only)
    cursor.execute("""
        SELECT 
            p.id,
            p.title,
            p.authors,
            p.year,
            p.doi,
            p.source,
            'systems' as decision_type
        FROM papers p
        INNER JOIN flagged_papers fp ON p.id = fp.paper_id
        INNER JOIN systems_decisions sd ON fp.id = sd.flagged_paper_id
        WHERE sd.decision = 'keep'
    """)

    systems_keeps = cursor.fetchall()

    # Combine all three lists (remove duplicates by ID)
    all_papers = list(auto_consensus) + list(moderator_keeps) + list(systems_keeps)

    # Remove duplicates (same paper might be in multiple categories)
    seen_ids = set()
    unique_papers = []
    for paper in all_papers:
        if paper['id'] not in seen_ids:
            seen_ids.add(paper['id'])
            unique_papers.append(paper)

    # Get progress stats
    cursor.execute("SELECT COUNT(*) FROM papers")
    total_papers = cursor.fetchone()['count']

    # Count papers that need decisions
    cursor.execute("""
        SELECT COUNT(DISTINCT p.id)
        FROM papers p
        LEFT JOIN swipe_decisions sd ON p.id = sd.paper_id
        LEFT JOIN flagged_papers fp ON p.id = fp.paper_id
        WHERE 
            -- Not fully reviewed by both reviewers
            (SELECT COUNT(*) FROM swipe_decisions WHERE paper_id = p.id) < 2
            OR
            -- Disputed but no moderator decision
            (
                (SELECT COUNT(*) FROM swipe_decisions WHERE paper_id = p.id AND decision = 'keep') = 1
                AND (SELECT COUNT(*) FROM swipe_decisions WHERE paper_id = p.id AND decision = 'reject') = 1
                AND NOT EXISTS (SELECT 1 FROM moderator_decisions WHERE paper_id = p.id)
            )
            OR
            -- Flagged but no systems decision
            (
                fp.id IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM systems_decisions WHERE flagged_paper_id = fp.id)
            )
    """)

    pending_result = cursor.fetchone()
    pending_count = pending_result['count'] if pending_result else 0

    completed_count = len(unique_papers)

    conn.close()

    return jsonify({
        'papers': unique_papers,
        'progress': {
            'total': total_papers,
            'completed': completed_count,
            'pending': pending_count
        }
    })