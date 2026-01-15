"""
AI Systems View - Refactored using Clean Architecture
"""
from pathlib import Path
from django.shortcuts import render
from django.core.paginator import Paginator

from ...presentation.dependency_injection import get_container
from ...domain.services.compliance_service import ComplianceService


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


def ai_systems(request):
    """AI Systems page - List all AI use cases using Clean Architecture"""
    ensure_governance_platform(request)
    
    # Initialize dependency container
    base_dir = Path(__file__).parent.parent.parent.parent
    container = get_container(base_dir)
    
    # Get search term and pagination parameters
    search_term = request.GET.get('search', '').strip()
    page_number = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))
    
    # Get repositories
    agent_repository = container.agent_repository
    use_case_repository = container.use_case_repository
    model_repository = container.model_repository
    dataset_repository = container.dataset_repository
    
    # Get data using repositories
    if search_term:
        agents = agent_repository.search(search_term)
    else:
        agents = agent_repository.get_all()
    
    use_cases = use_case_repository.get_all()
    models = model_repository.get_all()
    datasets = dataset_repository.get_all()
    
    # Build agents data with use cases
    compliance_service = ComplianceService()
    agents_list = []
    
    for agent in agents:
        agent_use_cases = use_case_repository.get_by_agent_id(agent.id)
        
        use_cases_list = []
        for use_case in agent_use_cases:
            compliance = compliance_service.calculate_compliance(use_case)
            risks = compliance_service.calculate_risks(use_case)
            
            # Get models and datasets
            use_case_models = model_repository.get_by_ids(use_case.models)
            use_case_datasets = dataset_repository.get_by_ids(use_case.datasets)
            
            use_cases_list.append({
                'use_case': use_case,
                'compliance': {
                    'status': compliance.status.value,
                    'gdpr': compliance.gdpr,
                    'eu_ai_act': compliance.eu_ai_act,
                    'data_act': compliance.data_act,
                },
                'risks': risks,
                'models': [
                    {'id': m.id, 'name': m.name, 'vendor': m.vendor}
                    for m in use_case_models
                ],
                'datasets': [
                    {'id': d.id, 'name': d.name, 'source': d.source}
                    for d in use_case_datasets
                ],
            })
        
        # Calculate progress
        progress = {
            'models': sum(len(uc.models) for uc in agent_use_cases),
            'datasets': sum(len(uc.datasets) for uc in agent_use_cases),
            'evidences': 0,  # Would need evidence repository
            'reports': 0,  # Would need report repository
        }
        
        agents_list.append({
            'agent': agent,
            'use_cases': use_cases_list,
            'progress': progress,
        })
    
    # Pagination
    paginator = Paginator(agents_list, limit)
    page_obj = paginator.get_page(page_number)
    
    company = MockCompany()
    breadcrumbs = [
        {"name": "AI Systems", "url": request.build_absolute_uri()},
    ]
    
    return render(
        request,
        "governance/pages/ai_systems.html",
        {
            "company": company,
            "subpage": "ai_systems",
            "breadcrumbs": breadcrumbs,
            "agents_data": page_obj.object_list,
            "page_obj": page_obj,
            "search_term": search_term,
            "limit": limit,
            "business_units": [],
        },
    )
