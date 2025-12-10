"""
Swipe Routes
Handles paper swiping and progress tracking for groupmates
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import (
    get_total_papers,
    get_paper_by_index,
    save_swipe_decision,
    get_user_progress,
    update_user_progress,
    get_all_user_progress
)

swipe_bp = Blueprint('swipe', __name__)


@swipe_bp.route('/api/swipe/get-paper', methods=['GET'])
@login_required
def get_current_paper():
    """Get current paper for user to swipe"""
    if not current_user.is_groupmate():
        return jsonify({'error': 'Only groupmates can swipe'}), 403

    # Get user's progress
    progress = get_user_progress(current_user.id)

    if not progress:
        return jsonify({'error': 'Progress not found'}), 404

    current_index = progress['current_paper_index']
    total_papers = get_total_papers()

    # Check if finished
    if current_index >= total_papers:
        return jsonify({
            'finished': True,
            'message': 'You have reviewed all papers!',
            'stats': {
                'total_kept': progress['total_kept'],
                'total_rejected': progress['total_rejected'],
                'total_reviewed': progress['total_kept'] + progress['total_rejected']
            }
        })

    # Get paper
    paper = get_paper_by_index(current_index)

    if not paper:
        return jsonify({'error': 'Paper not found'}), 404

    return jsonify({
        'finished': False,
        'paper': dict(paper),
        'progress': {
            'current': current_index + 1,
            'total': total_papers,
            'kept': progress['total_kept'],
            'rejected': progress['total_rejected']
        }
    })


@swipe_bp.route('/api/swipe/decision', methods=['POST'])
@login_required
def submit_swipe_decision():
    """Submit swipe decision (keep or reject)"""
    if not current_user.is_groupmate():
        return jsonify({'error': 'Only groupmates can swipe'}), 403

    data = request.json
    paper_id = data.get('paper_id')
    decision = data.get('decision')  # 'keep' or 'reject'

    if decision not in ['keep', 'reject']:
        return jsonify({'error': 'Invalid decision'}), 400

    # Save decision
    success = save_swipe_decision(current_user.id, paper_id, decision)

    if not success:
        return jsonify({'error': 'Failed to save decision'}), 500

    # Update progress
    progress = get_user_progress(current_user.id)
    new_index = progress['current_paper_index'] + 1
    new_kept = progress['total_kept'] + (1 if decision == 'keep' else 0)
    new_rejected = progress['total_rejected'] + (1 if decision == 'reject' else 0)

    update_user_progress(current_user.id, new_index, new_kept, new_rejected)

    return jsonify({
        'success': True,
        'message': 'Decision saved',
        'new_progress': {
            'current': new_index + 1,
            'total': get_total_papers(),
            'kept': new_kept,
            'rejected': new_rejected
        }
    })


@swipe_bp.route('/api/progress/all', methods=['GET'])
@login_required
def get_all_progress():
    """Get progress for all groupmates"""
    progress_list = get_all_user_progress()
    total_papers = get_total_papers()

    return jsonify({
        'total_papers': total_papers,
        'users': [dict(p) for p in progress_list]
    })