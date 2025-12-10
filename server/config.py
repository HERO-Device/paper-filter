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
        # 8 Groupmates
        'HERO-CALLUM-2025': {'role': 'groupmate', 'suggested_name': 'Callum'},
        'HERO-DANIIL-2025': {'role': 'groupmate', 'suggested_name': 'Daniil'},
        'HERO-DYLAN-2025': {'role': 'groupmate', 'suggested_name': 'Dylan'},
        'HERO-ELLEN-2025': {'role': 'groupmate', 'suggested_name': 'Ellen'},
        'HERO-KOKO-2025': {'role': 'groupmate', 'suggested_name': 'Koko'},
        'HERO-MANQI-2025': {'role': 'groupmate', 'suggested_name': 'Manqi'},
        'HERO-ROHAN-2025': {'role': 'groupmate', 'suggested_name': 'Rohan'},
        'HERO-RATUL-2025': {'role': 'groupmate', 'suggested_name': 'Ratul'},

        # 1 Supervisor
        'HERO-DAVIDE-2025': {'role': 'supervisor', 'suggested_name': 'Davide'},
    }

    # Consensus threshold (how many "keeps" needed for supervisor view)
    CONSENSUS_THRESHOLD = 5  # 5 out of 8 = >50%


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS


# Select config based on environment
config = DevelopmentConfig if os.getenv('FLASK_ENV') == 'development' else ProductionConfig