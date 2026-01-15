"""
Swipe Routes - Paper review interface for reviewers
Handles getting papers, saving decisions, and flagging
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import models

swipe_bp = Blueprint('swipe', __name__)


@swipe_bp.route('/swipe')
@login_required
def swipe_interface():
    """Render swipe interface for reviewers"""
    if not current_user.is_reviewer():
        return "Access denied. Reviewers only.", 403

    return render_template('swipe.html')


@swipe_bp.route('/api/swipe/get-paper')
@login_required
def get_paper():
    """Get next paper for user to review"""
    if not current_user.is_reviewer():
        return jsonify({'error': 'Access denied'}), 403

    # Get stage from query parameter (default: title)
    stage = request.args.get('stage', 'title')

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        # Get user's progress for this stage
        progress = models.get_user_progress(current_user.id, stage)

        if not progress:
            return jsonify({'error': 'Progress not found'}), 404

        current_index = progress['current_paper_index']
        total_papers = progress['total_papers']

        # Check if user has finished all papers
        if current_index >= total_papers:
            return jsonify({
                'finished': True,
                'stats': {
                    'total_kept': progress['total_kept'],
                    'total_rejected': progress['total_rejected'],
                    'total_papers': total_papers
                }
            })

        # Get the paper at current index
        paper = models.get_paper_by_index(current_index, stage)

        if not paper:
            return jsonify({'error': 'Paper not found'}), 404

        return jsonify({
            'paper': {
                'id': paper['id'],
                'title': paper['title'],
                'authors': paper['authors'],
                'year': paper['year'],
                'doi': paper['doi'],
                'source': paper['source']
            },
            'progress': {
                'current': current_index + 1,
                'total': total_papers,
                'kept': progress['total_kept'],
                'rejected': progress['total_rejected'],
                'percentage': progress['completion_percentage']
            }
        })

    except Exception as e:
        print(f"Error getting paper: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@swipe_bp.route('/api/swipe/decision', methods=['POST'])
@login_required
def save_decision():
    """Save user's swipe decision"""
    if not current_user.is_reviewer():
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    paper_id = data.get('paper_id')
    decision = data.get('decision')  # 'keep' or 'reject'
    stage = data.get('stage', 'title')

    if not paper_id or not decision:
        return jsonify({'error': 'Missing data'}), 400

    if decision not in ['keep', 'reject']:
        return jsonify({'error': 'Invalid decision'}), 400

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        # Save the decision
        success = models.save_swipe_decision(current_user.id, paper_id, decision, stage)

        if not success:
            return jsonify({'error': 'Failed to save decision'}), 500

        # Update progress
        progress = models.get_user_progress(current_user.id, stage)
        new_index = progress['current_paper_index'] + 1
        new_kept = progress['total_kept'] + (1 if decision == 'keep' else 0)
        new_rejected = progress['total_rejected'] + (1 if decision == 'reject' else 0)

        models.update_user_progress(current_user.id, new_index, new_kept, new_rejected, stage)

        return jsonify({
            'success': True,
            'progress': {
                'current': new_index,
                'total': progress['total_papers'],
                'kept': new_kept,
                'rejected': new_rejected
            }
        })

    except Exception as e:
        print(f"Error saving decision: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@swipe_bp.route('/api/swipe/flag', methods=['POST'])
@login_required
def flag_paper():
    """Flag a paper for systems review (TITLE STAGE ONLY)"""
    if not current_user.is_reviewer():
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    paper_id = data.get('paper_id')
    reason = data.get('reason', '')
    stage = data.get('stage', 'title')

    # Flagging only allowed in title stage
    if stage != 'title':
        return jsonify({'error': 'Flagging only allowed in title stage'}), 400

    if not paper_id:
        return jsonify({'error': 'Missing paper_id'}), 400

    try:
        # Flag the paper
        success = models.flag_paper(current_user.id, paper_id, reason)

        if not success:
            return jsonify({'error': 'Failed to flag paper'}), 500

        # Update progress (flagging counts as progressing)
        progress = models.get_user_progress(current_user.id, stage)
        new_index = progress['current_paper_index'] + 1

        models.update_user_progress(current_user.id, new_index, progress['total_kept'], progress['total_rejected'], stage)

        return jsonify({
            'success': True,
            'progress': {
                'current': new_index,
                'total': progress['total_papers'],
                'kept': progress['total_kept'],
                'rejected': progress['total_rejected']
            }
        })

    except Exception as e:
        print(f"Error flagging paper: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@swipe_bp.route('/api/swipe/progress')
@login_required
def get_progress():
    """Get user's current progress"""
    if not current_user.is_reviewer():
        return jsonify({'error': 'Access denied'}), 403

    stage = request.args.get('stage', 'title')

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        progress = models.get_user_progress(current_user.id, stage)

        return jsonify({
            'current_index': progress['current_paper_index'],
            'total_papers': progress['total_papers'],
            'total_kept': progress['total_kept'],
            'total_rejected': progress['total_rejected'],
            'completion_percentage': progress['completion_percentage']
        })

    except Exception as e:
        print(f"Error getting progress: {e}")
        return jsonify({'error': 'Internal server error'}), 500
