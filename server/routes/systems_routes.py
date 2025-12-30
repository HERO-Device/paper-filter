"""
Systems Routes
Handles API endpoints for systems team to review flagged papers
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    get_flagged_papers_for_systems,
    save_systems_decision,
    get_systems_stats
)

systems_bp = Blueprint('systems', __name__)


@systems_bp.route('/systems')
@login_required
def systems_page():
    """Systems team dashboard page"""
    if not current_user.is_systems():
        return redirect(url_for('main.dashboard'))
    return render_template('systems.html', user=current_user)


@systems_bp.route('/api/systems/flagged-papers', methods=['GET'])
@login_required
def get_flagged_papers_api():
    """Get all flagged papers for systems team"""
    try:
        if not current_user.is_systems():
            return jsonify({'error': 'Systems team access required'}), 403

        print(f"DEBUG: Loading flagged papers for user {current_user.id}")

        papers = get_flagged_papers_for_systems(status='pending')
        print(f"DEBUG: Found {len(papers)} flagged papers")

        stats = get_systems_stats()
        print(f"DEBUG: Stats: {stats}")

        return jsonify({
            'papers': papers,
            'stats': stats
        })

    except Exception as e:
        print(f"ERROR in get_flagged_papers_api: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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

    success = save_systems_decision(flagged_paper_id, decision, notes)

    if not success:
        return jsonify({'error': 'Failed to save decision'}), 500

    return jsonify({
        'success': True,
        'message': 'Decision saved successfully'
    })