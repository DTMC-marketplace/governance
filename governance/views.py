"""
Governance Platform Views - Refactored with Clean Architecture
Using Clean Architecture patterns: Domain, Application, Infrastructure, Presentation layers

Note: This file maintains backward compatibility. New views using Clean Architecture
are in governance/presentation/views/
"""
import os
import tempfile
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

# Try to import Clean Architecture views (will override legacy functions below)
try:
    from .presentation.views import (
        governance_dashboard as ca_governance_dashboard,
        ensure_governance_platform as ca_ensure_governance_platform,
        MockCompany as CA_MockCompany,
        ai_systems as ca_ai_systems,
        assessment as ca_assessment,
        multi_agent_use_cases as ca_multi_agent_use_cases,
    )
    USE_CLEAN_ARCHITECTURE = True
except ImportError:
    USE_CLEAN_ARCHITECTURE = False

# Import AI Act Chat API view
from .presentation.views.ai_act_chat_view import ai_act_chat_api

from .mock_data import (
    get_mock_agents, get_mock_use_cases, get_mock_models, get_mock_datasets,
    get_mock_evidences, get_mock_evaluation_reports, get_mock_review_comments,
    create_mock_agent, create_mock_use_case, calculate_compliance_mock, calculate_risks_mock,
    MockObject, convert_evidences_to_objects, convert_reports_to_objects, convert_comments_to_objects
)
from .constants import VIRTUAL_AGENT


# Use Clean Architecture implementations if available, otherwise use legacy
if USE_CLEAN_ARCHITECTURE:
    ensure_governance_platform = ca_ensure_governance_platform
    MockCompany = CA_MockCompany
    governance_dashboard = ca_governance_dashboard
    ai_systems = ca_ai_systems
    assessment = ca_assessment
    multi_agent_use_cases = ca_multi_agent_use_cases
else:
    def ensure_governance_platform(request):
        """Helper function to ensure request.platform is set to 'governance'"""
        if not hasattr(request, 'platform') or request.platform != 'governance':
            request.platform = 'governance'
    
    # Mock company object
    class MockCompany:
        def __init__(self):
            self.id = 1
            self.name = "Demo Company"
            self.storage_name = "demo-company"
    
    def governance_dashboard(request):
        """Governance Dashboard - Main overview page"""
        ensure_governance_platform(request)
        
        company = MockCompany()
        breadcrumbs = [
            {"name": "Dashboard", "url": request.build_absolute_uri()},
        ]
        
        # Get all use cases from mock data
        all_use_cases_data = get_mock_use_cases()
        all_use_cases = [create_mock_use_case(uc) for uc in all_use_cases_data]
        total_use_cases = len(all_use_cases)
        assessed_use_cases = sum(1 for uc in all_use_cases if uc.compliance_assessed)
        
        # Under reviewed: use cases with review_status='partial' or 'complete'
        under_reviewed = sum(1 for uc in all_use_cases if uc.review_status in ['partial', 'complete'])
        
        # Get agents to check compliance_status
        agents_data = get_mock_agents()
        under_reviewed += sum(1 for agent in agents_data if agent.get('compliance_status') == 'reviewing')
        
        # Data Collection Completed: count of evidences and evaluation reports
        evidences = get_mock_evidences()
        evaluation_reports = get_mock_evaluation_reports()
        data_collection_completed = len(evidences) + len(evaluation_reports)
        
        # Data Collection Progress
        completed_use_cases = 0
        in_progress_use_cases = 0
        not_started_use_cases = 0
        
        for use_case in all_use_cases:
            has_models = len(use_case.models) > 0
            has_datasets = len(use_case.datasets) > 0
            use_case_id = use_case.id
            has_evidences = any(e.get('use_case_id') == use_case_id for e in evidences)
            has_reports = any(r.get('use_case_id') == use_case_id for r in evaluation_reports)
            
            if has_models and has_datasets and has_evidences and has_reports and use_case.compliance_assessed:
                completed_use_cases += 1
            elif has_models or has_datasets or has_evidences or has_reports:
                in_progress_use_cases += 1
            else:
                not_started_use_cases += 1
        
        total_progress = completed_use_cases + in_progress_use_cases + not_started_use_cases
        if total_progress > 0:
            completed_pct = round((completed_use_cases / total_progress) * 100)
            in_progress_pct = round((in_progress_use_cases / total_progress) * 100)
            not_started_pct = round((not_started_use_cases / total_progress) * 100)
        else:
            completed_pct = 0
            in_progress_pct = 0
            not_started_pct = 0
        
        # Risk Scoring - Calculate average risk scores
        ai_risks_map = {'high_risks': 4, 'limited_risks': 2.5, 'minimal_risks': 1.5}
        agents_data = get_mock_agents()
        ai_risk_scores = [ai_risks_map.get(agent.get('risk_classification', 'limited_risks'), 2.5) for agent in agents_data]
        avg_ai_risk = sum(ai_risk_scores) / len(ai_risk_scores) if ai_risk_scores else 2.5
        avg_ai_risk = max(1.0, min(4.0, avg_ai_risk))
        
        # Data Risks: based on GDPR compliance of use cases
        data_risk_scores = []
        for use_case in all_use_cases:
            compliance = calculate_compliance_mock(use_case)
            if not compliance.get('gdpr', False):
                data_risk_scores.append(3.5)
            elif compliance.get('status') == 'partial':
                data_risk_scores.append(2.5)
            else:
                data_risk_scores.append(1.5)
        avg_data_risk = sum(data_risk_scores) / len(data_risk_scores) if data_risk_scores else 2.5
        avg_data_risk = max(1.0, min(4.0, avg_data_risk))
        
        # Cyber Risks: based on data_act compliance
        cyber_risk_scores = []
        for use_case in all_use_cases:
            compliance = calculate_compliance_mock(use_case)
            if not compliance.get('data_act', False):
                cyber_risk_scores.append(3.0)
            else:
                cyber_risk_scores.append(2.0)
        avg_cyber_risk = sum(cyber_risk_scores) / len(cyber_risk_scores) if cyber_risk_scores else 2.5
        avg_cyber_risk = max(1.0, min(4.0, avg_cyber_risk))
        
        # Reporting Progress
        reporting_completed = 0
        reporting_in_progress = 0
        reporting_not_started = 0
        reporting_deprioritized = 0
        
        for use_case in all_use_cases:
            compliance = calculate_compliance_mock(use_case)
            if compliance.get('status') == 'compliant' and use_case.compliance_assessed:
                reporting_completed += 1
            elif compliance.get('status') == 'partial' or (use_case.compliance_assessed and compliance.get('status') != 'compliant'):
                reporting_in_progress += 1
            elif not use_case.compliance_assessed:
                reporting_not_started += 1
            else:
                reporting_deprioritized += 1
        
        total_reporting = reporting_completed + reporting_in_progress + reporting_not_started + reporting_deprioritized
        if total_reporting > 0:
            reporting_completed_pct = round((reporting_completed / total_reporting) * 100)
            reporting_in_progress_pct = round((reporting_in_progress / total_reporting) * 100)
            reporting_not_started_pct = round((reporting_not_started / total_reporting) * 100)
            reporting_deprioritized_pct = round((reporting_deprioritized / total_reporting) * 100)
        else:
            reporting_completed_pct = 0
            reporting_in_progress_pct = 0
            reporting_not_started_pct = 0
            reporting_deprioritized_pct = 0
        
        # Progress By Framework
        frameworks_data = {
            'GDPR': {'completed': 0, 'in_progress': 0, 'not_started': 0, 'deprioritized': 0},
            'EU_AI_Act': {'completed': 0, 'in_progress': 0, 'not_started': 0, 'deprioritized': 0},
            'DSA': {'completed': 0, 'in_progress': 0, 'not_started': 0, 'deprioritized': 0},
            'Data_Act': {'completed': 0, 'in_progress': 0, 'not_started': 0, 'deprioritized': 0},
        }
        
        for use_case in all_use_cases:
            compliance = calculate_compliance_mock(use_case)
            
            # GDPR
            if compliance.get('gdpr', False) and use_case.compliance_assessed:
                frameworks_data['GDPR']['completed'] += 1
            elif use_case.compliance_assessed:
                frameworks_data['GDPR']['in_progress'] += 1
            elif not use_case.compliance_assessed:
                frameworks_data['GDPR']['not_started'] += 1
            
            # EU AI Act
            if compliance.get('eu_ai_act', False) and use_case.compliance_assessed:
                frameworks_data['EU_AI_Act']['completed'] += 1
            elif use_case.compliance_assessed:
                frameworks_data['EU_AI_Act']['in_progress'] += 1
            elif not use_case.compliance_assessed:
                frameworks_data['EU_AI_Act']['not_started'] += 1
            
            # Data Act
            if compliance.get('data_act', False) and use_case.compliance_assessed:
                frameworks_data['Data_Act']['completed'] += 1
            elif use_case.compliance_assessed:
                frameworks_data['Data_Act']['in_progress'] += 1
            elif not use_case.compliance_assessed:
                frameworks_data['Data_Act']['not_started'] += 1
            
            # DSA (placeholder)
            frameworks_data['DSA']['not_started'] += 1
        
        return render(
            request,
            "governance/pages/dashboard.html",
            {
                "company": company,
                "subpage": "dashboard",
                "breadcrumbs": breadcrumbs,
                "use_cases_assessed": assessed_use_cases,
                "total_use_cases": total_use_cases,
                "under_reviewed": under_reviewed,
                "data_collection_completed": data_collection_completed,
                "data_collection_progress": {
                    "completed": completed_use_cases,
                    "in_progress": in_progress_use_cases,
                    "not_started": not_started_use_cases,
                    "completed_pct": completed_pct,
                    "in_progress_pct": in_progress_pct,
                    "not_started_pct": not_started_pct,
                },
                "risk_scoring": {
                    "ai_risk": round(avg_ai_risk, 1),
                    "data_risk": round(avg_data_risk, 1),
                    "cyber_risk": round(avg_cyber_risk, 1),
                },
                "reporting_progress": {
                    "completed": reporting_completed,
                    "in_progress": reporting_in_progress,
                    "not_started": reporting_not_started,
                    "deprioritized": reporting_deprioritized,
                    "completed_pct": reporting_completed_pct,
                    "in_progress_pct": reporting_in_progress_pct,
                    "not_started_pct": reporting_not_started_pct,
                    "deprioritized_pct": reporting_deprioritized_pct,
                },
                "frameworks_data": frameworks_data,
            },
        )


# ai_systems is now using Clean Architecture from presentation.views.ai_systems_view
# If Clean Architecture import failed, define legacy version below
if not USE_CLEAN_ARCHITECTURE:
    def ai_systems(request):
        """AI Systems page - Legacy implementation using mock data"""
        ensure_governance_platform(request)
        
        company = MockCompany()
        breadcrumbs = [
            {"name": "AI Systems", "url": request.build_absolute_uri()},
        ]
        
        # Get mock data
        agents_data = get_mock_agents()
        use_cases_data = get_mock_use_cases()
        models_data = get_mock_models()
        datasets_data = get_mock_datasets()
        
        # Build agents data with use cases
        agents_list = []
        for agent_data in agents_data:
            agent_use_cases = [uc for uc in use_cases_data if uc.get('agent_id') == agent_data.get('id')]
            
            use_cases_list = []
            for uc_data in agent_use_cases:
                use_case = create_mock_use_case(uc_data)
                compliance = calculate_compliance_mock(use_case)
                risks = calculate_risks_mock(use_case)
                
                # Get models and datasets
                use_case_models = [m for m in models_data if m.get('id') in use_case.models]
                use_case_datasets = [d for d in datasets_data if d.get('id') in use_case.datasets]
                
                use_cases_list.append({
                    'use_case': use_case,
                    'compliance': compliance,
                    'risks': risks,
                    'models': [
                        {'id': m.get('id'), 'name': m.get('name'), 'vendor': m.get('vendor')}
                        for m in use_case_models
                    ],
                    'datasets': [
                        {'id': d.get('id'), 'name': d.get('name'), 'source': d.get('source')}
                        for d in use_case_datasets
                    ],
                })
            
            # Calculate progress
            total_models = sum(len(uc.get('models', [])) for uc in agent_use_cases)
            total_datasets = sum(len(uc.get('datasets', [])) for uc in agent_use_cases)
            total_evidences = 0
            total_reports = 0
            
            # Data collection progress: total = 8 (models + datasets + evidences + reports + other fields)
            completed = min(total_models + total_datasets + total_evidences + total_reports, 8)
            total = 8
            percentage = int((completed / total) * 100) if total > 0 else 0
            
            progress = {
                'models': total_models,
                'datasets': total_datasets,
                'evidences': total_evidences,
                'reports': total_reports,
                'completed': completed,
                'total': total,
                'percentage': percentage,
            }
            
            # Create mock agent object
            class MockAgent:
                def __init__(self, data):
                    self.id = data.get('id')
                    self.name = data.get('name', '')
                    self.description = data.get('description', '')
                    self.compliance_status = data.get('compliance_status', 'assessing')
                    self.ai_act_role = data.get('ai_act_role', 'deployer')
                    self.vendor = data.get('vendor', '')
                    self.risk_classification = data.get('risk_classification', 'limited_risks')
                    self.business_unit = data.get('business_unit', '')
                    
                def get_ai_act_role_display(self):
                    role_map = {
                        'deployer': 'Deployer',
                        'provider': 'Provider',
                        'importer': 'Importer',
                        'distributor': 'Distributor',
                    }
                    return role_map.get(self.ai_act_role, self.ai_act_role.title())
            
            agents_list.append({
                'agent': MockAgent(agent_data),
                'use_cases': use_cases_list,
                'progress': progress,
            })
        
        return render(
            request,
            "governance/pages/ai_systems.html",
            {
                "company": company,
                "subpage": "ai_systems",
                "breadcrumbs": breadcrumbs,
                "agents_data": agents_list,
                "page_obj": None,  # No pagination in legacy version
                "search_term": "",
                "limit": 10,
                "business_units": [],
            },
        )


def ai_models(request):
    """AI Models page"""
    company = MockCompany()
    breadcrumbs = [
        {"name": "AI Models", "url": request.build_absolute_uri()},
    ]
    
    return render(
        request,
        "governance/pages/ai_models.html",
        {
            "company": company,
            "subpage": "ai_models",
            "breadcrumbs": breadcrumbs,
        },
    )


def ai_assistant(request, id=None):
    """AI Assistant page"""
    ensure_governance_platform(request)
    company = MockCompany()
    
    # If id is provided, show chat interface
    if id:
        selected_agent = None
        for agent in VIRTUAL_AGENT:
            if agent["id"] == id:
                selected_agent = agent
                break
        
        if not selected_agent:
            from django.shortcuts import redirect
            return redirect("ai_assistant")
        
        # Mock chat histories
        chat_histories = []
        
        breadcrumbs = [
            {"name": "AI Assistant", "url": "/ai-assistant/"},
            {"name": f"Chat with {selected_agent.get('name', 'Unknown Agent')}", "url": request.build_absolute_uri()},
        ]
        
        return render(
            request,
            "governance/pages/ai_assistant_chat.html",
            {
                "company": company,
                "back": "/ai-assistant/",
                "subpage": "ai_assistant",
                "virtualAgent": VIRTUAL_AGENT,
                "selected_agent": selected_agent,
                "agent_chat_type": selected_agent.get("chat_type", "Company"),
                "chat_histories": chat_histories,
                "breadcrumbs": breadcrumbs,
            },
        )
    
    # Otherwise, show agent list page
    breadcrumbs = [
        {"name": "AI Assistant", "url": request.build_absolute_uri()},
    ]
    
    categories = list({agent["category"] for agent in VIRTUAL_AGENT})
    categories.sort()
    
    # Add implementation status
    implemented_agents = ["agent_ai_act"]
    virtual_agents_with_status = []
    for agent in VIRTUAL_AGENT:
        agent_copy = agent.copy()
        agent_copy["is_implemented"] = agent["id"] in implemented_agents
        virtual_agents_with_status.append(agent_copy)
    
    return render(
        request,
        "governance/pages/ai_assistant.html",
        {
            "company": company,
            "subpage": "ai_assistant",
            "breadcrumbs": breadcrumbs,
            "virtualAgent": virtual_agents_with_status,
            "categories": categories,
            "is_demo_user": True,  # Always demo for hackathon
        },
    )


# assessment is now using Clean Architecture from presentation.views.assessment_view
# If Clean Architecture import failed, define legacy version below
if not USE_CLEAN_ARCHITECTURE:
    def assessment(request):
        """Assessment/Questionnaires page - Legacy implementation"""
        ensure_governance_platform(request)
        company = MockCompany()
        agent_name = request.GET.get('agent', '')
        use_case_id = request.GET.get('use_case_id', None)
        breadcrumbs = [
            {"name": "Questionnaires", "url": request.build_absolute_uri()},
        ]
        
        # Get governance agents (first 3)
        governance_agents = VIRTUAL_AGENT[:3]
        
        # Get agents and use cases
        agents_data = get_mock_agents()
        use_cases_data = get_mock_use_cases()
        models_data = get_mock_models()
        datasets_data = get_mock_datasets()
        
        # Filter by agent if provided
        agent = None
        if agent_name:
            agent = next((a for a in agents_data if a.get('name') == agent_name), None)
        
        # Get use cases
        if agent_name and agent:
            use_cases_data = [uc for uc in use_cases_data if uc.get('agent_id') == agent.get('id')]
        else:
            use_cases_data = use_cases_data
        
        # Build use cases data
        use_cases_list = []
        for uc_data in use_cases_data:
            use_case = create_mock_use_case(uc_data)
            compliance = calculate_compliance_mock(use_case)
            risks = calculate_risks_mock(use_case)
            
            models = [m for m in models_data if m.get('id') in uc_data.get('models', [])]
            datasets = [d for d in datasets_data if d.get('id') in uc_data.get('datasets', [])]
            
            use_cases_list.append({
                'use_case': use_case,
                'compliance': compliance,
                'risks': risks,
                'models': models,
                'datasets': datasets,
            })
        
        # Get selected use case
        selected_use_case = None
        if use_case_id:
            selected_use_case = next((uc for uc in use_cases_list if uc['use_case'].id == int(use_case_id)), None)
            if selected_use_case:
                selected_use_case = selected_use_case['use_case']
        
        # Get evidences, reports, comments
        evidences_data = get_mock_evidences()
        evaluation_reports_data = get_mock_evaluation_reports()
        review_comments_data = get_mock_review_comments()
        
        if selected_use_case:
            evidences_data = [e for e in evidences_data if e.get('use_case_id') == selected_use_case.id]
            evaluation_reports_data = [r for r in evaluation_reports_data if r.get('use_case_id') == selected_use_case.id]
            review_comments_data = [c for c in review_comments_data if c.get('use_case_id') == selected_use_case.id]
        
        # Convert to objects with proper attributes
        evidences = convert_evidences_to_objects(evidences_data, use_cases_list)
        evaluation_reports = convert_reports_to_objects(evaluation_reports_data, use_cases_list)
        review_comments = convert_comments_to_objects(review_comments_data)
        
        report_types = [
            ('dataset_evaluation', 'Dataset evaluations'),
            ('model_evaluation', 'Models evaluations'),
            ('secondary', 'Secondary'),
            ('red_teaming_1', 'Red Teaming report'),
            ('red_teaming_4', 'Red Teaming report 4'),
            ('red_teaming_5', 'Red Teaming report 5'),
            ('red_teaming_6', 'Red Teaming report 6'),
            ('red_teaming_7', 'Red Teaming report 7'),
        ]
        
        reports_dict = {}
        for report in evaluation_reports:
            report_type = getattr(report, 'report_type', None)
            if report_type:
                reports_dict[report_type] = report
        
        # Create mock agent objects for template
        all_agents = []
        for agent_data in agents_data:
            class MockAgent:
                def __init__(self, data):
                    self.id = data.get('id')
                    self.name = data.get('name', '')
                    self.description = data.get('description', '')
                    self.is_virtual = False
                
                def get_ai_act_role_display(self):
                    return "Deployer"
                
                def get_risk_classification_display(self):
                    return "Limited Risks"
            
            all_agents.append(MockAgent(agent_data))
        
        return render(
            request,
            "governance/pages/assessment.html",
            {
                "company": company,
                "subpage": "risk_assessment",
                "breadcrumbs": breadcrumbs,
                "agent_name": agent_name,
                "agent": agent,
                "use_cases_data": use_cases_list,
                "all_agents": all_agents,
                "selected_use_case": selected_use_case,
                "evidences": evidences,
                "evaluation_reports": evaluation_reports,
                "review_comments": review_comments,
                "report_types": report_types,
                "reports_dict": reports_dict,
            },
        )


# Placeholder views for other pages
def ai_assistant_chat(request):
    """AI Assistant Chat API - placeholder"""
    return JsonResponse({'success': False, 'error': 'Not implemented in demo'}, status=501)


def assessment_library(request):
    """Assessment Library page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Assessment Library", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/assessment_library.html", {
        "company": company,
        "subpage": "assessment_library",
        "breadcrumbs": breadcrumbs,
    })


def assessment_detail(request, assessment_id):
    """Assessment Detail page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Assessment Detail", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/assessment_detail.html", {
        "company": company,
        "subpage": "assessment_detail",
        "breadcrumbs": breadcrumbs,
        "assessment_id": assessment_id,
    })


def questionnaire_library(request):
    """Questionnaire Library page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Questionnaire Library", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/questionnaire_library.html", {
        "company": company,
        "subpage": "data_collection",
        "breadcrumbs": breadcrumbs,
    })


def questionnaire_detail(request, questionnaire_id):
    """Questionnaire Detail page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Questionnaire Detail", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/questionnaire_detail.html", {
        "company": company,
        "subpage": "questionnaire_detail",
        "breadcrumbs": breadcrumbs,
        "questionnaire_id": questionnaire_id,
    })


def datasets(request):
    """Datasets page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Datasets", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/datasets.html", {
        "company": company,
        "subpage": "datasets",
        "breadcrumbs": breadcrumbs,
    })


def vendors(request):
    """Vendors page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Vendors", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/vendors.html", {
        "company": company,
        "subpage": "vendors",
        "breadcrumbs": breadcrumbs,
    })


def investment(request):
    """Investment page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Investment", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/investment.html", {
        "company": company,
        "subpage": "investment",
        "breadcrumbs": breadcrumbs,
    })


def framework(request):
    """Framework/Reporting page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Framework", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/framework.html", {
        "company": company,
        "subpage": "regulations",
        "breadcrumbs": breadcrumbs,
    })


def digital_regulations(request):
    """Digital Regulations page"""
    company = MockCompany()
    agent_name = request.GET.get('agent', '')
    breadcrumbs = [{"name": "Digital Regulations", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/digital_regulations.html", {
        "company": company,
        "subpage": "digital_regulations",
        "breadcrumbs": breadcrumbs,
        "agent_name": agent_name,
    })


# multi_agent_use_cases is now using Clean Architecture from presentation.views.multi_agent_use_cases_view
# If Clean Architecture import failed, define legacy version below
if not USE_CLEAN_ARCHITECTURE:
    def multi_agent_use_cases(request):
        """Multi Agent Use Cases page - Legacy implementation"""
        ensure_governance_platform(request)
        company = MockCompany()
        agent_name = request.GET.get('agent', '')
        search_term = request.GET.get('search', '').strip()
        page_number = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        
        breadcrumbs = [{"name": "Multi Agent Use Cases", "url": request.build_absolute_uri()}]
        
        # Similar to ai_systems but for use cases
        use_cases_data = get_mock_use_cases()
        models_data = get_mock_models()
        datasets_data = get_mock_datasets()
        agents_data = get_mock_agents()
        
        if search_term:
            use_cases_data = [uc for uc in use_cases_data if search_term.lower() in uc.get('name', '').lower()]
        
        use_cases_list = []
        for uc_data in use_cases_data:
            use_case = create_mock_use_case(uc_data)
            
            # Find and assign agent to use_case
            agent_id = uc_data.get('agent_id')
            if agent_id:
                agent_data = next((a for a in agents_data if a.get('id') == agent_id), None)
                if agent_data:
                    use_case.agent = create_mock_agent(agent_data)
                else:
                    # Create a default agent if not found
                    use_case.agent = MockObject(id=agent_id, name="Unknown Agent")
            else:
                use_case.agent = MockObject(id=None, name="No Agent")
            
            compliance = calculate_compliance_mock(use_case)
            risks = calculate_risks_mock(use_case)
            
            models = [m for m in models_data if m.get('id') in uc_data.get('models', [])]
            datasets = [d for d in datasets_data if d.get('id') in uc_data.get('datasets', [])]
            
            use_cases_list.append({
                'use_case': use_case,
                'compliance': compliance,
                'risks': risks,
                'models': models,
                'datasets': datasets,
            })
        
        from django.core.paginator import Paginator
        paginator = Paginator(use_cases_list, limit)
        page_obj = paginator.get_page(page_number)
        
        use_case_id = request.GET.get('use_case_id', None)
        selected_use_case = None
        if use_case_id:
            selected_use_case = next((uc for uc in use_cases_list if uc['use_case'].id == int(use_case_id)), None)
            if selected_use_case:
                selected_use_case = selected_use_case['use_case']
        
        evidences_data = get_mock_evidences()
        evaluation_reports_data = get_mock_evaluation_reports()
        review_comments_data = get_mock_review_comments()
        
        if selected_use_case:
            evidences_data = [e for e in evidences_data if e.get('use_case_id') == selected_use_case.id]
            evaluation_reports_data = [r for r in evaluation_reports_data if r.get('use_case_id') == selected_use_case.id]
            review_comments_data = [c for c in review_comments_data if c.get('use_case_id') == selected_use_case.id]
        
        # Convert to objects with proper attributes
        evidences = convert_evidences_to_objects(evidences_data, use_cases_list)
        evaluation_reports = convert_reports_to_objects(evaluation_reports_data, use_cases_list)
        review_comments = convert_comments_to_objects(review_comments_data)
        
        report_types = [
            ('dataset_evaluation', 'Dataset evaluations'),
            ('model_evaluation', 'Models evaluations'),
            ('secondary', 'Secondary'),
            ('red_teaming_1', 'Red Teaming report'),
            ('red_teaming_4', 'Red Teaming report 4'),
            ('red_teaming_5', 'Red Teaming report 5'),
            ('red_teaming_6', 'Red Teaming report 6'),
            ('red_teaming_7', 'Red Teaming report 7'),
        ]
        
        reports_dict = {}
        for report in evaluation_reports:
            report_type = getattr(report, 'report_type', None)
            if report_type:
                reports_dict[report_type] = report
        
        return render(request, "governance/pages/multiagentusecases.html", {
            "company": company,
            "subpage": "multi_agent_use_cases",
            "breadcrumbs": breadcrumbs,
            "agent_name": agent_name,
            "agent": None,
            "use_cases_data": page_obj.object_list,
            "page_obj": page_obj,
            "search_term": search_term,
            "limit": limit,
            "all_models": models_data,
            "all_datasets": datasets_data,
            "all_agents": [create_mock_agent(a) for a in get_mock_agents()],
            "selected_use_case": selected_use_case,
            "evidences": evidences,
            "evaluation_reports": evaluation_reports,
            "review_comments": review_comments,
            "report_types": report_types,
            "reports_dict": reports_dict,
        })


def agent_creation(request):
    """Agent Creation page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Agent Creation", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/agent_creation.html", {
        "company": company,
        "subpage": "agent_creation",
        "breadcrumbs": breadcrumbs,
    })


def questionnaire_response(request):
    """Questionnaire Response list page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Questionnaire Responses", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/questionnaire_response.html", {
        "company": company,
        "subpage": "questionnaire_response",
        "breadcrumbs": breadcrumbs,
    })


def questionnaire_response_detail(request, response_id):
    """Questionnaire Response Detail page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Questionnaire Response Detail", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/questionnaire_response_detail.html", {
        "company": company,
        "subpage": "questionnaire_response_detail",
        "breadcrumbs": breadcrumbs,
        "response_id": response_id,
    })


def assessment_response(request):
    """Assessment Response list page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Assessment Responses", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/assessment_response.html", {
        "company": company,
        "subpage": "assessment_response",
        "breadcrumbs": breadcrumbs,
    })


def assessment_response_detail(request, response_id):
    """Assessment Response Detail page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Assessment Response Detail", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/assessment_response_detail.html", {
        "company": company,
        "subpage": "assessment_response_detail",
        "breadcrumbs": breadcrumbs,
        "response_id": response_id,
    })


# EU Act pages
def eu_act_gpihr(request):
    """EU Act GPIHR page"""
    company = MockCompany()
    breadcrumbs = [{"name": "EU Act GPIHR", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/euactGPIHR.html", {
        "company": company,
        "subpage": "eu_act_gpihr",
        "breadcrumbs": breadcrumbs,
    })


def eu_act_gpilr(request):
    """EU Act GPILR page"""
    company = MockCompany()
    breadcrumbs = [{"name": "EU Act GPILR", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/euactGPILR.html", {
        "company": company,
        "subpage": "eu_act_gpilr",
        "breadcrumbs": breadcrumbs,
    })


def eu_act_hr(request):
    """EU Act HR page"""
    company = MockCompany()
    agent_name = request.GET.get('agent', '')
    breadcrumbs = [{"name": "EU Act HR", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/euactHR.html", {
        "company": company,
        "subpage": "eu_act_hr",
        "breadcrumbs": breadcrumbs,
        "agent_name": agent_name,
    })


def eu_act_lr(request):
    """EU Act LR page"""
    company = MockCompany()
    breadcrumbs = [{"name": "EU Act LR", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/euactLR.html", {
        "company": company,
        "subpage": "eu_act_lr",
        "breadcrumbs": breadcrumbs,
    })


def eu_ai_act_framework(request):
    """EU AI Act Framework page"""
    company = MockCompany()
    breadcrumbs = [{"name": "EU AI Act Framework", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/euaiactframework.html", {
        "company": company,
        "subpage": "eu_ai_act_framework",
        "breadcrumbs": breadcrumbs,
    })


def main_eu_act_gpihr(request):
    """Main EU Act GPIHR page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Main EU Act GPIHR", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/main_euactgpihr.html", {
        "company": company,
        "subpage": "main_eu_act_gpihr",
        "breadcrumbs": breadcrumbs,
    })


