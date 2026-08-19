"""
Admin Routes
Handles supervisor and admin endpoints for viewing consensus papers and analytics
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import get_all_papers_with_votes

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/all-papers', methods=['GET'])
@login_required
def get_admin_papers():
    """Get all papers with reviewer vote counts (admin only)"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    stage = request.args.get('stage', 'title')
    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    papers = get_all_papers_with_votes(stage)

    return jsonify({
        'total_papers': len(papers),
        'papers': [dict(p) for p in papers],
    })
