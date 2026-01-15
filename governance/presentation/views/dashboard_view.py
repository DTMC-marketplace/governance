"""
Dashboard View - Refactored using Clean Architecture
"""
from pathlib import Path
from django.shortcuts import render
from django.utils.translation import gettext as _
from ...presentation.dependency_injection import get_container


def ensure_governance_platform(request):
    """Helper function to ensure request.platform is set to 'governance'"""
    if not hasattr(request, 'platform') or request.platform != 'governance':
        request.platform = 'governance'


class MockCompany:
    """Mock company object"""
    def __init__(self):
        self.id = 1
        self.name = "Demo Company"
        self.storage_name = "demo-company"


def governance_dashboard(request):
    """Governance Dashboard - Main overview page using Clean Architecture"""
    ensure_governance_platform(request)
    
    # Initialize dependency container
    base_dir = Path(__file__).parent.parent.parent.parent
    container = get_container(base_dir)
    
    # Execute use case
    dashboard_dto = container.get_dashboard_data_use_case.execute()
    
    # Prepare context
    company = MockCompany()
    breadcrumbs = [
        {"name": _("Dashboard"), "url": request.build_absolute_uri()},
    ]
    
    # Convert DTO to template context
    context = {
        "company": company,
        "subpage": "dashboard",
        "breadcrumbs": breadcrumbs,
        "use_cases_assessed": dashboard_dto.assessed_use_cases,
        "total_use_cases": dashboard_dto.total_use_cases,
        "under_reviewed": dashboard_dto.under_reviewed,
        "data_collection_completed": dashboard_dto.data_collection_completed,
        "data_collection_progress": {
            "completed": dashboard_dto.data_collection_progress.completed,
            "in_progress": dashboard_dto.data_collection_progress.in_progress,
            "not_started": dashboard_dto.data_collection_progress.not_started,
            "completed_pct": dashboard_dto.data_collection_progress.completed_pct,
            "in_progress_pct": dashboard_dto.data_collection_progress.in_progress_pct,
            "not_started_pct": dashboard_dto.data_collection_progress.not_started_pct,
        },
        "risk_scoring": {
            "ai_risk": dashboard_dto.risk_scoring.ai_risk,
            "data_risk": dashboard_dto.risk_scoring.data_risk,
            "cyber_risk": dashboard_dto.risk_scoring.cyber_risk,
        },
        "reporting_progress": {
            "completed": dashboard_dto.reporting_progress.completed,
            "in_progress": dashboard_dto.reporting_progress.in_progress,
            "not_started": dashboard_dto.reporting_progress.not_started,
            "deprioritized": dashboard_dto.reporting_progress.deprioritized,
            "completed_pct": dashboard_dto.reporting_progress.completed_pct,
            "in_progress_pct": dashboard_dto.reporting_progress.in_progress_pct,
            "not_started_pct": dashboard_dto.reporting_progress.not_started_pct,
            "deprioritized_pct": dashboard_dto.reporting_progress.deprioritized_pct,
        },
        "frameworks_data": {
            key: {
                "completed": value.completed,
                "in_progress": value.in_progress,
                "not_started": value.not_started,
                "deprioritized": value.deprioritized,
            }
            for key, value in dashboard_dto.frameworks_data.items()
        },
    }
    
    return render(request, "governance/pages/dashboard.html", context)
