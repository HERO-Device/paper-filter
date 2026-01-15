"""
Moderator Routes - Resolve disputed papers (1 keep, 1 reject)
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import models

moderator_bp = Blueprint('moderator', __name__)


@moderator_bp.route('/moderator')
@login_required
def moderator_interface():
    """Render moderator interface"""
    if not current_user.is_moderator():
        return "Access denied. Moderators only.", 403

    return render_template('moderator.html')


@moderator_bp.route('/api/moderator/disputed-papers')
@login_required
def get_disputed_papers():
    """Get papers with 1 keep, 1 reject"""
    if not current_user.is_moderator():
        return jsonify({'error': 'Access denied'}), 403

    stage = request.args.get('stage', 'title')

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        papers = models.get_disputed_papers(stage)
        stats = models.get_moderator_stats(stage)

        return jsonify({
            'papers': papers,
            'stats': stats
        })

    except Exception as e:
        print(f"Error getting disputed papers: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@moderator_bp.route('/api/moderator/decision', methods=['POST'])
@login_required
def save_decision():
    """Save moderator's decision"""
    if not current_user.is_moderator():
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    paper_id = data.get('paper_id')
    decision = data.get('decision')  # 'keep' or 'reject'
    notes = data.get('notes', '')
    stage = data.get('stage', 'title')

    if not paper_id or not decision:
        return jsonify({'error': 'Missing data'}), 400

    if decision not in ['keep', 'reject']:
        return jsonify({'error': 'Invalid decision'}), 400

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        success = models.save_moderator_decision(paper_id, decision, notes, stage)

        if not success:
            return jsonify({'error': 'Failed to save decision'}), 500

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error saving moderator decision: {e}")
        return jsonify({'error': 'Internal server error'}), 500
