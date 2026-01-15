"""
Presentation Views - Refactored views using Clean Architecture
"""
from .dashboard_view import governance_dashboard, ensure_governance_platform, MockCompany
from .ai_systems_view import ai_systems
from .assessment_view import assessment
from .multi_agent_use_cases_view import multi_agent_use_cases

__all__ = [
    'governance_dashboard',
    'ensure_governance_platform',
    'MockCompany',
    'ai_systems',
    'assessment',
    'multi_agent_use_cases',
]
