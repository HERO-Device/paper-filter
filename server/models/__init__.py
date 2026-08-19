"""
Database Models Package
Exposes all database query functions.
"""

from ._db import get_db
from .user import (
    get_user_by_username,
    get_user_by_id,
    create_user,
    check_invite_code_used,
)
from .paper import (
    get_total_papers,
    get_paper_by_index,
    get_paper_by_id,
    get_all_papers_with_votes,
)
from .swipe import (
    save_swipe_decision,
    get_user_decision,
    get_paper_vote_counts,
    get_user_progress,
    update_user_progress,
    get_all_user_progress,
    check_title_consensus,
)
from .moderator import (
    get_disputed_papers,
    save_moderator_decision,
    get_moderator_stats,
)
from .systems import (
    flag_paper,
    get_flagged_papers_for_systems,
    save_systems_decision,
    get_systems_stats,
)
from .abstract import (
    populate_abstract_eligible_papers,
    get_abstract_stage_status,
)

__all__ = [
    # Connection
    'get_db',

    # User functions
    'get_user_by_username',
    'get_user_by_id',
    'create_user',
    'check_invite_code_used',

    # Paper functions
    'get_total_papers',
    'get_paper_by_index',
    'get_paper_by_id',
    'get_all_papers_with_votes',

    # Swipe functions
    'save_swipe_decision',
    'get_user_decision',
    'get_paper_vote_counts',
    'get_user_progress',
    'update_user_progress',
    'get_all_user_progress',
    'check_title_consensus',

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
