"""
Admin Routes
Handles supervisor and admin endpoints for viewing consensus papers and analytics
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import get_consensus_papers, get_all_papers_with_votes
from config import config

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/supervisor/consensus-papers', methods=['GET'])
@login_required
def get_supervisor_papers():
    """Get consensus papers (for supervisor view)"""
    if not (current_user.is_supervisor() or current_user.is_admin()):
        return jsonify({'error': 'Supervisor access required'}), 403

    papers = get_consensus_papers(config.CONSENSUS_THRESHOLD)

    return jsonify({
        'threshold': config.CONSENSUS_THRESHOLD,
        'total_papers': len(papers),
        'papers': [dict(p) for p in papers]
    })


@admin_bp.route('/api/admin/all-papers', methods=['GET'])
@login_required
def get_admin_papers():
    """Get all papers with vote counts (admin only)"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    papers = get_all_papers_with_votes()

    return jsonify({
        'total_papers': len(papers),
        'papers': [dict(p) for p in papers]
    })