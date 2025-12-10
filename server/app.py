"""
Paper Filter - Main Flask Application
H.E.R.O. System Literature Review Tool

Usage:
    python app.py
"""

from flask import Flask, render_template, redirect, url_for, Blueprint
from flask_login import login_required, current_user
from flask_cors import CORS
from auth import login_manager
from config import config

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = config.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = config.SESSION_COOKIE_SAMESITE
app.config['PERMANENT_SESSION_LIFETIME'] = config.PERMANENT_SESSION_LIFETIME

# Enable CORS
CORS(app)

# Initialize Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# ============================================================================
# REGISTER BLUEPRINTS
# ============================================================================

from routes.auth_routes import auth_bp
from routes.swipe_routes import swipe_bp
from routes.admin_routes import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(swipe_bp)
app.register_blueprint(admin_bp)

# ============================================================================
# MAIN APPLICATION ROUTES
# ============================================================================

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - role-based view"""
    if current_user.is_groupmate():
        # Groupmates see swipe interface
        return render_template('swipe.html', user=current_user)
    elif current_user.is_supervisor():
        # Supervisor sees consensus papers
        return render_template('supervisor.html', user=current_user)
    else:
        # Admin sees everything
        return render_template('admin.html', user=current_user)


@main_bp.route('/progress')
@login_required
def progress_page():
    """Group progress dashboard (accessible to all)"""
    return render_template('progress.html', user=current_user)


@main_bp.route('/api/user/me', methods=['GET'])
@login_required
def get_current_user_info():
    """Get current user info"""
    from flask import jsonify
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'display_name': current_user.display_name,
        'role': current_user.role
    })

app.register_blueprint(main_bp)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    from flask import jsonify
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    from flask import jsonify
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("📄 Paper Filter - Flask Application")
    print("=" * 60)
    print(f"Environment: {'Development' if config.DEBUG else 'Production'}")
    print(f"Server: http://{config.HOST}:{config.PORT}")
    print(f"Database: {config.DB_CONFIG['database']} @ {config.DB_CONFIG['host']}")
    print("=" * 60)
    print()

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )