"""
Assessment View - Refactored using Clean Architecture
"""
from pathlib import Path
from django.shortcuts import render

from ...presentation.dependency_injection import get_container
from ...constants import VIRTUAL_AGENT
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


def assessment(request):
    """Assessment/Questionnaires page using Clean Architecture"""
    ensure_governance_platform(request)
    
    # Initialize dependency container
    base_dir = Path(__file__).parent.parent.parent.parent
    container = get_container(base_dir)
    
    # Get parameters
    agent_name = request.GET.get('agent', '')
    use_case_id = request.GET.get('use_case_id', None)
    if use_case_id:
        use_case_id = int(use_case_id)
    
    # Execute use case
    assessment_data = container.get_assessment_data_use_case.execute(
        agent_name=agent_name if agent_name else None,
        use_case_id=use_case_id,
    )
    
    # Prepare context
    company = MockCompany()
    breadcrumbs = [
        {"name": "Questionnaires", "url": request.build_absolute_uri()},
    ]
    
    # Get governance agents (first 3)
    governance_agents = VIRTUAL_AGENT[:3]
    
    # Convert domain entities to dict for template compatibility
    all_agents = []
    for agent in assessment_data['all_agents']:
        all_agents.append({
            'id': agent.id,
            'name': agent.name,
            'description': '',  # Agent entity doesn't have description attribute
            'is_virtual': False,
            'get_ai_act_role_display': lambda: "Deployer",
            'get_risk_classification_display': lambda: "Limited Risks",
        })
    
    # Convert use cases for template
    use_cases_list = []
    for uc_data in assessment_data['use_cases_data']:
        use_case = uc_data['use_case']
        use_cases_list.append({
            'use_case': use_case,
            'compliance': uc_data['compliance'],
            'risks': uc_data['risks'],
            'models': uc_data['models'],
            'datasets': uc_data['datasets'],
        })
    
    # Convert agent to dict for template compatibility
    agent_dict = None
    agent_obj = assessment_data.get('agent')
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
    elif agent_name:
        # Try to find agent from all_agents if not found in use case
        for agent in assessment_data['all_agents']:
            if agent.name == agent_name:
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
    
    # Convert evidences, reports, comments to objects for template compatibility
    evidences = convert_evidences_to_objects(assessment_data['evidences'], use_cases_list)
    evaluation_reports = convert_reports_to_objects(assessment_data['evaluation_reports'], use_cases_list)
    review_comments = convert_comments_to_objects(assessment_data['review_comments'], use_cases_list)
    
    # Build reports_dict from converted objects
    reports_dict = {}
    for report in evaluation_reports:
        report_type = getattr(report, 'report_type', None)
        if report_type:
            reports_dict[report_type] = report
    
    context = {
        "company": company,
        "subpage": "risk_assessment",
        "breadcrumbs": breadcrumbs,
        "agent_name": assessment_data['agent_name'],
        "agent": agent_dict,
        "use_cases_data": use_cases_list,
        "all_agents": all_agents,
        "selected_use_case": assessment_data['selected_use_case'],
        "evidences": evidences,
        "evaluation_reports": evaluation_reports,
        "review_comments": review_comments,
        "report_types": assessment_data['report_types'],
        "reports_dict": reports_dict,
    }
    
    return render(request, "governance/pages/assessment.html", context)
