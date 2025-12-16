"""
Systems Team Routes
Handles API endpoints for systems team to review flagged papers
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    get_flagged_papers,
    save_systems_decision,
    get_systems_team_progress
)
from config import config

systems_bp = Blueprint('systems', __name__)


@systems_bp.route('/api/systems/flagged-papers', methods=['GET'])
@login_required
def get_flagged_papers_api():
    """Get all flagged papers for systems team"""
    if not current_user.is_systems():
        return jsonify({'error': 'Systems team access required'}), 403

    # Get all pending flagged papers
    papers = get_flagged_papers(status='pending')

    # Get vote counts for each paper
    papers_with_votes = []
    my_reviewed = 0

    for paper in papers:
        votes = get_systems_team_progress(paper['flag_id'])
        paper_dict = dict(paper)
        paper_dict['keep_votes'] = votes['keep']
        paper_dict['reject_votes'] = votes['reject']
        papers_with_votes.append(paper_dict)

    # Get user's decisions
    from models import get_db
    from psycopg2.extras import RealDictCursor

    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
                   SELECT flagged_paper_id, decision
                   FROM systems_decisions
                   WHERE reviewer_id = %s
                   """, (current_user.id,))

    my_decisions = {row['flagged_paper_id']: row['decision'] for row in cursor.fetchall()}
    my_reviewed = len(my_decisions)
    conn.close()

    return jsonify({
        'papers': papers_with_votes,
        'my_decisions': my_decisions,
        'total_flagged': len(papers_with_votes),
        'pending_review': len([p for p in papers_with_votes if p['flag_id'] not in my_decisions]),
        'my_reviewed': my_reviewed,
        'threshold': config.SYSTEMS_THRESHOLD
    })


@systems_bp.route('/api/systems/decision', methods=['POST'])
@login_required
def submit_systems_decision():
    """Submit systems team decision on a flagged paper"""
    if not current_user.is_systems():
        return jsonify({'error': 'Systems team access required'}), 403

    data = request.json
    flagged_paper_id = data.get('flagged_paper_id')
    decision = data.get('decision')
    notes = data.get('notes', None)

    if decision not in ['keep', 'reject']:
        return jsonify({'error': 'Invalid decision'}), 400

    # Save decision
    success = save_systems_decision(flagged_paper_id, current_user.id, decision, notes)

    if not success:
        return jsonify({'error': 'Failed to save decision'}), 500

    # Check if paper has reached consensus
    votes = get_systems_team_progress(flagged_paper_id)

    # Update flagged paper status if threshold reached
    if votes['keep'] >= config.SYSTEMS_THRESHOLD:
        from models import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
                       UPDATE flagged_papers
                       SET status = 'approved'
                       WHERE id = %s
                       """, (flagged_paper_id,))
        conn.commit()
        conn.close()
    elif votes['reject'] >= config.SYSTEMS_THRESHOLD:
        from models import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
                       UPDATE flagged_papers
                       SET status = 'rejected'
                       WHERE id = %s
                       """, (flagged_paper_id,))
        conn.commit()
        conn.close()

    return jsonify({
        'success': True,
        'message': 'Decision saved',
        'votes': votes
    })
