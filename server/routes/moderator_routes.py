"""
Moderator Routes
Handles API endpoints for moderator to review disputed papers
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    get_disputed_papers,
    save_moderator_decision,
    get_moderator_stats
)

moderator_bp = Blueprint('moderator', __name__)


@moderator_bp.route('/moderator')
@login_required
def moderator_page():
    """Moderator dashboard page"""
    if not current_user.is_moderator():
        return redirect(url_for('main.dashboard'))
    return render_template('moderator.html', user=current_user)


@moderator_bp.route('/api/moderator/disputed-papers', methods=['GET'])
@login_required
def get_disputed_papers_api():
    """Get all disputed papers (1 yes, 1 no from reviewers)"""
    if not current_user.is_moderator():
        return jsonify({'error': 'Moderator access required'}), 403

    papers = get_disputed_papers()
    stats = get_moderator_stats()

    return jsonify({
        'papers': papers,
        'stats': stats
    })


@moderator_bp.route('/api/moderator/decision', methods=['POST'])
@login_required
def submit_moderator_decision():
    """Submit moderator decision on a disputed paper"""
    if not current_user.is_moderator():
        return jsonify({'error': 'Moderator access required'}), 403

    data = request.json
    paper_id = data.get('paper_id')
    decision = data.get('decision')
    notes = data.get('notes', None)

    if decision not in ['keep', 'reject']:
        return jsonify({'error': 'Invalid decision'}), 400

    success = save_moderator_decision(paper_id, decision, notes)

    if not success:
        return jsonify({'error': 'Failed to save decision'}), 500

    return jsonify({
        'success': True,
        'message': 'Decision saved successfully'
    })