def main_eu_act_gpilr(request):
    """Main EU Act GPILR page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Main EU Act GPILR", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/main_euactgpilr.html", {
        "company": company,
        "subpage": "main_eu_act_gpilr",
        "breadcrumbs": breadcrumbs,
    })


def main_eu_act_hr(request):
    """Main EU Act HR page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Main EU Act HR", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/main_euacthr.html", {
        "company": company,
        "subpage": "main_eu_act_hr",
        "breadcrumbs": breadcrumbs,
    })


def main_eu_act_lr(request):
    """Main EU Act LR page"""
    company = MockCompany()
    breadcrumbs = [{"name": "Main EU Act LR", "url": request.build_absolute_uri()}]
    return render(request, "governance/pages/main_euactlr.html", {
        "company": company,
        "subpage": "main_eu_act_lr",
        "breadcrumbs": breadcrumbs,
    })


def mra(request):
    """Model Risk Assessment (MRA) page"""
    ensure_governance_platform(request)
    company = MockCompany()
    agent_name = request.GET.get('agent', '')
    category = request.GET.get('category', 'model')
    
    breadcrumbs = [{"name": "Risk Assessment", "url": request.build_absolute_uri()}]
    
    return render(request, "governance/pages/mra.html", {
        "company": company,
        "subpage": "mra",
        "breadcrumbs": breadcrumbs,
        "agent": None,
        "agent_name": agent_name,
        "category": category,
    })


def risk_overview(request):
    """Risk Registry Overview page"""
    ensure_governance_platform(request)
    company = MockCompany()
    agent_name = request.GET.get('agent', '')
    category = request.GET.get('category', 'overview')
    
    breadcrumbs = [{"name": "Risk Overview", "url": request.build_absolute_uri()}]
    
    # Load risk_tools.json using BASE_DIR from settings
    from django.conf import settings
    from pathlib import Path
    risk_tools_path = settings.BASE_DIR / 'static' / 'governance' / 'data' / 'risk_tools.json'
    risk_tools_data = {}
    if risk_tools_path.exists():
        try:
            with open(risk_tools_path, 'r', encoding='utf-8') as f:
                risk_tools_data = json.load(f)
        except Exception as e:
            # Log error but don't break the page
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load risk_tools.json: {e}")
    
    # Pass risk_tools_data as JSON for JavaScript to use
    import json as json_module
    risk_tools_json = json_module.dumps(risk_tools_data) if risk_tools_data else '{}'
    
    return render(request, "governance/pages/risk_overview.html", {
        "company": company,
        "subpage": "risk_overview",
        "breadcrumbs": breadcrumbs,
        "risk_tools_data": risk_tools_data,
        "risk_tools_json": risk_tools_json,  # JSON string for JavaScript
        "agent": None,
        "agent_name": agent_name,
        "category": category,
    })


# API Endpoints - return mock responses
@require_http_methods(["POST"])
def api_create_ai_agent(request):
    """Create new AI Agent - mock implementation"""
    return JsonResponse({
        'success': True,
        'message': 'Mock: Agent creation not implemented in demo mode'
    })


@require_http_methods(["POST"])
def api_create_ai_use_case(request):
    """Create new AI Use Case - mock implementation"""
    return JsonResponse({
        'success': True,
        'message': 'Mock: Use case creation not implemented in demo mode'
    })


@require_http_methods(["GET"])
def api_get_models_datasets(request):
    """Get all available models and datasets"""
    models = get_mock_models()
    datasets = get_mock_datasets()
    
    return JsonResponse({
        'success': True,
        'models': [{'id': m.get('id'), 'name': m.get('name'), 'vendor': m.get('vendor', '')} for m in models],
        'datasets': [{'id': d.get('id'), 'name': d.get('name'), 'source': d.get('source', '')} for d in datasets],
    })


@require_http_methods(["POST"])
def api_create_model(request):
    """Create new AI Model - mock implementation"""
    return JsonResponse({
        'success': True,
        'message': 'Mock: Model creation not implemented in demo mode'
    })


@require_http_methods(["POST"])
def api_create_dataset(request):
    """Create new AI Dataset - mock implementation"""
    return JsonResponse({
        'success': True,
        'message': 'Mock: Dataset creation not implemented in demo mode'
    })


@require_http_methods(["GET", "POST"])
def api_use_case_evidences(request, use_case_id):
    """Get or create evidence for use case"""
    if request.method == 'GET':
        evidences = [e for e in get_mock_evidences() if e.get('use_case_id') == int(use_case_id)]
        return JsonResponse({
            'success': True,
            'evidences': evidences
        })
    else:
        return JsonResponse({
            'success': True,
            'message': 'Mock: Evidence upload not implemented in demo mode'
        })


@require_http_methods(["DELETE"])
def api_delete_evidence(request, use_case_id, evidence_id):
    """Delete evidence - mock implementation"""
    return JsonResponse({'success': True, 'message': 'Mock: Deletion not implemented in demo mode'})


@require_http_methods(["GET", "POST"])
def api_use_case_evaluation_reports(request, use_case_id):
    """Get or create evaluation report for use case"""
    if request.method == 'GET':
        reports = [r for r in get_mock_evaluation_reports() if r.get('use_case_id') == int(use_case_id)]
        return JsonResponse({
            'success': True,
            'reports': reports
        })
    else:
        return JsonResponse({
            'success': True,
            'message': 'Mock: Report upload not implemented in demo mode'
        })


@require_http_methods(["DELETE"])
def api_delete_evaluation_report(request, use_case_id, report_id):
    """Delete evaluation report - mock implementation"""
    return JsonResponse({'success': True, 'message': 'Mock: Deletion not implemented in demo mode'})


@require_http_methods(["GET", "POST"])
def api_use_case_review_comments(request, use_case_id):
    """Get or create review comment for use case"""
    if request.method == 'GET':
        comments = [c for c in get_mock_review_comments() if c.get('use_case_id') == int(use_case_id)]
        return JsonResponse({
            'success': True,
            'comments': comments
        })
    else:
        return JsonResponse({
            'success': True,
            'message': 'Mock: Comment creation not implemented in demo mode'
        })


