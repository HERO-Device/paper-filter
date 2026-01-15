"""
Supervisor Routes - View consensus results and export data
Handles both title and abstract stages
"""

from flask import Blueprint, render_template, jsonify, request, Response
from flask_login import login_required, current_user
import models
import csv
import io

supervisor_bp = Blueprint('supervisor', __name__)


@supervisor_bp.route('/supervisor')
@login_required
def supervisor_interface():
    """Render supervisor interface"""
    if not current_user.is_supervisor() and not current_user.is_admin():
        return "Access denied. Supervisors only.", 403

    return render_template('supervisor.html')


@supervisor_bp.route('/api/supervisor/consensus-papers')
@login_required
def get_consensus_papers():
    """Get all consensus papers for a given stage"""
    if not current_user.is_supervisor() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    stage = request.args.get('stage', 'title')

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        conn = models.get_db()
        cursor = conn.cursor(cursor_factory=models.RealDictCursor)

        # Query consensus papers for this stage
        cursor.execute("""
            WITH consensus_papers AS (
                -- Reviewer consensus (2 keeps, not flagged)
                SELECT DISTINCT 
                    p.id,
                    p.title,
                    p.authors,
                    p.year,
                    p.doi,
                    p.source,
                    'Reviewer Consensus (2/2)' as decision_type
                FROM papers p
                WHERE (
                    SELECT COUNT(*) 
                    FROM swipe_decisions sd 
                    WHERE sd.paper_id = p.id 
                    AND sd.decision = 'keep' 
                    AND sd.stage = %s
                ) = 2
                AND NOT EXISTS (
                    SELECT 1 FROM flagged_papers fp WHERE fp.paper_id = p.id
                )
                
                UNION
                
                -- Moderator keeps
                SELECT DISTINCT 
                    p.id,
                    p.title,
                    p.authors,
                    p.year,
                    p.doi,
                    p.source,
                    '⚖️ Moderator Decision' as decision_type
                FROM papers p
                JOIN moderator_decisions md ON p.id = md.paper_id
                WHERE md.decision = 'keep' 
                AND md.stage = %s
                
                UNION
                
                -- Systems keeps (for title stage only)
                SELECT DISTINCT 
                    p.id,
                    p.title,
                    p.authors,
                    p.year,
                    p.doi,
                    p.source,
                    '🔧 Systems Approved' as decision_type
                FROM papers p
                JOIN flagged_papers fp ON p.id = fp.paper_id
                JOIN systems_decisions sd ON sd.flagged_paper_id = fp.id
                WHERE sd.decision = 'keep'
                AND %s = 'title'
            )
            SELECT * FROM consensus_papers
            ORDER BY id
        """, (stage, stage, stage))

        papers = cursor.fetchall()

        # Get progress stats for this stage
        cursor.execute("""
            SELECT COUNT(*) FROM papers
        """)
        total_papers = cursor.fetchone()['count']

        if stage == 'abstract':
            # For abstract stage, total is from abstract_eligible_papers
            cursor.execute("""
                SELECT COUNT(*) FROM abstract_eligible_papers
            """)
            total_papers = cursor.fetchone()['count']

        # Get review completion stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as reviewers,
                AVG(current_paper_index) as avg_progress
            FROM user_progress
            WHERE stage = %s
        """, (stage,))

        progress_stats = cursor.fetchone()

        conn.close()

        return jsonify({
            'papers': papers,
            'stats': {
                'total_papers': total_papers,
                'consensus_count': len(papers),
                'pending': total_papers - len(papers),
                'completion_percentage': (len(papers) / total_papers * 100) if total_papers > 0 else 0,
                'reviewers': progress_stats['reviewers'] if progress_stats else 0,
                'avg_progress': float(progress_stats['avg_progress']) if progress_stats and progress_stats['avg_progress'] else 0
            }
        })

    except Exception as e:
        print(f"Error getting consensus papers: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@supervisor_bp.route('/api/supervisor/stage-status')
@login_required
def get_stage_status():
    """Get status of both title and abstract stages"""
    if not current_user.is_supervisor() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    try:
        # Get abstract stage status
        abstract_status = models.get_abstract_stage_status()

        # Get title stage completion
        conn = models.get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM papers")
        total_title_papers = cursor.fetchone()[0]

        # Count how many papers have been reviewed by both reviewers in title stage
        cursor.execute("""
            SELECT COUNT(DISTINCT paper_id) 
            FROM swipe_decisions 
            WHERE stage = 'title'
            GROUP BY paper_id
            HAVING COUNT(DISTINCT user_id) = 2
        """)
        reviewed_title_papers = len(cursor.fetchall())

        conn.close()

        title_complete = reviewed_title_papers >= total_title_papers

        return jsonify({
            'title_stage': {
                'complete': title_complete,
                'total_papers': total_title_papers,
                'reviewed_papers': reviewed_title_papers,
                'completion_percentage': (reviewed_title_papers / total_title_papers * 100) if total_title_papers > 0 else 0
            },
            'abstract_stage': {
                'initialized': abstract_status['initialized'],
                'total_papers': abstract_status['total_papers'],
                'reviewer_pool': abstract_status['reviewer_pool'],
                'systems_pool': abstract_status['systems_pool']
            }
        })

    except Exception as e:
        print(f"Error getting stage status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@supervisor_bp.route('/api/supervisor/initialize-abstract-stage', methods=['POST'])
@login_required
def initialize_abstract_stage():
    """Initialize abstract stage by populating eligible papers from title stage"""
    if not current_user.is_supervisor() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    try:
        count = models.populate_abstract_eligible_papers()

        return jsonify({
            'success': True,
            'papers_added': count
        })

    except Exception as e:
        print(f"Error initializing abstract stage: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@supervisor_bp.route('/api/supervisor/export-csv')
@login_required
def export_csv():
    """Export consensus papers to CSV"""
    if not current_user.is_supervisor() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    stage = request.args.get('stage', 'title')

    if stage not in ['title', 'abstract']:
        return jsonify({'error': 'Invalid stage'}), 400

    try:
        conn = models.get_db()
        cursor = conn.cursor(cursor_factory=models.RealDictCursor)

        # Same query as get_consensus_papers
        cursor.execute("""
            WITH consensus_papers AS (
                -- Reviewer consensus (2 keeps, not flagged)
                SELECT DISTINCT 
                    p.id,
                    p.title,
                    p.authors,
                    p.year,
                    p.doi,
                    p.source,
                    'Reviewer Consensus (2/2)' as decision_type
                FROM papers p
                WHERE (
                    SELECT COUNT(*) 
                    FROM swipe_decisions sd 
                    WHERE sd.paper_id = p.id 
                    AND sd.decision = 'keep' 
                    AND sd.stage = %s
                ) = 2
                AND NOT EXISTS (
                    SELECT 1 FROM flagged_papers fp WHERE fp.paper_id = p.id
                )
                
                UNION
                
                -- Moderator keeps
                SELECT DISTINCT 
                    p.id,
                    p.title,
                    p.authors,
                    p.year,
                    p.doi,
                    p.source,
                    '⚖️ Moderator Decision' as decision_type
                FROM papers p
                JOIN moderator_decisions md ON p.id = md.paper_id
                WHERE md.decision = 'keep' 
                AND md.stage = %s
                
                UNION
                
                -- Systems keeps (for title stage only)
                SELECT DISTINCT 
                    p.id,
                    p.title,
                    p.authors,
                    p.year,
                    p.doi,
                    p.source,
                    '🔧 Systems Approved' as decision_type
                FROM papers p
                JOIN flagged_papers fp ON p.id = fp.paper_id
                JOIN systems_decisions sd ON sd.flagged_paper_id = fp.id
                WHERE sd.decision = 'keep'
                AND %s = 'title'
            )
            SELECT * FROM consensus_papers
            ORDER BY id
        """, (stage, stage, stage))

        papers = cursor.fetchall()
        conn.close()

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['ID', 'Title', 'Authors', 'Year', 'DOI', 'Source', 'Decision Type', 'Stage'])

        # Write rows
        for paper in papers:
            writer.writerow([
                paper['id'],
                paper['title'],
                paper['authors'],
                paper['year'],
                paper['doi'],
                paper['source'],
                paper['decision_type'],
                stage
            ])

        # Create response
        output.seek(0)
        filename = f'consensus_papers_{stage}_stage.csv'

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

    except Exception as e:
        print(f"Error exporting CSV: {e}")
        return jsonify({'error': 'Internal server error'}), 500
