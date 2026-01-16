"""
Multi-Agent Use Cases View - Refactored using Clean Architecture
"""
from pathlib import Path
from django.shortcuts import render

from ...presentation.dependency_injection import get_container
from ...mock_data import (
    convert_evidences_to_objects,
    convert_reports_to_objects,
    convert_comments_to_objects,
)


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


def multi_agent_use_cases(request):
    """Multi Agent Use Cases page using Clean Architecture"""
    ensure_governance_platform(request)
    
    # Initialize dependency container
    base_dir = Path(__file__).parent.parent.parent.parent
    container = get_container(base_dir)
    
    # Get parameters
    agent_name = request.GET.get('agent', '')
    search_term = request.GET.get('search', '').strip()
    page_number = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))
    use_case_id = request.GET.get('use_case_id', None)
    if use_case_id:
        use_case_id = int(use_case_id)
    
    # Execute use case
    use_cases_data = container.get_multi_agent_use_cases_use_case.execute(
        search_term=search_term,
        agent_name=agent_name if agent_name else None,
        use_case_id=use_case_id,
        page_number=page_number,
        limit=limit,
    )
    
    # Prepare context
    company = MockCompany()
    breadcrumbs = [
        {"name": "Multi Agent Use Cases", "url": request.build_absolute_uri()},
    ]
    
    # Convert page_obj to Django Paginator for template compatibility
    from django.core.paginator import Paginator
    paginator = Paginator(use_cases_data['use_cases_data'], limit)
    page_obj = paginator.get_page(page_number)
    
    # Convert use cases for template compatibility (filtered by agent)
    use_cases_list = []
    for uc_data in use_cases_data['use_cases_data']:
        use_cases_list.append({
            'use_case': uc_data['use_case'],
            'compliance': uc_data['compliance'],
            'risks': uc_data['risks'],
            'models': uc_data['models'],
            'datasets': uc_data['datasets'],
        })
    
    # For converting evidences/reports/comments, we need ALL use cases to find use_case names
    # even if the data is already filtered by agent in the use case
    # Get all use cases from the container to build complete list for conversion
    all_use_cases_list = []
    all_use_cases_repo = container.use_case_repository
    all_use_cases_entities = all_use_cases_repo.get_all()
    
    # Build complete use cases list for conversion (to find use_case names)
    for use_case_entity in all_use_cases_entities:
        all_use_cases_list.append({
            'use_case': use_case_entity,
        })
    
    # Convert evidences, reports, comments to objects for template compatibility
    # Use all_use_cases_list to find use_case names (data is already filtered by agent in use case)
    evidences = convert_evidences_to_objects(use_cases_data['evidences'], all_use_cases_list)
    evaluation_reports = convert_reports_to_objects(use_cases_data['evaluation_reports'], all_use_cases_list)
    review_comments = convert_comments_to_objects(use_cases_data['review_comments'], all_use_cases_list)
    
    # Build reports_dict from converted objects
    reports_dict = {}
    for report in evaluation_reports:
        report_type = getattr(report, 'report_type', None)
        if report_type:
            reports_dict[report_type] = report
    
    # Convert agents for template
    all_agents = []
    for agent in use_cases_data['all_agents']:
        all_agents.append(agent)
    
    # Convert agent to dict for template compatibility
    # If agent is not found but agent_name is provided, try to find it from all_agents
    agent_dict = None
    agent_obj = use_cases_data.get('agent')
    if agent_obj:
        agent_dict = {
            'id': agent_obj.id,
            'name': agent_obj.name,
            'business_unit': agent_obj.business_unit,
            'compliance_status': agent_obj.compliance_status.value if hasattr(agent_obj.compliance_status, 'value') else str(agent_obj.compliance_status),
            'ai_act_role': agent_obj.ai_act_role.value if hasattr(agent_obj.ai_act_role, 'value') else str(agent_obj.ai_act_role),
            'vendor': agent_obj.vendor,
            'risk_classification': agent_obj.risk_classification.value if hasattr(agent_obj.risk_classification, 'value') else str(agent_obj.risk_classification),
            'investment_type': agent_obj.investment_type,
        }
    
    # If still not found and agent_name is provided, try to find from all_agents
    if not agent_dict and agent_name:
        # Use case-insensitive matching to handle URL encoding
        agent_name_lower = agent_name.lower().strip()
        for agent in all_agents:
            if agent.name.lower().strip() == agent_name_lower:
                agent_dict = {
                    'id': agent.id,
                    'name': agent.name,
                    'business_unit': agent.business_unit,
                    'compliance_status': agent.compliance_status.value if hasattr(agent.compliance_status, 'value') else str(agent.compliance_status),
                    'ai_act_role': agent.ai_act_role.value if hasattr(agent.ai_act_role, 'value') else str(agent.ai_act_role),
                    'vendor': agent.vendor,
                    'risk_classification': agent.risk_classification.value if hasattr(agent.risk_classification, 'value') else str(agent.risk_classification),
                    'investment_type': agent.investment_type,
                }
                break
    
    # Re-paginate with converted use cases
    paginator = Paginator(use_cases_list, limit)
    page_obj = paginator.get_page(page_number)
    
    # Debug: Print context values
    print(f"DEBUG: agent_name = {agent_name}")
    print(f"DEBUG: agent_dict = {agent_dict}")
    print(f"DEBUG: selected_use_case = {use_cases_data['selected_use_case']}")
    print(f"DEBUG: evidences count = {len(evidences)}")
    print(f"DEBUG: evaluation_reports count = {len(evaluation_reports)}")
    print(f"DEBUG: review_comments count = {len(review_comments)}")
    print(f"DEBUG: use_cases_list count = {len(use_cases_list)}")
    
    context = {
        "company": company,
        "subpage": "multi_agent_use_cases",
        "breadcrumbs": breadcrumbs,
        "agent_name": use_cases_data.get('agent_name', agent_name),
        "agent": agent_dict,
        "use_cases_data": page_obj.object_list,
        "page_obj": page_obj,
        "search_term": use_cases_data['search_term'],
        "limit": use_cases_data['limit'],
        "all_models": use_cases_data['all_models'],
        "all_datasets": use_cases_data['all_datasets'],
        "all_agents": all_agents,
        "selected_use_case": use_cases_data['selected_use_case'],
        "evidences": evidences,
        "evaluation_reports": evaluation_reports,
        "review_comments": review_comments,
        "report_types": use_cases_data['report_types'],
        "reports_dict": reports_dict,
    }
    
    return render(request, "governance/pages/multiagentusecases.html", context)
