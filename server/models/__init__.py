"""
Database Models Package
Exposes all database query functions
"""

from .user import *
from .paper import *
from .swipe import *
from .moderator import *
from .systems import *
from .abstract import *

__all__ = [
    # User functions
    'get_user_by_username',
    'get_user_by_id',
    'create_user',
    'check_invite_code_used',

    # Paper functions
    'get_total_papers',
    'get_paper_by_index',
    'get_paper_by_id',

    # Swipe functions
    'save_swipe_decision',
    'get_user_decision',
    'get_paper_vote_counts',
    'get_user_progress',
    'update_user_progress',
    'get_all_user_progress',

    # Moderator functions
    'get_disputed_papers',
    'save_moderator_decision',
    'get_moderator_stats',

    # Systems functions
    'flag_paper',
    'get_flagged_papers_for_systems',
    'save_systems_decision',
    'get_systems_stats',

    # Abstract stage functions
    'populate_abstract_eligible_papers',
    'get_abstract_stage_status',
]