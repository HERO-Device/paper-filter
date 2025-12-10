"""
Authentication Routes
Handles user login, signup, and logout
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, current_user
from auth import authenticate_user, register_user, check_invite_code
from models import get_user_by_username

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """Landing page - redirect based on auth status"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        data = request.json
        username = data.get('username', '').strip().lower()
        password = data.get('password', '')
        remember = data.get('remember', False)

        # Authenticate
        user = authenticate_user(username, password)

        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401

        # Login user
        login_user(user, remember=remember)

        return jsonify({
            'success': True,
            'message': 'Logged in successfully',
            'redirect': url_for('main.dashboard')
        })

    return render_template('login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page with invite code"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        data = request.json

        invite_code = data.get('invite_code', '').strip()
        username = data.get('username', '').strip().lower()
        password = data.get('password', '')
        display_name = data.get('display_name', '').strip()

        # Register user
        success, message, user_id = register_user(username, password, display_name, invite_code)

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400

    return render_template('signup.html')


@auth_bp.route('/logout')
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/api/user/check-username', methods=['POST'])
def check_username_available():
    """Check if username is available"""
    username = request.json.get('username', '').strip().lower()
    user = get_user_by_username(username)
    return jsonify({'available': user is None})


@auth_bp.route('/api/user/check-invite-code', methods=['POST'])
def check_invite_code_valid():
    """Check if invite code is valid"""
    invite_code = request.json.get('invite_code', '').strip()
    code_info = check_invite_code(invite_code)
    return jsonify({
        'valid': code_info is not None,
        'info': code_info
    })