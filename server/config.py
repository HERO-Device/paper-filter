"""
Configuration Settings for Paper Filter Application
Loads settings from environment variables
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Server settings
    HOST = os.getenv('SERVER_HOST', '0.0.0.0')
    PORT = int(os.getenv('SERVER_PORT', '5000'))

    # Database settings
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'paper_filter'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'your_password_here')
    }

    # Session settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # Invite codes (for signup)
    INVITE_CODES = {
        # 2 Reviewers
        'HERO-REVIEWER1-2025': {'role': 'reviewer', 'suggested_name': 'Callum'},
        'HERO-REVIEWER2-2025': {'role': 'reviewer', 'suggested_name': 'Rohan'},

        # 1 Moderator
        'HERO-MODERATOR-2025': {'role': 'moderator', 'suggested_name': 'Daniil'},

        # 1 Systems Team
        'HERO-SYSTEMS-2025': {'role': 'systems', 'suggested_name': 'Systems'},

        # 1 Supervisor
        'HERO-SUPERVISOR-2025': {'role': 'supervisor', 'suggested_name': 'Supervisor'},

        # Admin
        'HERO-ADMIN-2025': {'role': 'admin', 'suggested_name': 'Admin'},
    }

    # Consensus threshold (how many "keeps" needed for supervisor view)
    CONSENSUS_THRESHOLD = 2  #Both reviewers must agree

    SYSTEMS_THRESHOLD = 1

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS


# Select config based on environment
config = DevelopmentConfig if os.getenv('FLASK_ENV') == 'development' else ProductionConfig