@require_http_methods(["POST"])
def api_upload(request):
    """
    Upload files to Gemini File Search Store for RAG processing.
    
    Expected form data:
    - file_url: File(s) to upload (can be multiple)
    - data_type: Type of data (e.g., 'ai_input_ai_act')
    
    Returns JSON response with success status and message.
    """
    import logging
    from pathlib import Path
    from django.conf import settings
    
    logger = logging.getLogger(__name__)
    
    try:
        # Check if data_type is for AI Act
        data_type = request.POST.get('data_type', '')
        if data_type != 'ai_input_ai_act':
            return JsonResponse({
                'success': False,
                'error': f'Unsupported data_type: {data_type}'
            }, status=400)
        
        # Get files from request
        files = request.FILES.getlist('file_url')
        if not files:
            return JsonResponse({
                'success': False,
                'error': 'No files provided'
            }, status=400)
        
        # Initialize Gemini client
        try:
            from google import genai
        except ImportError:
            return JsonResponse({
                'success': False,
                'error': 'google-genai package not installed'
            }, status=503)
        
        api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': 'GEMINI_API_KEY not configured'
            }, status=503)
        
        client = genai.Client(api_key=api_key)
        
        # Get store name
        store_name = getattr(settings, 'AI_ACT_STORE_NAME', '') or os.environ.get('AI_ACT_STORE_NAME', '')
        if not store_name:
            # Try to load from store info file
            store_info_path = getattr(settings, 'AI_ACT_STORE_INFO_PATH', None)
            if store_info_path and Path(store_info_path).exists():
                try:
                    with open(store_info_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.startswith('store_name='):
                                store_name = line.split('=', 1)[1].strip()
                                break
                except Exception as e:
                    logger.warning(f"Could not read store info file: {e}")
        
        if not store_name:
            return JsonResponse({
                'success': False,
                'error': 'AI Act store not configured. Please run setup_ai_act_store.py first.'
            }, status=503)
        
        # Ensure store name is in the correct format (fileSearchStores/{id})
        # The store.name from the API is already in this format, but if stored without prefix, add it
        if not store_name.startswith('fileSearchStores/'):
            # If it's just an ID, add the prefix
            if '/' not in store_name:
                store_name = f"fileSearchStores/{store_name}"
            else:
                # Try to find store by display name if store_name looks like a display name
                logger.info(f"Store name '{store_name}' doesn't match expected format, trying to find by display name...")
                try:
                    stores = list(client.file_search_stores.list())
                    store_display_name = store_name
                    found_store = None
                    for store in stores:
                        if store.display_name == store_display_name:
                            found_store = store
                            break
                    
                    if found_store:
                        store_name = found_store.name
                        logger.info(f"Found store by display name: {store_name}")
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': f'Store not found. Please verify the store name or run setup_ai_act_store.py to create a new store.'
                        }, status=404)
                except Exception as e:
                    logger.error(f"Error listing stores: {e}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Could not verify store: {str(e)}'
                    }, status=503)
        
        # Verify store exists and is accessible
        try:
            logger.info(f"Verifying store access: {store_name}")
            # Try to list documents in the store to verify access
            list(client.file_search_stores.documents.list(parent=store_name, page_size=1))
        except Exception as e:
            logger.error(f"Store verification failed: {e}")
            # If verification fails, try to find store by listing all stores
            try:
                logger.info("Attempting to find store by listing all stores...")
                stores = list(client.file_search_stores.list())
                if not stores:
                    return JsonResponse({
                        'success': False,
                        'error': 'No file search stores found. Please run setup_ai_act_store.py to create a store.'
                    }, status=404)
                
                # Try to find a store with matching name or use the first one
                found_store = None
                for store in stores:
                    if store.name == store_name or store.name.endswith(store_name.split('/')[-1]):
                        found_store = store
                        break
                
                if not found_store:
                    # Use the first available store as fallback
                    found_store = stores[0]
                    logger.warning(f"Store '{store_name}' not found, using first available store: {found_store.name}")
                
                store_name = found_store.name
            except Exception as list_error:
                error_msg = f'Could not access file search store "{store_name}". '
                if '403' in str(e) or 'PERMISSION_DENIED' in str(e):
                    error_msg += 'Permission denied. The store may have been created with a different API key, or the API key may not have the required permissions. '
                error_msg += f'Original error: {str(e)}'
                if str(list_error) != str(e):
                    error_msg += f' List error: {str(list_error)}'
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=503)
        
        # Upload files to store
        uploaded_count = 0
        errors = []
        
        for file in files:
            temp_file_path = None
            try:
                # Generate a display name from the file name
                display_name = f"user_uploaded/{file.name}"
                
                # Determine MIME type
                mime_type = 'text/plain'  # Default
                if file.name.endswith('.pdf'):
                    mime_type = 'application/pdf'
                elif file.name.endswith(('.doc', '.docx')):
                    mime_type = 'application/msword'
                elif file.name.endswith('.txt'):
                    mime_type = 'text/plain'
                
                logger.info(f"Uploading file: {file.name} to store: {store_name}")
                
                # Save uploaded file to temporary file (Gemini API expects a file path or file handle)
                # Reset file pointer to beginning in case it was read
                file.seek(0)
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.name).suffix) as temp_file:
                    temp_file_path = temp_file.name
                    # Write uploaded file content to temp file
                    for chunk in file.chunks():
                        temp_file.write(chunk)
                    temp_file.flush()
                
                # Upload to file search store using the temporary file
                with open(temp_file_path, 'rb') as f:
                    client.file_search_stores.upload_to_file_search_store(
                        file_search_store_name=store_name,
                        file=f,
                        config={'display_name': display_name, 'mime_type': mime_type}
                    )
                
                uploaded_count += 1
                logger.info(f"Successfully uploaded: {file.name}")
                
            except Exception as e:
                error_msg = f"Error uploading {file.name}: {str(e)}"
                # Provide more helpful error messages for common issues
                if '403' in str(e) or 'PERMISSION_DENIED' in str(e):
                    error_msg += f" (Permission denied - the store '{store_name}' may have been created with a different API key)"
                elif '404' in str(e) or 'NOT_FOUND' in str(e):
                    error_msg += f" (Store '{store_name}' not found)"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
            finally:
                # Clean up temporary file
                if temp_file_path and Path(temp_file_path).exists():
                    try:
                        Path(temp_file_path).unlink()
                    except Exception as e:
                        logger.warning(f"Could not delete temp file {temp_file_path}: {e}")
        
        if uploaded_count == 0:
            return JsonResponse({
                'success': False,
                'error': 'Failed to upload any files',
                'errors': errors
            }, status=500)
        
        response_data = {
            'success': True,
            'message': f'Successfully uploaded {uploaded_count} file(s)',
            'uploaded_count': uploaded_count
        }
        
        if errors:
            response_data['warnings'] = errors
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in api_upload: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["DELETE"])
def api_delete_chat_history(request, chat_id):
    """
    Delete a single chat history item.
    For hackathon demo, this clears from in-memory storage.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get AI Act service to clear chat history
        from .infrastructure.services.gemini_ai_act_service import get_ai_act_service
        
        try:
            ai_act_service = get_ai_act_service()
            # Clear chat history for this ID
            if hasattr(ai_act_service, '_chat_histories') and chat_id in ai_act_service._chat_histories:
                del ai_act_service._chat_histories[chat_id]
            if hasattr(ai_act_service, '_chat_sessions') and chat_id in ai_act_service._chat_sessions:
                del ai_act_service._chat_sessions[chat_id]
            logger.info(f"Deleted chat history: {chat_id}")
        except (ValueError, ImportError) as e:
            logger.warning(f"AI Act service not available: {e}")
            # For demo purposes, still return success even if service not available
        
        return JsonResponse({
            'success': True,
            'message': 'Chat history deleted'
        })
        
    except Exception as e:
        logger.error(f"Error deleting chat history: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["PUT", "DELETE"])
def api_clear_chat_history(request, agent_id):
    """
    Clear all chat history for an agent.
    For hackathon demo, this clears from in-memory storage.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get AI Act service to clear chat history
        from .infrastructure.services.gemini_ai_act_service import get_ai_act_service
        
        try:
            ai_act_service = get_ai_act_service()
            # Clear all chat histories and sessions
            if hasattr(ai_act_service, '_chat_histories'):
                ai_act_service._chat_histories.clear()
            if hasattr(ai_act_service, '_chat_sessions'):
                ai_act_service._chat_sessions.clear()
            logger.info(f"Cleared all chat history for agent: {agent_id}")
        except (ValueError, ImportError) as e:
            logger.warning(f"AI Act service not available: {e}")
            # For demo purposes, still return success even if service not available
        
        return JsonResponse({
            'success': True,
            'message': 'Chat history cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def api_check_store_info(request):
    """
    Check and display store information and model configuration.
    Useful for debugging and verification.
    """
    import logging
    from pathlib import Path
    from django.conf import settings
    
    logger = logging.getLogger(__name__)
    
    info = {
        'store_info_file': {
            'path': str(getattr(settings, 'AI_ACT_STORE_INFO_PATH', None)),
            'exists': False,
            'content': {}
        },
        'settings': {
            'AI_ACT_STORE_NAME': getattr(settings, 'AI_ACT_STORE_NAME', '') or 'Not set',
            'AI_ACT_MODEL_NAME': getattr(settings, 'AI_ACT_MODEL_NAME', 'Not set'),
            'AI_ACT_USE_FILE_SEARCH': getattr(settings, 'AI_ACT_USE_FILE_SEARCH', False),
            'GEMINI_API_KEY': 'Set' if getattr(settings, 'GEMINI_API_KEY', '') else 'Not set',
        },
        'environment': {
            'AI_ACT_STORE_NAME': os.environ.get('AI_ACT_STORE_NAME', 'Not set'),
            'AI_ACT_MODEL_NAME': os.environ.get('AI_ACT_MODEL_NAME', 'Not set'),
        },
        'resolved_store_name': None,
        'service_status': 'Not initialized'
    }
    
    # Check store info file
    store_info_path = getattr(settings, 'AI_ACT_STORE_INFO_PATH', None)
    if store_info_path:
        path_obj = Path(store_info_path)
        info['store_info_file']['exists'] = path_obj.exists()
        if path_obj.exists():
            try:
                with open(store_info_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            info['store_info_file']['content'][key] = value
            except Exception as e:
                info['store_info_file']['error'] = str(e)
    
    # Try to get resolved store name from service
    try:
        from .infrastructure.services.gemini_ai_act_service import get_ai_act_service
        try:
            ai_act_service = get_ai_act_service()
            info['resolved_store_name'] = ai_act_service.get_store_name()
            info['service_status'] = 'Initialized'
            info['service_model'] = ai_act_service.model_name
        except (ValueError, ImportError) as e:
            info['service_status'] = f'Error: {str(e)}'
    except Exception as e:
        info['service_status'] = f'Failed to initialize: {str(e)}'
    
        return JsonResponse({
            'success': True,
            'info': info
        })


def organization(request):
    """
    Organization Information page.
    Displays form for configuring organization details and AI compliance settings.
    """
    # For hackathon demo, use mock data
    # In production, this would load from database
    organization_data = {
        'documents': [],
        'org_profile': {},
        'scope': {},
        'governance': {},
        'ai_literacy': {}
    }
    
    return render(request, 'governance/pages/organization.html', {
        'organization_data': organization_data,
        'company': MockCompany() if 'MockCompany' in globals() else None,
    })


@require_http_methods(["POST"])
def api_save_organization(request):
    """
    Save organization information from all sections.
    For hackathon demo, stores in memory.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        
        # In a real application, this would save to database
        # For demo, we'll just log and return success
        logger.info(f"Organization data received: {len(data)} sections")
        
        # Store in a simple in-memory dict (would be database in production)
        if not hasattr(api_save_organization, '_storage'):
            api_save_organization._storage = {}
        
        api_save_organization._storage = data
        
        return JsonResponse({
            'success': True,
            'message': 'Organization information saved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error saving organization data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def ai_inventory(request):
    """
    AI Inventory page - Table view of all AI systems.
    Displays systems with status, role, risk classification, and compliance status.
    """
    ensure_governance_platform(request)
    
    company = MockCompany()
    breadcrumbs = [
        {"name": "AI Inventory", "url": request.build_absolute_uri()},
    ]
    
    # Get mock data
    agents_data = get_mock_agents()
    
    # Transform agents data to systems format for the table
    ai_systems = []
    systems_need_attention = 0
    
    # Status mapping
    status_map = {
        'assessing': 'In progress',
        'reviewing': 'In progress',
        'compliant': 'In production',
        'non_compliant': 'Testing',
        'planned': 'Planned',
    }
    
    # Badge classes
    status_badge_classes = {
        'In production': 'bg-green-100 text-green-700',
        'Testing': 'bg-orange-100 text-orange-700',
        'Planned': 'bg-gray-100 text-gray-700',
        'In progress': 'bg-blue-100 text-blue-700',
    }
    
    risk_badge_classes = {
        'Minimal': 'bg-green-100 text-green-700',
        'Limited transparency': 'bg-yellow-100 text-yellow-700',
        'High-risk': 'bg-orange-100 text-orange-700',
        'Not assessed': 'bg-gray-100 text-gray-700',
    }
    
    compliance_badge_classes = {
        'Compliant': 'bg-green-100 text-green-700',
        'In progress': 'bg-blue-100 text-blue-700',
        'Not started': 'bg-gray-100 text-gray-700',
    }
    
    # Role mapping
    role_map = {
        'deployer': 'Deployer',
        'provider': 'Provider',
        'importer': 'Importer',
        'distributor': 'Distributor',
    }
    
    # Risk classification mapping
    risk_map = {
        'limited_risks': 'Limited transparency',
        'high_risks': 'High-risk',
        'minimal_risks': 'Minimal',
        'not_assessed': 'Not assessed',
    }
    
    # Provider type mapping (mock data based on vendor)
    provider_type_map = {
        '': 'In-house',  # No vendor = in-house
        'DTM': 'In-house',
        'DT Master Nature': 'In-house',
        'Cleary': 'External',
    }
    
    # Mock last updated dates (in days ago from today)
    import random
    from datetime import datetime, timedelta
    
    for idx, agent in enumerate(agents_data):
        compliance_status = agent.get('compliance_status', 'assessing')
        status = status_map.get(compliance_status, 'Planned')
        
        # Handle 'planned' status specially
        if compliance_status == 'planned':
            status = 'Planned'
        
        # Check if needs attention
        if compliance_status in ['assessing', 'reviewing']:
            systems_need_attention += 1
        
        # Map compliance status for display
        compliance_display = {
            'assessing': 'In progress',
            'reviewing': 'In progress',
            'compliant': 'Compliant',
            'non_compliant': 'Not started',
            'planned': 'Not started',
        }.get(compliance_status, 'Not started')
        
        # Get risk classification
        risk_class = agent.get('risk_classification', 'limited_risks')
        risk_display = risk_map.get(risk_class, 'Not assessed')
        
        # Get owner (business unit)
        owner = agent.get('business_unit', '') or '—'
        
        # Get provider type
        vendor = agent.get('vendor', '')
        provider_type = provider_type_map.get(vendor, 'Mixed' if vendor else 'In-house')
        
        # Generate mock last updated date (varying dates for different systems)
        # Use system index to create varied dates
        days_ago = [15, 18, 10, 5, 20][idx % 5]  # Cycle through different days
        last_updated_date = datetime.now() - timedelta(days=days_ago)
        last_updated = last_updated_date.strftime('%b %d, %Y')
        
        ai_systems.append({
            'id': agent.get('id'),
            'name': agent.get('name', 'Unnamed System'),
            'owner': owner,
            'status': status,
            'status_badge_class': status_badge_classes.get(status, 'bg-gray-100 text-gray-700'),
            'role': role_map.get(agent.get('ai_act_role', 'deployer'), 'Deployer'),
            'risk_classification': risk_display,
            'risk_badge_class': risk_badge_classes.get(risk_display, 'bg-gray-100 text-gray-700'),
            'compliance_status': compliance_display,
            'compliance_badge_class': compliance_badge_classes.get(compliance_display, 'bg-gray-100 text-gray-700'),
            'last_updated': last_updated,
            'provider_type': provider_type,
        })
    
    return render(request, 'governance/pages/ai_inventory.html', {
        'company': company,
        'subpage': 'ai_inventory',
        'breadcrumbs': breadcrumbs,
        'ai_systems': ai_systems,
        'systems_need_attention': systems_need_attention,
    })


def ai_system_detail(request, agent_id):
    """
    AI System Detail page - Shows detailed information about a specific AI system.
    Displays Profile, Assessment, and Result tabs.
    """
    ensure_governance_platform(request)
    
    company = MockCompany()
    
    # Get agent data
    agents_data = get_mock_agents()
    agent = next((a for a in agents_data if str(a.get('id')) == str(agent_id)), None)
    
    if not agent:
        from django.http import Http404
        raise Http404("AI System not found")
    
    # Mock uploaded documents for Profile tab
    uploaded_documents = [
        {'name': 'Company_Registration.pdf', 'uploaded': '2 mins ago'},
        {'name': 'AI_Policy_Document.docx', 'uploaded': '5 mins ago'},
        {'name': 'Compliance_Report_2024.pdf', 'uploaded': '10 mins ago'},
    ]

    sector_options = [
        "Biometric identification and categorisation",
        "Critical infrastructure management",
        "Education & vocational training",
        "Employment & workforce management",
        "Access to essential private or public services & benefits",
        "Law enforcement",
        "Migration, asylum & border control",
        "Justice & democratic processes",
        "Other / not listed:",
    ]

    deployment_contexts = [
        "Workplace (employee-facing)",
        "Educational institution",
        "Healthcare setting",
        "Law enforcement / public security",
        "Public administration / government service",
        "General public / consumer-facing",
        "Other:",
    ]

    system_users = [
        "Internal employees",
        "External contractors / service providers",
        "Customers / consumers",
        "Students",
        "Patients",
        "Public authority staff",
        "Other:",
    ]

    affected_outputs = [
        "Employees",
        "Job applicants",
        "Students",
        "Patients",
        "Customers / consumers",
        "Citizens / residents",
        "Other:",
    ]

    vulnerable_groups = [
        "Children / minors",
        "Persons with disabilities",
        "Persons in socio-economic vulnerability",
        "None / not applicable",
        "Unknown",
    ]

    workflow_roles = [
        "Provides insights / recommendations only (human decides)",
        "Supports decisions (human approval required)",
        "Automatically makes decisions / actions (no human approval)",
        "Mixed / depends on case",
        "Unknown",
    ]

    output_types = [
        "Score / rating",
        "Ranking",
        "Recommendation",
        "Classification / label",
        "Prediction / forecasting",
        "Matching (e.g., job matching, content matching)",
        "Detection (e.g., fraud detection)",
        "Identification / verification",
        "Generated content (text / image / audio / video)",
        "Automated decision (system executes action)",
        "Other:",
    ]

    decision_influence = [
        "Yes",
        "No",
        "Not sure",
    ]

    auto_execute = [
        "No (advisory only)",
        "Yes (automatic actions)",
        "Mixed",
        "Unknown",
    ]

    capability_practices = [
        "Subliminal / manipulative / deceptive techniques that materially distort behaviour and are likely to cause significant harm",
        "Exploitation of vulnerabilities (age, disability, or social / economic situation) to distort behaviour likely causing significant harm",
        "Social scoring leading to detrimental / unfavourable treatment (esp. unjustified / disproportionate)",
        "Criminal offence risk assessment / prediction based solely on profiling or personality traits (individual predictive policing)",
        "Untargeted scraping of facial images from the internet or CCTV to build / expand facial recognition databases",
        "Emotion recognition in the workplace or in education settings",
        "Biometric categorisation that infers or predicts sensitive traits (e.g., race, political opinions, religion, trade union membership, sexual orientation)",
        "Real-time remote biometric identification (RBI) in publicly accessible spaces for law enforcement purposes",
        "None of the above",
    ]

    interacts_natural_persons = [
        "Yes",
        "No",
        "Unknown",
    ]

    synthetic_content = [
        "Text",
        "Image",
        "Audio",
        "Video",
        "No",
        "Unknown",
    ]

    ai_kinds = [
        "Rules-based automation",
        "Machine learning",
        "Deep learning",
        "Generative AI",
        "Hybrid",
        "Unknown",
    ]

    gpai_integration = [
        "Yes",
        "No",
        "Unknown",
    ]

    training_sources = [
        "In-house training",
        "Vendor-trained model (no training by us)",
        "Fine-tuned by us",
        "Unknown / not applicable",
    ]

    update_frequency = [
        "Static / never",
        "Periodic retraining",
        "Continuous learning",
        "Unknown",
    ]

    data_types = [
        "Personal data",
        "Sensitive data (health, biometric, etc.)",
        "Employee data",
        "Children / minors data",
        "Public web data",
        "Non-personal / industrial data",
        "Unknown",
    ]

    assessment_blocks = [
        {"title": "Block 1 — Prohibited Practices Screening", "status": "Not assessed"},
        {"title": "Block 2 — High-Risk Classification", "status": "Not assessed"},
        {"title": "Block 3 — Transparency Obligation", "status": "Not assessed"},
        {"title": "Block 4 — GPAI (General-Purpose AI) Applicability", "status": "Not assessed"},
    ]

    result_blocks = [
        {
            "title": "Block 1 — Prohibited Practices",
            "description": "This AI system does not fall under prohibited practices. It may proceed to further compliance assessment.",
            "status": "Not Prohibited",
            "status_class": "bg-green-100 text-green-700",
        },
        {
            "title": "Block 2 — High-Risk Classification",
            "description": "This AI system requires further review to determine its high-risk classification. Additional information or clarification is needed.",
            "status": "Needs Review",
            "status_class": "bg-yellow-100 text-yellow-700",
        },
        {
            "title": "Block 3 — Transparency Obligation",
            "description": "",
            "status": "Not assessed",
            "status_class": "bg-yellow-100 text-yellow-700",
        },
        {
            "title": "Block 4 — GPAI (General-Purpose AI) Applicability",
            "description": "",
            "status": "Not assessed",
            "status_class": "bg-yellow-100 text-yellow-700",
        },
    ]
    
    breadcrumbs = [
        {"name": "AI Inventory", "url": "/ai-inventory/"},
        {"name": "AI System", "url": request.build_absolute_uri()},
    ]
    
    return render(request, 'governance/pages/ai_system_detail.html', {
        'company': company,
        'subpage': 'ai_system_detail',
        'breadcrumbs': breadcrumbs,
        'agent': agent,
        'uploaded_documents': uploaded_documents,
        'sector_options': sector_options,
        'deployment_contexts': deployment_contexts,
        'system_users': system_users,
        'affected_outputs': affected_outputs,
        'vulnerable_groups': vulnerable_groups,
        'workflow_roles': workflow_roles,
        'output_types': output_types,
        'decision_influence': decision_influence,
        'auto_execute': auto_execute,
        'capability_practices': capability_practices,
        'interacts_natural_persons': interacts_natural_persons,
        'synthetic_content': synthetic_content,
        'ai_kinds': ai_kinds,
        'gpai_integration': gpai_integration,
        'training_sources': training_sources,
        'update_frequency': update_frequency,
        'data_types': data_types,
        'assessment_blocks': assessment_blocks,
        'result_blocks': result_blocks,
    })
