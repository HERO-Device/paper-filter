"""
Admin Routes
Handles supervisor and admin endpoints for viewing consensus papers and analytics
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import get_db
from config import config
from psycopg2.extras import RealDictCursor

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/all-papers', methods=['GET'])
@login_required
def get_admin_papers():
    """Get all papers with vote counts (admin only)"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403

    #papers = get_all_papers_with_votes()

    return jsonify({
        'total_papers': len(papers),
        'papers': [dict(p) for p in papers]
    })