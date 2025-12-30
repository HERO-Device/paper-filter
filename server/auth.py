"""
Authentication Module
Handles user authentication, login, and session management
"""
from flask import jsonify
from flask_login import LoginManager, UserMixin
import bcrypt
from models import get_user_by_id, get_user_by_username, create_user, check_invite_code_used
from config import config


# ============================================================================
# USER CLASS (Flask-Login)
# ============================================================================

class User(UserMixin):
    """User class for Flask-Login"""

    def __init__(self, id, username, display_name, role):
        self.id = id
        self.username = username
        self.display_name = display_name
        self.role = role

    def is_reviewer(self):
        """Check if user is a reviewer"""
        return self.role == 'reviewer'

    def is_moderator(self):
        """Check if user is a moderator"""
        return self.role == 'moderator'

    def is_systems(self):
        """Check if user is on systems team"""
        return self.role == 'systems'

    def is_supervisor(self):
        """Check if user is a supervisor"""
        return self.role == 'supervisor'

    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin'

# ============================================================================
# FLASK-LOGIN SETUP
# ============================================================================

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """Load user from database by ID (required by Flask-Login)"""
    user_data = get_user_by_id(user_id)

    if user_data:
        return User(
            user_data['id'],
            user_data['username'],
            user_data['display_name'],
            user_data['role']
        )
    return None


# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def authenticate_user(username, password):
    """
    Authenticate user with username and password

    Returns:
        User object if successful, None otherwise
    """
    user_data = get_user_by_username(username.lower())

    if not user_data:
        return None

    # Check password
    if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
        return None

    # Return User object
    return User(
        user_data['id'],
        user_data['username'],
        user_data['display_name'],
        user_data['role']
    )


def register_user(username, password, display_name, invite_code):
    """
    Register a new user

    Returns:
        tuple: (success: bool, message: str, user_id: int or None)
    """
    username = username.lower().strip()

    # Validate invite code
    if invite_code not in config.INVITE_CODES:
        return False, "Invalid invite code", None

    # Check if invite code already used
    if check_invite_code_used(invite_code):
        return False, "Invite code has already been used", None

    # Validate username
    if len(username) < 3:
        return False, "Username must be at least 3 characters", None

    if not username.isalnum():
        return False, "Username must be alphanumeric", None

    # Validate password
    if not password or len(password.strip()) == 0:
        return jsonify({'error' :'Password Required'}), 400

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Get role from invite code
    role = config.INVITE_CODES[invite_code]['role']

    # Create user
    user_id = create_user(username, password_hash, display_name or username, role, invite_code)

    if user_id:
        return True, "Account created successfully", user_id
    else:
        return False, "Username already taken", None


def check_invite_code(invite_code):
    """
    Check if invite code is valid and unused

    Returns:
        dict with role and suggested_name, or None if invalid
    """
    if invite_code not in config.INVITE_CODES:
        return None

    if check_invite_code_used(invite_code):
        return None

    return config.INVITE_CODES[invite_code]
