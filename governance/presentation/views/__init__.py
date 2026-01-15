"""
Presentation Views - Refactored views using Clean Architecture
"""
from .dashboard_view import governance_dashboard, ensure_governance_platform, MockCompany
from .ai_systems_view import ai_systems

__all__ = [
    'governance_dashboard',
    'ensure_governance_platform',
    'MockCompany',
    'ai_systems',
]
