"""
Systems Routes - Review flagged papers
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import models

systems_bp = Blueprint('systems', __name__)


@systems_bp.route('/systems')
@login_required
def systems_interface():
    """Render systems interface"""
    if not current_user.is_systems():
        return "Access denied. Systems team only.", 403

    return render_template('systems.html')


@systems_bp.route('/api/systems/flagged-papers')
@login_required
def get_flagged_papers():
    """Get flagged papers for review"""
    if not current_user.is_systems():
        return jsonify({'error': 'Access denied'}), 403

    stage = request.args.get('stage', 'title')

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        papers = models.get_flagged_papers_for_systems(stage)
        stats = models.get_systems_stats(stage)

        return jsonify({
            'papers': papers,
            'stats': stats
        })

    except Exception as e:
        print(f"Error getting flagged papers: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@systems_bp.route('/api/systems/decision', methods=['POST'])
@login_required
def save_decision():
    """Save systems decision on flagged paper"""
    if not current_user.is_systems():
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    flag_id = data.get('flag_id')
    paper_id = data.get('paper_id')
    decision = data.get('decision')  # 'keep' or 'reject'
    notes = data.get('notes', '')
    stage = data.get('stage', 'title')

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        if stage == 'title':
            # Title stage uses flag_id
            if not flag_id or not decision:
                return jsonify({'error': 'Missing data'}), 400

            success = models.save_systems_decision(flag_id, decision, notes)

        elif stage == 'abstract':
            # Abstract stage uses swipe decisions
            if not paper_id or not decision:
                return jsonify({'error': 'Missing data'}), 400

            success = models.save_swipe_decision(current_user.id, paper_id, decision, stage)

        if not success:
            return jsonify({'error': 'Failed to save decision'}), 500

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error saving systems decision: {e}")
        return jsonify({'error': 'Internal server error'}), 500
