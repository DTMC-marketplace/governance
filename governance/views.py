"""
Governance Platform Views - Refactored with Clean Architecture
Using Clean Architecture patterns: Domain, Application, Infrastructure, Presentation layers

Note: This file maintains backward compatibility. New views using Clean Architecture
are in governance/presentation/views/
"""
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings

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

# Import AI Act Chat API views (standard + streaming)
from .presentation.views.ai_act_chat_view import ai_act_chat_api, ai_act_chat_stream_api

from .mock_data import (
    get_mock_agents, get_mock_use_cases, get_mock_models, get_mock_datasets,
    get_mock_evidences, get_mock_evaluation_reports, get_mock_review_comments,
    get_compliance_projects, get_compliance_detail,
    create_mock_agent, create_mock_use_case, calculate_compliance_mock, calculate_risks_mock,
    MockObject, convert_evidences_to_objects, convert_reports_to_objects, convert_comments_to_objects
)
from .constants import VIRTUAL_AGENT

# Shared list for "Deployment Context" (Add New AI System) and Q1 "In what context will this AI system be deployed?" (AI system detail)
DEPLOYMENT_CONTEXT_DEFAULTS = [
    "Workplace (employee-facing)",
    "Educational institution",
    "Healthcare setting",
    "Law enforcement / public security",
    "Public administration / government service",
    "General public / consumer-facing",
    "Other:",
]

def _deployment_contexts_file_path():
    from pathlib import Path
    return Path(__file__).parent.parent / 'mock_data' / 'deployment_contexts.json'

def _load_deployment_context_options():
    path = _deployment_contexts_file_path()
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
        except Exception:
            pass
    # Fallback to defaults and persist for easier reuse
    _save_deployment_context_options(DEPLOYMENT_CONTEXT_DEFAULTS)
    return list(DEPLOYMENT_CONTEXT_DEFAULTS)

def _save_deployment_context_options(options):
    path = _deployment_contexts_file_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(options, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def _ensure_deployment_context_option(value):
    if not value or not str(value).strip():
        return
    val = str(value).strip()
    if val.lower().startswith('other'):
        return
    options = _load_deployment_context_options()
    if val not in options:
        options.append(val)
        _save_deployment_context_options(options)

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


def organization(request):
    """
    Organization Information page.
    Displays form for configuring organization details and AI compliance settings.
    """
    from pathlib import Path
    
    # Load organization data from JSON file
    mock_data_dir = Path(__file__).parent.parent / 'mock_data'
    org_file = mock_data_dir / 'organization.json'
    
    organization_data = {
        'documents': [],
        'org_profile': {},
        'scope': {},
        'governance': {},
        'ai_literacy': {}
    }
    
    if org_file.exists():
        try:
            with open(org_file, 'r', encoding='utf-8') as f:
                organization_data = json.load(f)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not load organization data: {e}")
    
    return render(request, 'governance/pages/organization.html', {
        'organization_data': organization_data,
        'company': MockCompany() if 'MockCompany' in globals() else None,
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_upload_file(request):
    """
    Upload files to static folder (for general file uploads, not AI Act chat).
    
    Expected form data:
    - file: File(s) to upload (can be multiple)
    - folder: Optional subfolder in static (e.g., 'governance/uploads/organization')
    
    Returns JSON response with success status and file URLs.
    """
    import logging
    from pathlib import Path
    from django.conf import settings
    import uuid
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get files from request
        files = request.FILES.getlist('file')
        if not files:
            return JsonResponse({
                'success': False,
                'error': 'No files provided'
            }, status=400)
        
        # Get optional folder parameter
        folder = request.POST.get('folder', 'governance/uploads')
        
        # Get static directory
        # Calculate BASE_DIR from views.py location (governance/views.py -> project root)
        BASE_DIR = Path(__file__).parent.parent
        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else BASE_DIR / 'static'
        upload_dir = static_dir / folder
        
        # Ensure directory exists
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            try:
                # Generate unique filename to avoid conflicts
                file_ext = Path(file.name).suffix
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                file_path = upload_dir / unique_filename
                
                # Save file
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                # Generate URL
                file_url = f"{settings.STATIC_URL}{folder}/{unique_filename}"
                
                uploaded_files.append({
                    'name': file.name,
                    'size': file.size,
                    'url': file_url,
                    'path': str(file_path.relative_to(static_dir))
                })
                
                logger.info(f"Uploaded {file.name} to {file_path}")
                
            except Exception as e:
                logger.error(f"Error uploading file {file.name}: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error uploading {file.name}: {str(e)}'
                }, status=500)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
            'files': uploaded_files
        })
        
    except Exception as e:
        logger.error(f"Error in file upload: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_save_organization(request):
    """
    Save organization information from all sections.
    For hackathon demo, saves to JSON file.
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        
        # Get path to organization.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        org_file = mock_data_dir / 'organization.json'
        
        # Ensure directory exists
        mock_data_dir.mkdir(exist_ok=True)
        
        # Load existing data if file exists
        existing_data = {}
        if org_file.exists():
            try:
                with open(org_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing organization data: {e}")
        
        # Merge new data with existing data
        # Special handling for documents array - append instead of replace
        if 'documents' in data and isinstance(data['documents'], list):
            if 'documents' not in existing_data:
                existing_data['documents'] = []
            # Append new documents (avoid duplicates by name)
            existing_doc_names = {doc.get('name') for doc in existing_data['documents']}
            for doc in data['documents']:
                if doc.get('name') not in existing_doc_names:
                    existing_data['documents'].append(doc)
            # Remove documents key from data to avoid overwriting
            data_without_docs = {k: v for k, v in data.items() if k != 'documents'}
        else:
            data_without_docs = data
        
        # Merge other data
        existing_data.update(data_without_docs)
        
        # Save to JSON file
        with open(org_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Organization data saved successfully to {org_file}")
        
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


@csrf_exempt
def api_get_organization(request):
    """
    Get organization information from JSON file.
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get path to organization.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        org_file = mock_data_dir / 'organization.json'
        
        # Load data from JSON file
        if org_file.exists():
            with open(org_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Return empty structure if file doesn't exist
            data = {
                'documents': [],
                'org_profile': {},
                'scope': {},
                'governance': {},
                'ai_literacy': {}
            }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error loading organization data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_create_ai_inventory_system(request):
    """
    Create new AI system in inventory.
    
    Expected JSON body:
    {
        "name": "System Name",
        "owner": "Not provided",
        "status": "Planned",
        "roles": ["Provider"],
        "provider_type": "Unknown",
        "risk_classification": "Not assessed",
        "compliance_status": "Not started",
        "deployment_context": "Workplace",
        "document": {
            "name": "file.pdf",
            "url": "/static/governance/uploads/uuid.pdf",
            "path": "governance/uploads/uuid.pdf",
            "size": 12345
        }
    }
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        
        # Get path to agents.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        agents_file = mock_data_dir / 'agents.json'
        
        # Load existing agents
        existing_agents = []
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    existing_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing agents: {e}")
        
        # Find next ID
        next_id = max([agent.get('id', 0) for agent in existing_agents], default=0) + 1
        
        # Map form data to agent structure
        # Map roles array to ai_act_role (use first role as primary, or join if multiple)
        roles = data.get('roles', ['Provider'])
        ai_act_role = roles[0].lower() if roles else 'provider'
        
        # Map status to compliance_status format
        status_map = {
            'Planned': 'planned',
            'Testing': 'assessing',
            'In production': 'compliant',
            'Retired': 'compliant'
        }
        compliance_status = status_map.get(data.get('status', 'Planned'), 'planned')
        
        # Map risk classification
        risk_map = {
            'Not assessed': 'not_assessed',
            'Prohibited': 'prohibited',
            'High-risk': 'high_risks',
            'Limited transparency': 'limited_risks',
            'Minimal': 'minimal_risks',
            'Not in scope': 'not_in_scope'
        }
        risk_classification = risk_map.get(data.get('risk_classification', 'Not assessed'), 'not_assessed')
        
        # Map provider_type to vendor (for backward compatibility) and store provider_type separately
        provider_type = data.get('provider_type', 'Unknown')
        vendor_map = {
            'In-house': '',
            'External': 'External',
            'Mixed': 'Mixed',
            'Unknown': ''
        }
        vendor = vendor_map.get(provider_type, '')
        
        # Create new agent
        deployment_context = data.get('deployment_context', '')
        _ensure_deployment_context_option(deployment_context)
        new_agent = {
            'id': next_id,
            'name': data.get('name', ''),
            'business_unit': data.get('owner', 'Not provided'),
            'compliance_status': data.get('compliance_status', 'Not started').lower().replace(' ', '_'),
            'ai_act_role': ai_act_role,
            'roles': roles,  # Store all roles
            'vendor': vendor,  # For backward compatibility
            'provider_type': provider_type,  # Store original provider type
            'risk_classification': risk_classification,
            'investment_type': 'internal',
            'status': data.get('status', 'Planned'),
            'deployment_context': deployment_context
        }
        
        # Add document if provided
        if data.get('document'):
            new_agent['document'] = data['document']
        
        # Add to list
        existing_agents.append(new_agent)
        
        # Save to JSON file
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(existing_agents, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created new AI system: {new_agent['name']} (ID: {next_id})")
        
        return JsonResponse({
            'success': True,
            'message': 'AI System created successfully',
            'system_id': next_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating AI system: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_add_deployment_context(request):
    """
    Add a new deployment context option to mock_data/deployment_contexts.json.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        data = json.loads(request.body)
        value = data.get('value', '')
        _ensure_deployment_context_option(value)
        return JsonResponse({
            'success': True,
            'options': _load_deployment_context_options()
        })
    except Exception as e:
        logger.error(f"Error adding deployment context option: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_delete_ai_inventory_systems(request):
    """
    Delete AI systems from inventory.
    
    Expected JSON body:
    {
        "system_ids": [1, 2, 3]
    }
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        system_ids = data.get('system_ids', [])
        
        if not system_ids:
            return JsonResponse({
                'success': False,
                'error': 'No system IDs provided'
            }, status=400)
        
        # Get path to agents.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        agents_file = mock_data_dir / 'agents.json'
        
        # Load existing agents
        existing_agents = []
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    existing_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing agents: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Could not load agents data'
                }, status=500)
        
        # Convert system_ids to integers and ensure they match agent IDs
        system_ids_int = [int(sid) for sid in system_ids]
        
        # Filter out deleted agents - compare IDs as integers
        original_count = len(existing_agents)
        remaining_agents = []
        deleted_ids = []
        
        for agent in existing_agents:
            agent_id = agent.get('id')
            # Convert agent_id to int if it's not already
            if isinstance(agent_id, str):
                try:
                    agent_id = int(agent_id)
                except (ValueError, TypeError):
                    pass
            
            if agent_id in system_ids_int:
                deleted_ids.append(agent_id)
            else:
                remaining_agents.append(agent)
        
        deleted_count = original_count - len(remaining_agents)
        
        if deleted_count == 0:
            logger.warning(f"No systems found to delete. Requested IDs: {system_ids_int}, Available IDs: {[a.get('id') for a in existing_agents]}")
            return JsonResponse({
                'success': False,
                'error': f'No systems found to delete. Requested IDs: {system_ids_int}'
            }, status=404)
        
        # Save updated list
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(remaining_agents, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Deleted {deleted_count} AI system(s): {system_ids}")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} system(s)',
            'deleted_count': deleted_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error deleting AI systems: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def api_export_ai_inventory(request):
    """
    Export AI systems to CSV format.
    Returns CSV file with all AI systems data.
    """
    import logging
    import csv
    from io import StringIO
    from django.http import HttpResponse
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get mock data
        agents_data = get_mock_agents()
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers - match template format (Last Updated is auto-generated, not in template)
        headers = [
            'AI System Name',
            'Owner (Person / Team)',
            'Status',
            'Role',
            'Risk Classification',
            'Compliance Status',
            'Provider Type',
            'Deployment Context'
        ]
        writer.writerow(headers)
        
        # Status mapping
        status_map = {
            'assessing': 'In progress',
            'reviewing': 'In progress',
            'compliant': 'In production',
            'non_compliant': 'Testing',
            'planned': 'Planned',
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
        
        # Compliance status mapping
        compliance_map = {
            'assessing': 'In progress',
            'reviewing': 'In progress',
            'compliant': 'Compliant',
            'non_compliant': 'Not started',
            'planned': 'Not started',
        }
        
        # Provider type mapping (for backward compatibility)
        provider_type_map = {
            '': 'In-house',
            'DTM': 'In-house',
            'DT Master Nature': 'In-house',
            'Cleary': 'External',
        }
        
        # Write data rows
        for agent in agents_data:
            compliance_status = agent.get('compliance_status', 'assessing')
            status = status_map.get(compliance_status, 'Planned')
            if compliance_status == 'planned':
                status = 'Planned'
            
            # Get roles - support both old and new format
            roles = agent.get('roles', [])
            if not roles and agent.get('ai_act_role'):
                roles = [agent.get('ai_act_role')]
            
            roles_display = [role_map.get(role.lower(), role.title()) for role in roles]
            role_display = ', '.join(roles_display) if roles_display else 'Not specified'
            
            risk_class = agent.get('risk_classification', 'limited_risks')
            risk_display = risk_map.get(risk_class, 'Not assessed')
            
            compliance_display = compliance_map.get(compliance_status, 'Not started')
            
            # Get provider type - use provider_type field if available, otherwise map from vendor
            if 'provider_type' in agent:
                provider_type = agent.get('provider_type', 'Unknown')
            else:
                # Backward compatibility: map from vendor
                vendor = agent.get('vendor', '')
                provider_type = provider_type_map.get(vendor, 'Mixed' if vendor else 'In-house')
            
            owner = agent.get('business_unit', '') or '—'
            
            deployment_context = agent.get('deployment_context', 'Workplace')
            from datetime import datetime
            last_updated = datetime.now().strftime('%b %d, %Y')
            writer.writerow([
                agent.get('name', 'Unnamed System'),
                owner,
                status,
                role_display,
                risk_display,
                compliance_display,
                provider_type,
                deployment_context
            ])
        
        # Get CSV content
        csv_content = output.getvalue()
        output.close()
        
        # Return CSV as HTTP response
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="ai_systems_export.csv"'
        return response
        
    except Exception as e:
        logger.error(f"Error exporting AI inventory: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_import_ai_inventory(request):
    """
    Import AI systems from CSV file.
    
    Expected JSON body:
    {
        "file_url": "/static/governance/uploads/uuid.csv",
        "file_path": "governance/uploads/uuid.csv",
        "file_name": "import.csv"
    }
    """
    import logging
    import csv
    from pathlib import Path
    from django.conf import settings
    
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        file_path = data.get('file_path', '')
        file_url = data.get('file_url', '')
        
        if not file_path:
            return JsonResponse({
                'success': False,
                'error': 'File path not provided'
            }, status=400)
        
        # Get static directory
        BASE_DIR = Path(__file__).parent.parent
        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else BASE_DIR / 'static'
        full_file_path = static_dir / file_path
        
        if not full_file_path.exists():
            return JsonResponse({
                'success': False,
                'error': f'File not found: {file_path}'
            }, status=404)
        
        # Read CSV file
        imported_systems = []
        with open(full_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                imported_systems.append(row)
        
        # Get path to agents.json
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        agents_file = mock_data_dir / 'agents.json'
        
        # Load existing agents
        existing_agents = []
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    existing_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing agents: {e}")
        
        # Find next ID
        next_id = max([agent.get('id', 0) for agent in existing_agents], default=0) + 1
        
        # Map CSV data to agent format and add to list
        for system_data in imported_systems:
            # Map roles from CSV (could be comma-separated) - support both "Role" and "Role (Person / Team)" headers
            roles_str = system_data.get('Role') or system_data.get('Role (Select all that apply)', 'Provider')
            roles = [r.strip() for r in roles_str.split(',')] if roles_str else ['Provider']
            
            # Map status
            status = system_data.get('Status', 'Planned')
            compliance_status_map = {
                'Planned': 'planned',
                'In production': 'compliant',
                'Testing': 'assessing',
                'Retired': 'compliant'
            }
            compliance_status = compliance_status_map.get(status, 'planned')
            
            # Map risk classification
            risk_display = system_data.get('Risk Classification', 'Not assessed')
            risk_map = {
                'Limited transparency': 'limited_risks',
                'High-risk': 'high_risks',
                'Minimal': 'minimal_risks',
                'Not assessed': 'not_assessed',
                'Prohibited': 'prohibited',
                'Not in scope': 'not_in_scope'
            }
            risk_classification = risk_map.get(risk_display, 'not_assessed')
            
            # Map compliance status
            compliance_display = system_data.get('Compliance Status', 'Not started')
            compliance_map = {
                'Not started': 'planned',
                'In progress': 'assessing',
                'Compliant': 'compliant',
                'Non-compliant': 'non_compliant',
            }
            compliance_status = compliance_map.get(compliance_display, compliance_status)
            
            # Map provider type
            provider_type = system_data.get('Provider Type', 'Unknown')
            vendor_map = {
                'In-house': '',
                'External': 'External',
                'Mixed': 'Mixed',
                'Unknown': ''
            }
            vendor = vendor_map.get(provider_type, '')
            
            deployment_context = system_data.get('Deployment Context', 'Workplace')
            _ensure_deployment_context_option(deployment_context)
            
            # Get owner - support both "Owner" and "Owner (Person / Team)" headers
            owner = system_data.get('Owner (Person / Team)') or system_data.get('Owner', 'Not provided')
            
            new_agent = {
                'id': next_id,
                'name': system_data.get('AI System Name', 'Unnamed System'),
                'business_unit': owner,
                'compliance_status': compliance_status,
                'ai_act_role': roles[0].lower() if roles else 'provider',
                'roles': [r.title() for r in roles],  # Store as array
                'vendor': vendor,  # For backward compatibility
                'provider_type': provider_type,  # Store original provider type
                'risk_classification': risk_classification,
                'investment_type': 'internal',
                'status': status,
                'deployment_context': deployment_context
            }
            
            existing_agents.append(new_agent)
            next_id += 1
        
        # Save updated agents
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(existing_agents, f, indent=2, ensure_ascii=False)
        
        # Delete imported file after processing (no need to keep it)
        try:
            if full_file_path.exists():
                full_file_path.unlink()
                logger.info(f"Deleted imported file: {full_file_path}")
        except Exception as e:
            logger.warning(f"Could not delete imported file {full_file_path}: {e}")
            # Continue even if file deletion fails
        
        logger.info(f"Imported {len(imported_systems)} AI system(s) from CSV")
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully imported {len(imported_systems)} AI system(s)',
            'imported_count': len(imported_systems)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error importing AI inventory: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_ai_system_detail_data(request, agent_id):
    """
    Get or save AI system detail data (Profile, Assessment, Result).
    
    GET: Returns detail data for the agent
    POST: Saves detail data for the agent
    
    Expected JSON body (POST):
    {
        "profile": { ... },
        "assessment": { ... },
        "result": { ... },
        "documents": [ ... ]
    }
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get path to agents.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        agents_file = mock_data_dir / 'agents.json'
        
        # Load existing agents
        existing_agents = []
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    existing_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing agents: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Could not load agents data'
                }, status=500)
        
        # Find agent by ID
        agent = next((a for a in existing_agents if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        if request.method == 'GET':
            # Run assessment logic to ensure fresh data (especially if mock data was edited manually)
            if 'profile' in agent:
                assessment_state = agent.get('assessment', {})
                # For GET, we don't necessarily want to reset state (preserve confirms)
                assessment_results = run_assessment_logic(agent['profile'], assessment_state, reset_state=False)
                agent['assessment'] = assessment_results
            
            # Return detail data
            detail_data = {
                'profile': agent.get('profile', {}),
                'assessment': agent.get('assessment', {}),
                'result': agent.get('result', {}),
                'documents': agent.get('documents', []),
                'risk_evaluation': agent.get('risk_evaluation', {})  # Include risk_evaluation with code_files and dataset_files
            }
            
            # If single document exists, convert to array
            if agent.get('document') and not agent.get('documents'):
                detail_data['documents'] = [agent.get('document')]
            
            return JsonResponse({
                'success': True,
                'data': detail_data
            })
        
        else:  # POST
            # Save detail data
            data = json.loads(request.body)
            
            # Update agent with detail data
            if 'profile' in data:
                agent['profile'] = data['profile']
                
                # Run assessment logic when profile is saved
                # Reset state for fresh assessment as requested
                assessment_state = agent.get('assessment', {})
                assessment_results = run_assessment_logic(agent['profile'], assessment_state, reset_state=True)
                agent['assessment'] = assessment_results


                

                
                logger.info(f"Ran assessment logic for AI system ID: {agent_id}")
                
            if 'assessment' in data:
                agent['assessment'] = data['assessment']
            if 'result' in data:
                agent['result'] = data['result']
            if 'documents' in data:
                # Update documents array
                agent['documents'] = data['documents']
                # Also update single document field if only one document
                if len(data['documents']) == 1:
                    agent['document'] = data['documents'][0]
                elif len(data['documents']) == 0:
                    agent.pop('document', None)
                    agent.pop('documents', None)
            
            # Update agent in list
            for idx, a in enumerate(existing_agents):
                if str(a.get('id')) == str(agent_id):
                    existing_agents[idx] = agent
                    break
            
            # Save updated agents
            with open(agents_file, 'w', encoding='utf-8') as f:
                json.dump(existing_agents, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved detail data for AI system ID: {agent_id}")
            
            # Return assessment results if profile was updated
            response_data = {
                'success': True,
                'message': 'Detail data saved successfully'
            }
            if 'profile' in data:
                response_data['assessment'] = agent.get('assessment', {})
            
            return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error handling AI system detail data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def ai_detects_prohibited_practice():
    """
    Returns True if prohibited practice is detected, False otherwise.
    """
    return False


def run_assessment_logic(profile_data, assessment_state=None, reset_state=False):
    """
    Run assessment logic for Block 1, 2, 3, 4.
    
    Args:
        profile_data: Dictionary containing profile form data
        assessment_state: Dictionary containing assessment state (block1_state, etc.)
        
    Returns:
        Dictionary with assessment results for all blocks:
        {
            'block1': { 'status': '...', 'details': {...} },
            'block2': { 'status': '...', 'details': {...} },
            'block3': { 'status': '...', 'details': {...} },
            'block4': { 'status': '...', 'details': {...} },
            'block1_state': {...}  # Preserved state
        }
    """
    if assessment_state is None:
        assessment_state = {}
    
    block1_state = assessment_state.get('block1_state', {})
    block2_state = assessment_state.get('block2_state', {})
    
    block1_result = get_block1_status(profile_data, block1_state, reset_state=reset_state)
    block3_state = assessment_state.get('block3_state', {})
    block4_state = assessment_state.get('block4_state', {})
    
    assessment_results = {
        'block1': block1_result,
        'block2': get_block2_status(profile_data, block1_result=block1_result, block2_state=block2_state, reset_state=reset_state),
        'block3': get_block3_status(profile_data, block1_result=block1_result, block3_state=block3_state, reset_state=reset_state),
        'block4': get_block4_status(profile_data, block1_result=block1_result, block4_state=block4_state, reset_state=reset_state)
    }
    
    if block1_state:
        assessment_results['block1_state'] = block1_state
    if block2_state:
        assessment_results['block2_state'] = block2_state
    if block3_state:
        assessment_results['block3_state'] = block3_state
    if block4_state:
        assessment_results['block4_state'] = block4_state
    
    return assessment_results


def get_block1_status(profile_data, block1_state=None, reset_state=False):
    """
    Block 1: Prohibited Practices Screening.
    
    Args:
        profile_data: Dictionary containing profile form data
        block1_state: Dictionary containing Block 1 state (confirmation, exception, etc.)
        reset_state: Boolean, if True, clear block1_state for fresh assessment
    
    Returns:
        {
            'status': 'PASS' | 'Triggered' | 'Needs Review' | 'Prohibited' | 'Exception claimed' | 'Not assessed',
            'selected_practices': [...],
            'details': {...}
        }
    """
    if block1_state is None:
        block1_state = {}
    
    # Check Section 7 Capabilities, Q1
    capability_practices = profile_data.get('capability_practices', [])
    if not isinstance(capability_practices, list):
        capability_practices = []
        
    # Conditionally reset Block 1 state based on reset_state flag
    # reset_state=True: Fresh assessment from profile save
    # reset_state=False: State update from api_update_block1_state (preserve state)
    if reset_state:
        block1_state.clear()
    
    # 1. Not Answered -> Not assessed
    if len(capability_practices) == 0:
        return {
            'status': 'Not assessed',
            'selected_practices': [],
            'details': {'reason': 'No capabilities selected'}
        }
    
    # 2. Answered, only "None of the above" -> PASS
    if 'None of the above' in capability_practices and len(capability_practices) == 1:
        return {
            'status': 'PASS',
            'selected_practices': [],
            'details': {'reason': 'None of the above selected'}
        }
    
    # 3. Answered, any option other than "None of the above" -> Triggered
    selected_practices = [p for p in capability_practices if p != 'None of the above']
    
    if not selected_practices:
        # Should be covered by PASS case above, but safe fallback
        return {
            'status': 'PASS',
            'selected_practices': [],
            'details': {'reason': 'No prohibited practices selected'}
        }
    
    # Prohibited practices mapping (from Block_1_Prohibited_Practices_Logic.md)
    prohibited_practices_map = {
        'Subliminal / manipulative / deceptive techniques that materially distort behaviour and are likely to cause significant harm': {
            'label': 'Subliminal/manipulative/deceptive techniques',
            'article': '5(1)(a)',
            'has_exception': False,
            'exception_condition': None
        },
        'Exploitation of vulnerabilities (age, disability, or social / economic situation) to distort behaviour likely causing significant harm': {
            'label': 'Exploitation of vulnerabilities',
            'article': '5(1)(b)',
            'has_exception': False,
            'exception_condition': None
        },
        'Social scoring leading to detrimental / unfavourable treatment (esp. unjustified / disproportionate)': {
            'label': 'Social scoring',
            'article': '5(1)(c)',
            'has_exception': False,
            'exception_condition': None
        },
        'Criminal offence risk assessment / prediction based solely on profiling or personality traits (individual predictive policing)': {
            'label': 'Criminal offence risk assessment',
            'article': '5(1)(d)',
            'has_exception': True,
            'exception_condition': 'AI system is used to support a human assessment based on objective and verifiable facts directly linked to criminal activity (not solely profiling). (Art.5(1)(d))'
        },
        'Untargeted scraping of facial images from the internet or CCTV to build / expand facial recognition databases': {
            'label': 'Untargeted facial image scraping',
            'article': '5(1)(e)',
            'has_exception': False,
            'exception_condition': None
        },
        'Emotion recognition in the workplace or in education settings': {
            'label': 'Emotion recognition in workplace/education',
            'article': '5(1)(f)',
            'has_exception': True,
            'exception_condition': 'AI system is for medical or safety reasons. (Art.5(1)(f))'
        },
        'Biometric categorisation that infers or predicts sensitive traits (e.g., race, political opinions, religion, trade union membership, sexual orientation)': {
            'label': 'Biometric categorisation (sensitive traits)',
            'article': '5(1)(g)',
            'has_exception': True,
            'exception_condition': 'AI system is for labelling or filtering of lawfully acquired biometric datasets, such as images, based on biometric data or categorizing of biometric data in the area of law enforcement. (Art.5(1)(g))'
        },
        'Real-time remote biometric identification (RBI) in publicly accessible spaces for law enforcement purposes': {
            'label': 'Real-time remote biometric identification (RBI)',
            'article': '5(1)(h)',
            'has_exception': True,
            'exception_condition': 'Only if strictly necessary for one of the listed objectives (victims / imminent serious threat / serious crime suspect) and with safeguards + authorisation requirements (Art. 5(2)–(7)).'
        }
    }
    
    # Check if user has confirmed
    prohibited_confirmed = block1_state.get('prohibited_confirmed', False)
    
    if not prohibited_confirmed:
        # Status: "Triggered" (awaiting user confirmation)
        return {
            'status': 'Triggered',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown', 'has_exception': False}) for p in selected_practices},
            'details': {
                'reason': 'Prohibited practices detected, awaiting confirmation',
                'has_exception_available': any(prohibited_practices_map.get(p, {}).get('has_exception', False) for p in selected_practices),
                'has_no_exception': any(not prohibited_practices_map.get(p, {}).get('has_exception', False) for p in selected_practices)
            }
        }
    
    # After user confirms - Check Exception Availability
    has_no_exception_practice = any(not prohibited_practices_map.get(p, {}).get('has_exception', False) for p in selected_practices)
    claiming_exception = block1_state.get('claiming_exception', '')
    
    # 1. As long as, one option with no exception is selected -> Prohibited
    if has_no_exception_practice or claiming_exception == 'No':
        return {
            'status': 'Prohibited',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'No exception available for one or more selected practices' if has_no_exception_practice else 'User declined exception',
                'has_exception_available': not has_no_exception_practice,
                'has_no_exception': has_no_exception_practice
            }
        }
    
    # Check for exception qualifications
    if claiming_exception == '':
        # User hasn't answered exception claim question yet
        return {
            'status': 'Triggered',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'Awaiting exception claim decision',
                'has_exception_available': True,
                'has_no_exception': False
            }
        }
    
    # Exception Question: Does system fall under exception condition?
    # Handle multi-selection: all with exception need to be claimed.
    qualifies_map = block1_state.get('exception_qualifies_map', {})
    practices_with_exception = [p for p in selected_practices if prohibited_practices_map.get(p, {}).get('has_exception', False)]
    
    # Check if all practices with exceptions have been answered
    all_answered = all(p in qualifies_map for p in practices_with_exception)
    
    if not all_answered:
        return {
            'status': 'Triggered',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'Awaiting answers for all exception claims',
                'has_exception_available': True,
                'has_no_exception': False
            }
        }
    
    # Combined result check - only if all answered
    results = [qualifies_map.get(p) for p in practices_with_exception]
    
    # NEW: Check for final confirmation before transitioning to result status
    exception_confirmed = block1_state.get('exception_confirmed', False)
    
    if not exception_confirmed:
        return {
            'status': 'Triggered',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'Awaiting final confirmation of exception claim(s)',
                'has_exception_available': True,
                'has_no_exception': False,
                'is_all_answered': True,
                'answers': results
            }
        }

    if 'No' in results or 'Not sure' in results:
        # If any is "No" or "Not sure" -> Prohibited
        return {
            'status': 'Prohibited',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'One or more exception claims were denied or uncertain (answered "No" or "Not sure")',
                'has_exception_available': True,
                'has_no_exception': False
            }
        }
    
    # If we reached here, it means all were answered and all are 'Yes'
    # Check for evidence for EACH practice (since they need it "cho từng data value")
    evidence_map = block1_state.get('exception_evidence_map', {})
    
    all_evidence_provided = True
    for p in practices_with_exception:
        p_evidence = evidence_map.get(p, {})
        has_link = p_evidence.get('link', '')
        has_files = p_evidence.get('files', [])
        has_explanation = p_evidence.get('explanation', '')
        
        if not (has_link or has_files or has_explanation):
            all_evidence_provided = False
            break
            
    if all_evidence_provided:
        return {
            'status': 'Exception claimed',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'Evidence provided for all exception claims',
                'has_exception_available': True,
                'has_no_exception': False,
                'evidence_provided': True
            }
        }
    else:
        return {
            'status': 'Needs Review',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'Awaiting evidence for one or more exception claims',
                'has_exception_available': True,
                'has_no_exception': False,
                'evidence_provided': False
            }
        }
    
    # Default fallback
    return {
        'status': 'Triggered',
        'selected_practices': selected_practices,
        'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
        'details': {
            'reason': 'Awaiting exception qualification answer'
        }
    }


def ai_detects_high_risk():
    """
    High-Risk Classification check.
    Returns True if high-risk, False otherwise.
    """
    return False


def get_block2_status(profile_data, block1_result=None, block2_state=None, reset_state=False):
    """
    Block 2: High-Risk Classification.
    """
    if block2_state is None:
        block2_state = {}
    
    if reset_state:
        block2_state.clear()

    if block1_result:
        b1_status = block1_result.get('status', '')
        if b1_status == 'Prohibited':
            return {
                'status': 'De-activated',
                'details': {'reason': 'Block 1 Prohibited - High-risk classification assessment not applicable'}
            }
    
    ip = profile_data.get('intended_purpose', {}) or {}
    sector_domain = ip.get('sector_domain') or []
    if not isinstance(sector_domain, list):
        sector_domain = []
    safety_component = ip.get('safety_component', '')
    third_party_conformity = ip.get('third_party_conformity', '')

    # 1) Check for high-risk detection
    # PRESERVE confirmation
    if ai_detects_high_risk():
        high_risk_confirmed = block2_state.get('high_risk_confirmed', False)
        if high_risk_confirmed:
            return {
                'status': 'High-risk',
                'details': {
                    'reason': 'AI detected high-risk classification, user confirmed',
                    'trigger': 'ai_detection',
                },
            }
        return {
            'status': 'Triggered',
            'details': {
                'reason': 'AI detected high-risk classification',
                'trigger': 'ai_detection',
                'condition1': False,
                'condition2': False,
            },
        }

    # 3) Assessment logic: Q2 (Sector) and Q3 (Safety component)
    selected_high_risk_sectors = [
        s for s in sector_domain 
        if s and s not in ('Other / not listed', 'Other / not listed:', '')
    ]
    
    # Not assessed if Q2 not answered or Q3 not answered
    if not sector_domain or safety_component == '':
        return {
            'status': 'Not assessed',
            'details': {'reason': 'Please complete Section 4 (Q2 Sector and Q3 Safety) to assess high-risk status.'},
        }
    
    # Special case: Q3 Yes but Q4 not answered
    if safety_component == 'Yes' and third_party_conformity == '':
        return {
            'status': 'Not assessed',
            'details': {'reason': 'Safety component Yes but third-party conformity (Q4) not answered'},
        }

    # Condition 1: Q3=Yes AND Q4=Yes (Annex I)
    condition1 = safety_component == 'Yes' and third_party_conformity == 'Yes'
    # Condition 2: Any sector selected (Annex III)
    condition2 = len(selected_high_risk_sectors) > 0

    # 4) If neither triggered -> Not high-risk
    if not condition1 and not condition2:
        return {
            'status': 'Not high-risk',
            'details': {
                'reason': 'Based on your Profile inputs, this AI system is not classified as high-risk under the EU AI Act.',
                'condition1': False,
                'condition2': False,
            },
        }

    # 5) High-risk status: returned if either condition is met
    # UI will handle the confirmation flow based on block2_state
    trigger = 'both' if (condition1 and condition2) else ('condition1' if condition1 else 'condition2')
    
    # Return High-risk with full details for the frontend to render appropriate step
    result = {
        'status': 'High-risk',
        'details': {
            'reason': 'This AI system is classified as high-risk under the EU AI Act because it is a safety component of a product requiring third-party conformity assessment under EU harmonisation legislation (Annex I).' if condition1 else 'This AI system is classified as high-risk under the EU AI Act based on its sector of application (Annex III).',
            'condition1': condition1,
            'condition2': condition2,
            'selected_sectors': selected_high_risk_sectors,
            'trigger': trigger,
            'step': 'condition1_only' if condition1 else 'q1' # default step after confirmation
        },
    }
    
    # If already confirmed, potentially update the step or reason based on Annex III flow
    high_risk_confirmed = block2_state.get('high_risk_confirmed', False)
    if not high_risk_confirmed:
        return result

    # 6) User has confirmed → Progress through Annex III if applicable
    if condition1:
        # Condition 1 stays as is - confirmed high-risk
        return result

    # 7) Condition 2 only → Annex III Exemption Test flow
    # This part remains the same as before, but we are already in 'High-risk' status

    # 7) Condition 2 or Both → Annex III Exemption Test
    material_influence = block2_state.get('material_influence', '')
    narrow_tasks = block2_state.get('narrow_tasks') or []
    if not isinstance(narrow_tasks, list):
        narrow_tasks = []
    profiling = block2_state.get('profiling', '')
    exemption_evidence = block2_state.get('exemption_confirmed', False)
    # also check if evidence is present for legacy or automatic transition if desired, 
    # but let's stick to explicit confirmation for 'Exemption' status
    

    # Q1: Material Influence or Significant Risk?
    if material_influence == 'Not sure':
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Annex III Q1: Not sure – needs review',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q1',
            },
        }
    if material_influence == 'Yes':
        return {
            'status': 'High-risk',
            'details': {
                'reason': 'Annex III Q1: Material influence Yes → High-risk',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q1',
            },
        }

    if material_influence != 'No':
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Annex III: pending Q1 (Material influence)',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q1',
            },
        }

    # Q2: Task Type Selection
    none_of_above = 'None of above' in narrow_tasks or 'None of above' in [str(x) for x in narrow_tasks]
    specific_tasks = [t for t in narrow_tasks if t and str(t).strip() and str(t) != 'None of above']
    if not specific_tasks and not none_of_above:
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Annex III: pending Q2 (Task type selection)',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q2',
            },
        }
    if none_of_above:
        return {
            'status': 'High-risk',
            'details': {
                'reason': 'Annex III Q2: None of above → High-risk',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q2',
            },
        }

    # Q3: Performs Profiling?
    if profiling == 'Unknown':
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Annex III Q3: Profiling Unknown → Needs review',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q3',
            },
        }
    if profiling == 'Yes':
        return {
            'status': 'High-risk',
            'details': {
                'reason': 'Annex III Q3: Profiling Yes → High-risk',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q3',
            },
        }
    if profiling != 'No':
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Annex III: pending Q3 (Profiling)',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q3',
            },
        }

    # Check for evidence
    details_base = {
        'condition1': condition1,
        'condition2': condition2,
        'step': 'evidence',
        'exemption_evidence_file_name': block2_state.get('exemption_evidence_file_name', ''),
        'exemption_evidence_file_url': block2_state.get('exemption_evidence_file_url', ''),
        'exemption_evidence_saved_link': block2_state.get('exemption_evidence_saved_link', ''),
        'exemption_evidence_explanation': block2_state.get('exemption_evidence_explanation', ''),
    }

    if exemption_evidence:
        return {
            'status': 'Exemption',
            'details': {
                **details_base,
                'reason': 'Annex III: Profiling No + evidence provided → Not high-risk',
            },
        }
    
    return {
        'status': 'High-risk',
        'details': {
            **details_base,
            'reason': 'Annex III: Profiling No but no exemption evidence yet',
        }
    }


def get_block3_status(profile_data, block1_result=None, block3_state=None, reset_state=False):
    """
    Block 3: Transparency Obligation.
    """
    if block3_state is None:
        block3_state = {}

    if reset_state:
        block3_state.clear()
    
    if block1_result:
        b1_status = block1_result.get('status', '')
        if b1_status == 'Prohibited':
            return {
                'status': 'De-activated',
                'details': {'reason': 'Block 1 Prohibited - Transparency obligation assessment not applicable'}
            }
    
    capability_practices = profile_data.get('capability_practices', [])
    if not isinstance(capability_practices, list):
        capability_practices = []
    
    interacts_persons = profile_data.get('interacts_persons', '')
    synthetic_content = profile_data.get('synthetic_content', [])
    if not isinstance(synthetic_content, list):
        synthetic_content = []
    
    deployment_context = profile_data.get('deployment_context', '')
    affected_outputs = profile_data.get('affected_outputs', [])
    if not isinstance(affected_outputs, list):
        affected_outputs = []

    sector_domain = profile_data.get('sector_domain')
    if not sector_domain:
        ip = profile_data.get('intended_purpose', {}) or {}
        sector_domain = ip.get('sector_domain') or []
    if not isinstance(sector_domain, list):
        sector_domain = []
    
    if not sector_domain or not deployment_context or not affected_outputs or \
       not interacts_persons or not synthetic_content:
        return {
            'status': 'Not assessed',
            'details': {'reason': 'One or more transparency-related profile questions are not answered.'}
        }
    
    # Get 7 trigger cases
    triggers = []
    
    # Case 1: Section 4, Q2: "Biometric identification and categorisation"
    if any('Biometric identification and categorisation' in s for s in sector_domain):
        triggers.append('case1')
    
    # Case 2: Section 5, Q1: "General public / consumer-facing"
    if deployment_context == 'General public / consumer-facing':
        triggers.append('case2')
    
    # Case 3: Section 5, Q3: "Citizens / residents"
    if 'Citizens / residents' in affected_outputs:
        triggers.append('case3')
    
    # Case 4: Section 7, Q1: "Emotion recognition ..."
    if any('Emotion recognition in the workplace or in education settings' in p for p in capability_practices):
        triggers.append('case4')
    
    # Case 5: Section 7, Q1: "Biometric categorisation (sensitive traits)"
    if any('Biometric categorisation that infers or predicts sensitive traits' in p for p in capability_practices):
        triggers.append('case5')
    
    # Case 6: Section 7, Q2: "Yes"
    if interacts_persons == 'Yes':
        triggers.append('case6')
    
    # Case 7: Section 7, Q3: any except "No"
    if len(synthetic_content) > 0 and 'No' not in synthetic_content:
        triggers.append('case7')
    
    # Check for unknowns (if any specific question is 'Unknown')
    has_unknowns = (interacts_persons == 'Unknown' or deployment_context == 'Unknown')
    
    # 4) No triggers met → Not Applicable
    if len(triggers) == 0:
        return {
            'status': 'Not Applicable',
            'details': {'reason': 'Based on your Profile inputs, this AI system does not trigger transparency obligations under Article 50 of the EU AI Act.'}
        }
    
    # 5) Triggers met → Status: Triggered
    transparency_confirmed = block3_state.get('transparency_confirmed', False)
    
    if not transparency_confirmed:
        if has_unknowns:
            return {
                'status': 'Needs Review',
                'details': {
                    'reason': 'Triggers detected but Unknown values require review',
                    'triggers': triggers,
                    'has_unknowns': True
                }
            }
        
        return {
            'status': 'Triggered',
            'details': {
                'reason': 'Transparency triggers detected, awaiting confirmation',
                'triggers': triggers
            }
        }
    
    # 6) User Confirms → Exception Selection
    exception_options = block3_state.get('exception_options', [])
    if not isinstance(exception_options, list):
        exception_options = []
    
    # Map triggers to case groups
    case_groups = []
    if 'case1' in triggers or 'case4' in triggers or 'case5' in triggers:
        case_groups.append('group_biometric_emotion')
    if 'case6' in triggers:
        case_groups.append('group_direct_interaction')
    if 'case7' in triggers:
        case_groups.append('group_synthetic_content')
    if 'case2' in triggers or 'case3' in triggers:
        case_groups.append('group_public_exposure')
    
    # Exception options by group
    group_biometric_emotion_options = [
        'Permitted by law to detect, prevent or investigate criminal offences, as stated in Art. 50(3)',
        'None of the above (no exception for biometric/emotion recognition cases)'
    ]
    group_direct_interaction_options = [
        '"Obvious to the user" exception (no notice needed), as stated in Art. 50(1)',
        'Authorised by law to detect, prevent, investigate or prosecute criminal offences, as stated in Art. 50(1)',
        'None of the above (no exception for direct interaction case)'
    ]
    group_synthetic_content_options = [
        'Deepfake labelling exception (e.g., artistic / satire / fiction), as stated in Art. 50(4)',
        'None of the above (no exception for synthetic content case)'
    ]
    group_public_exposure_options = [
        'Authorised by law to detect, prevent, investigate or prosecute criminal offences, as stated in Art. 50(4)',
        'Human review is in place or a natural or legal person holds editorial responsibility for the publication of the content, as stated in Art. 50(4)',
        'None of the above (no exception for citizens/public-facing case)'
    ]
    
    # Check for "None of above"
    has_no_exception = any('None of the above' in opt for opt in exception_options)
    
    if has_no_exception:
        return {
            'status': 'Applies',
            'details': {
                'reason': '"None of the above" selected for at least one case group - transparency obligations apply',
                'triggers': triggers,
                'case_groups': case_groups
            }
        }
    
    # Check if valid exceptions for all groups
    has_exception_for_all = True
    if 'group_biometric_emotion' in case_groups:
        if not any(opt in group_biometric_emotion_options and 'None of the above' not in opt for opt in exception_options):
            has_exception_for_all = False
    if 'group_direct_interaction' in case_groups:
        if not any(opt in group_direct_interaction_options and 'None of the above' not in opt for opt in exception_options):
            has_exception_for_all = False
    if 'group_synthetic_content' in case_groups:
        if not any(opt in group_synthetic_content_options and 'None of the above' not in opt for opt in exception_options):
            has_exception_for_all = False
    if 'group_public_exposure' in case_groups:
        if not any(opt in group_public_exposure_options and 'None of the above' not in opt for opt in exception_options):
            has_exception_for_all = False
    
    # 7) Incomplete selections → Needs Review
    if not has_exception_for_all:
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Incomplete exception selections - not all case groups have valid exceptions',
                'triggers': triggers,
                'case_groups': case_groups
            }
        }
    
    # 8) Evidence check
    evidence_uploaded = block3_state.get('transparency_evidence_uploaded', False)
    evidence_saved_link = block3_state.get('transparency_evidence_saved_link', '')
    evidence_provided = evidence_uploaded or bool((evidence_saved_link or '').strip())
    
    if evidence_provided:
        return {
            'status': 'Exception',
            'details': {
                'reason': 'All triggered cases have valid exceptions with supporting evidence. Transparency obligations do not apply to this AI system.',
                'triggers': triggers,
                'case_groups': case_groups
            }
        }
    else:
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Valid exceptions for all groups but evidence not provided - needs review',
                'triggers': triggers,
                'case_groups': case_groups
            }
        }


def get_block4_status(profile_data, block1_result=None, block4_state=None, reset_state=False):
    """
    Block 4: GPAI Obligation.
    """
    if block4_state is None:
        block4_state = {}
    
    if reset_state:
        block4_state.clear()
    
    if block1_result:
        b1_status = block1_result.get('status', '')
        if b1_status == 'Prohibited':
            return {
                'status': 'De-activated',
                'details': {'reason': 'Block 1 Prohibited - GPAI obligation assessment not applicable'}
            }
    
    gpai_integration = profile_data.get('gpai_integration', '')
    
    if gpai_integration == '':
        return {
            'status': 'Not assessed',
            'details': {'reason': 'GPAI integration question not answered (Section 8, Q2)'}
        }
    
    if gpai_integration == 'No':
        return {
            'status': 'Not Applicable',
            'details': {
                'reason': 'Based on your Profile inputs, this AI system does not qualify as a general-purpose AI model, so GPAI obligations under Chapter V of the EU AI Act do not apply.',
                'gpai_integration': 'No'
            }
        }
    
    # Q2 Unknown → Needs Review
    if gpai_integration == 'Unknown':
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'In your Profile (Section 8, Q2), you indicated that it is Unknown whether this system is provided as a general-purpose AI (GPAI) model/component or integrates one. Please clarify this information to determine whether GPAI obligations under Chapter V of the EU AI Act apply to your system.',
                'gpai_integration': 'Unknown'
            }
        }
    
    # Q2 Yes → Triggered
    if gpai_integration == 'Yes':
        gpai_confirmed = block4_state.get('gpai_confirmed', False)
        
        if not gpai_confirmed:
            return {
                'status': 'Triggered',
                'details': {
                    'reason': 'Based on your Profile inputs, GPAI obligations apply to this AI system because: System is provided as or integrates a general-purpose AI (GPAI) model / component (Section 8, Q2).',
                    'gpai_integration': 'Yes'
                }
            }
        
        # Steps 2-5: Confirmed flow
        gpai_provider_answer = block4_state.get('gpai_provider_answer', '')
        
        if not gpai_provider_answer:
            # Step 2: Confirmed but provider role not yet selected
            return {
                'status': 'Needs Review',
                'details': {
                    'gpai_integration': 'Yes',
                    'gpai_confirmed': True
                }
            }
        
        # Steps 3-5: Provider role selected
        if gpai_provider_answer == 'Yes':
            return {
                'status': 'Applies',
                'details': {
                    'reason': 'GPAI integration confirmed and provider role selected - Chapter V obligations apply.',
                    'gpai_integration': 'Yes',
                    'gpai_confirmed': True,
                    'gpai_provider_answer': 'Yes'
                }
            }
        elif gpai_provider_answer == 'No':
            return {
                'status': 'Not Applicable',
                'details': {
                    'reason': 'GPAI integration confirmed but role is not a provider - Chapter V obligations do not apply.',
                    'gpai_integration': 'Yes',
                    'gpai_confirmed': True,
                    'gpai_provider_answer': 'No'
                }
            }
        else: # 'Not sure'
            return {
                'status': 'Needs Review',
                'details': {
                    'reason': 'GPAI integration confirmed but role selection requires review.',
                    'gpai_integration': 'Yes',
                    'gpai_confirmed': True,
                    'gpai_provider_answer': 'Not sure'
                }
            }

    return {
        'status': 'Not assessed',
        'details': {'reason': 'GPAI integration status unclear'}
    }


@csrf_exempt
@require_http_methods(["POST"])
def api_update_block2_state(request, agent_id):
    """
    Update Block 2 assessment state (confirmation, Annex III answers, evidence, etc.).
    
    Expected JSON body:
    {
        "high_risk_confirmed": true/false,
        "material_influence": "Yes" | "No" | "Not sure" | "",
        "narrow_tasks": ["task1", "task2", ...],
        "profiling": "Yes" | "No" | "Unknown" | "",
        "exemption_evidence_uploaded": true/false,
        "exemption_evidence_saved_link": "url string"
    }
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get path to agents.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        agents_file = mock_data_dir / 'agents.json'
        
        # Load existing agents
        existing_agents = []
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    existing_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing agents: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Could not load agents data'
                }, status=500)
        
        # Find agent by ID
        agent = next((a for a in existing_agents if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        # Get state update data
        data = json.loads(request.body)
        
        # Initialize assessment if not exists
        if 'assessment' not in agent:
            agent['assessment'] = {}
        
        # Initialize block2_state if not exists
        if 'block2_state' not in agent['assessment']:
            agent['assessment']['block2_state'] = {
                'high_risk_confirmed': False,
                'material_influence': '',
                'narrow_tasks': [],
                'profiling': '',
                'exemption_evidence_uploaded': False,
                'exemption_evidence_saved_link': '',
                'exemption_evidence_explanation': '',
                'exemption_confirmed': False,
                'exemption_evidence_file_name': '',
                'exemption_evidence_file_url': ''
            }
        
        # Update block2_state
        block2_state = agent['assessment']['block2_state']
        
        if 'high_risk_confirmed' in data:
            block2_state['high_risk_confirmed'] = bool(data['high_risk_confirmed'])
        if 'material_influence' in data:
            block2_state['material_influence'] = data.get('material_influence', '')
        if 'narrow_tasks' in data:
            block2_state['narrow_tasks'] = data.get('narrow_tasks', [])
        if 'profiling' in data:
            block2_state['profiling'] = data.get('profiling', '')
        if 'exemption_evidence_uploaded' in data:
            block2_state['exemption_evidence_uploaded'] = bool(data['exemption_evidence_uploaded'])
        if 'exemption_evidence_saved_link' in data:
            block2_state['exemption_evidence_saved_link'] = data.get('exemption_evidence_saved_link', '')
        if 'exemption_evidence_explanation' in data:
            block2_state['exemption_evidence_explanation'] = data.get('exemption_evidence_explanation', '')
        if 'exemption_confirmed' in data:
            block2_state['exemption_confirmed'] = bool(data['exemption_confirmed'])
        if 'exemption_evidence_file_name' in data:
            block2_state['exemption_evidence_file_name'] = data.get('exemption_evidence_file_name', '')
        if 'exemption_evidence_file_url' in data:
            block2_state['exemption_evidence_file_url'] = data.get('exemption_evidence_file_url', '')
        
        # Re-run assessment logic to get updated status
        if 'profile' in agent:
            assessment_state = agent.get('assessment', {})
            assessment_results = run_assessment_logic(agent['profile'], assessment_state)
            agent['assessment'] = assessment_results
        
        # Update agent in list
        for idx, a in enumerate(existing_agents):
            if str(a.get('id')) == str(agent_id):
                existing_agents[idx] = agent
                break
        
        # Save updated agents
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(existing_agents, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated Block 2 state for AI system ID: {agent_id}")
        
        # Return updated assessment results
        return JsonResponse({
            'success': True,
            'message': 'Block 2 state updated successfully',
            'assessment': agent.get('assessment', {})
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating Block 2 state: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_block3_state(request, agent_id):
    """
    Update Block 3 assessment state (confirmation, exception options, evidence, etc.).
    
    Expected JSON body:
    {
        "transparency_confirmed": true/false,
        "exception_options": ["option1", "option2", ...],
        "transparency_evidence_uploaded": true/false,
        "transparency_evidence_saved_link": "url string"
    }
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get path to agents.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        agents_file = mock_data_dir / 'agents.json'
        
        # Load existing agents
        existing_agents = []
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    existing_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing agents: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Could not load agents data'
                }, status=500)
        
        # Find agent by ID
        agent = next((a for a in existing_agents if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        # Get state update data
        data = json.loads(request.body)
        
        # Initialize assessment if not exists
        if 'assessment' not in agent:
            agent['assessment'] = {}
        
        # Initialize block3_state if not exists
        if 'block3_state' not in agent['assessment']:
            agent['assessment']['block3_state'] = {
                'transparency_confirmed': False,
                'exception_options': [],
                'transparency_evidence_uploaded': False,
                'transparency_evidence_saved_link': ''
            }
        
        # Update block3_state
        block3_state = agent['assessment']['block3_state']
        
        if 'transparency_confirmed' in data:
            block3_state['transparency_confirmed'] = bool(data['transparency_confirmed'])
        if 'exception_options' in data:
            block3_state['exception_options'] = data.get('exception_options', [])
        if 'transparency_evidence_uploaded' in data:
            block3_state['transparency_evidence_uploaded'] = bool(data['transparency_evidence_uploaded'])
        if 'transparency_evidence_saved_link' in data:
            block3_state['transparency_evidence_saved_link'] = data.get('transparency_evidence_saved_link', '')
        
        # Re-run assessment logic to get updated status
        if 'profile' in agent:
            assessment_state = agent.get('assessment', {})
            assessment_results = run_assessment_logic(agent['profile'], assessment_state)
            agent['assessment'] = assessment_results
        
        # Update agent in list
        for idx, a in enumerate(existing_agents):
            if str(a.get('id')) == str(agent_id):
                existing_agents[idx] = agent
                break
        
        # Save updated agents
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(existing_agents, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated Block 3 state for AI system ID: {agent_id}")
        
        # Return updated assessment results
        return JsonResponse({
            'success': True,
            'message': 'Block 3 state updated successfully',
            'assessment': agent.get('assessment', {})
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating Block 3 state: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_block4_state(request, agent_id):
    """
    Update Block 4 assessment state (confirmation, provider answer, etc.).
    
    Expected JSON body:
    {
        "gpai_confirmed": true/false,
        "gpai_provider_answer": "Yes" | "No" | "Not sure" | ""
    }
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get path to agents.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        agents_file = mock_data_dir / 'agents.json'
        
        # Load existing agents
        existing_agents = []
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    existing_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing agents: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Could not load agents data'
                }, status=500)
        
        # Find agent by ID
        agent = next((a for a in existing_agents if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        # Get state update data
        data = json.loads(request.body)
        
        # Initialize assessment if not exists
        if 'assessment' not in agent:
            agent['assessment'] = {}
        
        # Initialize block4_state if not exists
        if 'block4_state' not in agent['assessment']:
            agent['assessment']['block4_state'] = {
                'gpai_confirmed': False,
                'gpai_provider_answer': ''
            }
        
        # Update block4_state
        block4_state = agent['assessment']['block4_state']
        
        if 'gpai_confirmed' in data:
            block4_state['gpai_confirmed'] = bool(data['gpai_confirmed'])
        if 'gpai_provider_answer' in data:
            block4_state['gpai_provider_answer'] = data.get('gpai_provider_answer', '')
        
        # Re-run assessment logic to get updated status
        if 'profile' in agent:
            assessment_state = agent.get('assessment', {})
            assessment_results = run_assessment_logic(agent['profile'], assessment_state)
            agent['assessment'] = assessment_results
        
        # Update agent in list
        for idx, a in enumerate(existing_agents):
            if str(a.get('id')) == str(agent_id):
                existing_agents[idx] = agent
                break
        
        # Save updated agents
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(existing_agents, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated Block 4 state for AI system ID: {agent_id}")
        
        # Return updated assessment results
        return JsonResponse({
            'success': True,
            'message': 'Block 4 state updated successfully',
            'assessment': agent.get('assessment', {})
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating Block 4 state: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_block1_state(request, agent_id):
    """
    Update Block 1 assessment state (confirmation, exception claim, etc.).
    
    Expected JSON body:
    {
        "prohibited_confirmed": true/false,
        "claiming_exception": "Yes" | "No" | "",
        "exception_qualifies": "Yes" | "No" | "Not sure" | "",
        "exception_evidence_uploaded": true/false,
        "exception_evidence_saved_link": "url string",
        "no_exception_confirmed": true/false
    }
    """
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get path to agents.json file
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        agents_file = mock_data_dir / 'agents.json'
        
        # Load existing agents
        existing_agents = []
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    existing_agents = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing agents: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Could not load agents data'
                }, status=500)
        
        # Find agent by ID
        agent = next((a for a in existing_agents if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        # Get state update data
        data = json.loads(request.body)
        
        # Initialize assessment if not exists
        if 'assessment' not in agent:
            agent['assessment'] = {}
        
        # Initialize block1_state if not exists
        if 'block1_state' not in agent['assessment']:
            agent['assessment']['block1_state'] = {
                'prohibited_confirmed': False,
                'claiming_exception': '',
                'exception_qualifies': '',
                'exception_evidence_uploaded': False,
                'exception_evidence_saved_link': '',
                'no_exception_confirmed': False
            }
        
        # Update block1_state
        block1_state = agent['assessment']['block1_state']
        
        if 'prohibited_confirmed' in data:
            block1_state['prohibited_confirmed'] = bool(data['prohibited_confirmed'])
        if 'claiming_exception' in data:
            block1_state['claiming_exception'] = data.get('claiming_exception', '')
        if 'exception_qualifies' in data:
            block1_state['exception_qualifies'] = data.get('exception_qualifies', '')
        if 'exception_qualifies_map' in data:
            block1_state['exception_qualifies_map'] = data.get('exception_qualifies_map', {})
        if 'exception_evidence_map' in data:
            block1_state['exception_evidence_map'] = data.get('exception_evidence_map', {})
        if 'exception_evidence_uploaded' in data:
            block1_state['exception_evidence_uploaded'] = bool(data['exception_evidence_uploaded'])
        if 'exception_evidence_saved_link' in data:
            block1_state['exception_evidence_saved_link'] = data.get('exception_evidence_saved_link', '')
        if 'no_exception_confirmed' in data:
            block1_state['no_exception_confirmed'] = bool(data['no_exception_confirmed'])
        if 'exception_confirmed' in data:
            block1_state['exception_confirmed'] = bool(data['exception_confirmed'])
        if 'exception_conditions' in data:
            block1_state['exception_conditions'] = data.get('exception_conditions', [])
        if 'exception_explanation' in data:
            block1_state['exception_explanation'] = data.get('exception_explanation', '')
        if 'exception_evidence_files' in data:
            block1_state['exception_evidence_files'] = data.get('exception_evidence_files', [])
        
        # Re-run assessment logic to get updated status
        if 'profile' in agent:
            assessment_state = agent.get('assessment', {})
            assessment_results = run_assessment_logic(agent['profile'], assessment_state)
            agent['assessment'] = assessment_results
        
        # Update agent in list
        for idx, a in enumerate(existing_agents):
            if str(a.get('id')) == str(agent_id):
                existing_agents[idx] = agent
                break
        
        # Save updated agents
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(existing_agents, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated Block 1 state for AI system ID: {agent_id}")
        
        # Return updated assessment results
        return JsonResponse({
            'success': True,
            'message': 'Block 1 state updated successfully',
            'assessment': agent.get('assessment', {})
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating Block 1 state: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_delete_organization_files(request):
    """
    Delete files from organization.json and remove files from disk.
    
    Expected JSON body:
    {
        "files": [
            {
                "name": "filename.pdf",
                "url": "/static/governance/uploads/organization/uuid.pdf",
                "path": "governance/uploads/organization/uuid.pdf"
            },
            ...
        ]
    }
    """
    import logging
    from pathlib import Path
    from django.conf import settings
    
    logger = logging.getLogger(__name__)
    
    try:
        data = json.loads(request.body)
        files_to_delete = data.get('files', [])
        
        if not files_to_delete:
            return JsonResponse({
                'success': False,
                'error': 'No files provided'
            }, status=400)
        
        # Get paths
        mock_data_dir = Path(__file__).parent.parent / 'mock_data'
        org_file = mock_data_dir / 'organization.json'
        
        # Get static directory
        BASE_DIR = Path(__file__).parent.parent
        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else BASE_DIR / 'static'
        
        # Load existing organization data
        existing_data = {}
        if org_file.exists():
            try:
                with open(org_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load existing organization data: {e}")
                existing_data = {}
        
        # Get documents array
        documents = existing_data.get('documents', [])
        
        # Track deleted files
        deleted_files = []
        deleted_from_disk = []
        errors = []
        
        # Process each file to delete
        for file_info in files_to_delete:
            file_name = file_info.get('name', '')
            file_path = file_info.get('path', '')
            file_url = file_info.get('url', '')
            
            if not file_name:
                errors.append(f"Missing file name for file: {file_info}")
                continue
            
            # Remove from documents array (match by name)
            original_count = len(documents)
            documents = [doc for doc in documents if doc.get('name') != file_name]
            if len(documents) < original_count:
                deleted_files.append(file_name)
                logger.info(f"Removed {file_name} from documents array")
            else:
                logger.warning(f"File {file_name} not found in documents array")
            
            # Delete file from disk if path is provided
            if file_path:
                try:
                    # Construct full file path
                    full_file_path = static_dir / file_path
                    
                    if full_file_path.exists():
                        full_file_path.unlink()
                        deleted_from_disk.append(file_name)
                        logger.info(f"Deleted file from disk: {full_file_path}")
                    else:
                        logger.warning(f"File not found on disk: {full_file_path}")
                except Exception as e:
                    error_msg = f"Error deleting file {file_name} from disk: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
        
        # Update organization.json with remaining documents
        existing_data['documents'] = documents
        
        try:
            with open(org_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Updated organization.json after deleting {len(deleted_files)} file(s)")
        except Exception as e:
            error_msg = f"Error saving organization.json: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)
        
        # Return success response
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {len(deleted_files)} file(s)',
            'deleted_files': deleted_files,
            'deleted_from_disk': deleted_from_disk,
            'errors': errors if errors else None
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error deleting organization files: {str(e)}", exc_info=True)
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
    
    # Status mapping (fallback when explicit agent['status'] is missing)
    status_map = {
        'assessing': 'In progress',
        'reviewing': 'In progress',
        'compliant': 'In production',
        'non_compliant': 'Testing',
        'planned': 'Planned',
    }
    
    # Badge classes - Match React design colors
    status_badge_classes = {
        'Planned': 'bg-[#E5E7EB] text-[#6B7280]',
        'Testing': 'bg-[#FEF3C7] text-[#92400E]',
        'In production': 'bg-[#D1FAE5] text-[#065F46]',
        'Retired': 'bg-[#F3F4F6] text-[#4B5563]',
    }
    
    risk_badge_classes = {
        'Prohibited': 'bg-[#FEE2E2] text-[#991B1B]',
        'High-risk': 'bg-[#FED7AA] text-[#9A3412]',
        'Limited transparency': 'bg-[#FEF3C7] text-[#92400E]',
        'Minimal': 'bg-[#D1FAE5] text-[#065F46]',
        'Not assessed': 'bg-[#E5E7EB] text-[#6B7280]',
        'Not in scope': 'bg-[#F3F4F6] text-[#4B5563]',
    }
    
    compliance_badge_classes = {
        'Not started': 'bg-[#E5E7EB] text-[#6B7280]',
        'In progress': 'bg-[#DBEAFE] text-[#1E40AF]',
        'Compliant': 'bg-[#D1FAE5] text-[#065F46]',
        'Non-compliant': 'bg-[#FEE2E2] text-[#991B1B]',
        'Not in scope': 'bg-[#F3F4F6] text-[#4B5563]',
    }
    
    # Role mapping
    role_map = {
        'deployer': 'Deployer',
        'provider': 'Provider',
        'importer': 'Importer',
        'distributor': 'Distributor',
    }
    
    # Risk classification mapping (internal codes -> display labels)
    risk_map = {
        'limited_risks': 'Limited transparency',
        'high_risks': 'High-risk',
        'minimal_risks': 'Minimal',
        'not_assessed': 'Not assessed',
        'prohibited': 'Prohibited',
        'not_in_scope': 'Not in scope',
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
        # Normalize compliance status (handle 'non-compliant' vs 'non_compliant', etc.)
        compliance_status = (agent.get('compliance_status', 'assessing') or '').lower().replace('-', '_')
        # Prefer explicit status field if present; fallback to mapping from compliance_status
        status = agent.get('status')
        if not status:
            status = status_map.get(compliance_status, 'Planned')
            # Handle 'planned' status specially
            if compliance_status == 'planned':
                status = 'Planned'
        
        # Check if needs attention
        if compliance_status in ['assessing', 'reviewing']:
            systems_need_attention += 1
        
        # Map compliance status for display
        compliance_display_map = {
            'assessing': 'In progress',
            'reviewing': 'In progress',
            'compliant': 'Compliant',
            'non_compliant': 'Non-compliant',
            'not_started': 'Not started',
            'planned': 'Not started',
            'not_in_scope': 'Not in scope',
        }
        compliance_display = compliance_display_map.get(compliance_status, 'Not started')
        
        # Get risk classification
        risk_class = agent.get('risk_classification', 'limited_risks')
        risk_display = risk_map.get(risk_class, 'Not assessed')
        
        # Get owner (business unit)
        owner = agent.get('business_unit', '') or '—'
        
        # Get provider type - use provider_type field if available, otherwise map from vendor
        if 'provider_type' in agent:
            provider_type = agent.get('provider_type', 'Unknown')
        else:
            # Backward compatibility: map from vendor
            vendor = agent.get('vendor', '')
            provider_type = provider_type_map.get(vendor, 'Mixed' if vendor else 'In-house')
        
        # Generate mock last updated date (varying dates for different systems)
        # Use system index to create varied dates
        days_ago = [15, 18, 10, 5, 20][idx % 5]  # Cycle through different days
        last_updated_date = datetime.now() - timedelta(days=days_ago)
        last_updated = last_updated_date.strftime('%b %d, %Y')
        
        # Get roles - support both old format (ai_act_role) and new format (roles array)
        roles = agent.get('roles', [])
        if not roles and agent.get('ai_act_role'):
            # Backward compatibility: convert single role to array
            roles = [agent.get('ai_act_role')]
        
        # Map roles to display names
        roles_display = [role_map.get(role.lower(), role.title()) for role in roles]
        role_display = ', '.join(roles_display) if roles_display else 'Not specified'
        
        ai_systems.append({
            'id': agent.get('id'),
            'name': agent.get('name', 'Unnamed System'),
            'owner': owner,
            'status': status,
            'status_badge_class': status_badge_classes.get(status, 'bg-gray-100 text-gray-700'),
            'role': role_display,
            'roles': roles_display,  # Array for filtering
            'roles_raw': [r.lower() for r in roles],  # Raw lowercase for filter matching
            'risk_classification': risk_display,
            'risk_badge_class': risk_badge_classes.get(risk_display, 'bg-gray-100 text-gray-700'),
            'compliance_status': compliance_display,
            'compliance_badge_class': compliance_badge_classes.get(compliance_display, 'bg-gray-100 text-gray-700'),
            'last_updated': last_updated,
            'provider_type': provider_type,
        })
    
    # Default sort: newest systems (highest id) first
    try:
        ai_systems.sort(key=lambda s: int(s.get('id') or 0), reverse=True)
    except Exception:
        pass

    # Deployment context options: load from mock data file + append any unique values from agents
    deployment_context_options = _load_deployment_context_options()
    from_agents = set()
    for agent in agents_data:
        dc = agent.get('deployment_context') or ''
        if dc.strip():
            from_agents.add(dc.strip())
    new_from_agents = sorted(from_agents - set(deployment_context_options))
    if new_from_agents:
        deployment_context_options = list(deployment_context_options) + new_from_agents
        _save_deployment_context_options(deployment_context_options)

    return render(request, 'governance/pages/ai_inventory.html', {
        'company': company,
        'subpage': 'ai_inventory',
        'breadcrumbs': breadcrumbs,
        'ai_systems': ai_systems,
        'systems_need_attention': systems_need_attention,
        'deployment_context_options': deployment_context_options,
    })


def _ai_systems_for_compliance_modal():
    """Build minimal AI systems list for New Compliance Project modal (id, name, status, risk)."""
    agents_data = get_mock_agents()
    status_map = {'assessing': 'In progress', 'reviewing': 'In progress', 'compliant': 'In production',
                  'non_compliant': 'Testing', 'planned': 'Planned'}
    risk_map = {'limited_risks': 'Limited transparency', 'high_risks': 'High-risk', 'minimal_risks': 'Minimal',
                'not_assessed': 'Not assessed', 'prohibited': 'Prohibited', 'not_in_scope': 'Not in scope'}
    status_badge_classes = {'Planned': 'bg-[#E5E7EB] text-[#6B7280]', 'Testing': 'bg-[#FEF3C7] text-[#92400E]',
                            'In production': 'bg-[#D1FAE5] text-[#065F46]', 'Retired': 'bg-[#F3F4F6] text-[#4B5563]'}
    risk_badge_classes = {'Prohibited': 'bg-[#FEE2E2] text-[#991B1B]', 'High-risk': 'bg-[#FED7AA] text-[#9A3412]',
                          'Limited transparency': 'bg-[#FEF3C7] text-[#92400E]', 'Minimal': 'bg-[#D1FAE5] text-[#065F46]',
                          'Not assessed': 'bg-[#E5E7EB] text-[#6B7280]', 'Not in scope': 'bg-[#F3F4F6] text-[#4B5563]'}
    out = []
    for agent in agents_data:
        compliance_status = (agent.get('compliance_status', 'assessing') or '').lower().replace('-', '_')
        status = agent.get('status') or status_map.get(compliance_status, 'Planned')
        risk_class = agent.get('risk_classification', 'limited_risks')
        risk_display = risk_map.get(risk_class, 'Not assessed')
        out.append({
            'id': agent.get('id'),
            'name': agent.get('name', 'Unnamed System'),
            'status': status,
            'status_badge_class': status_badge_classes.get(status, 'bg-[#E5E7EB] text-[#6B7280]'),
            'risk_classification': risk_display,
            'risk_badge_class': risk_badge_classes.get(risk_display, 'bg-[#E5E7EB] text-[#6B7280]'),
        })
    out.sort(key=lambda s: int(s.get('id') or 0), reverse=True)
    return out


def compliance_hub(request):
    """
    Compliance page - Digital Regulation Hubs.
    """
    ensure_governance_platform(request)
    company = MockCompany()
    
    breadcrumbs = [
        {"name": "Compliance", "url": request.build_absolute_uri()},
    ]
    return render(request, 'governance/pages/compliance_hub.html', {
        'company': company,
        'subpage': 'compliance',
        'breadcrumbs': breadcrumbs,
    })


def compliance(request):
    """
    Compliance Projects view.
    """
    ensure_governance_platform(request)
    company = MockCompany()
    
    framework = request.GET.get('framework')
    
    # Check if viewing archived
    view_status = request.GET.get('view', 'active')
    show_archived = (view_status == 'archived')
    
    breadcrumbs = [
        {"name": "Compliance", "url": "/compliance/"},
    ]
    if framework == 'eu_ai_act':
        breadcrumbs.append({"name": "EU AI Act", "url": request.build_absolute_uri()})
    
    if show_archived:
        breadcrumbs.append({"name": "Archived", "url": request.build_absolute_uri()})

    projects = get_compliance_projects(archived=show_archived)
    total_projects = len(projects)
    
    # Active are those Progress not yet 100% (of the current set)
    active_projects = sum(1 for p in projects if p.get('progress', 0) < 100)
    
    # Not compliant: same logic as active/in-progress (progress < 100%) as requested
    not_compliant_count = active_projects
    ai_systems_for_modal = _ai_systems_for_compliance_modal()

    return render(request, 'governance/pages/compliance.html', {
        'company': company,
        'subpage': 'compliance',
        'breadcrumbs': breadcrumbs,
        'projects': projects,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'not_compliant_count': not_compliant_count,
        'ai_systems_for_modal': ai_systems_for_modal,
        'view_status': view_status,
        'framework': framework,
    })


@csrf_exempt
@require_http_methods(["GET"])
def api_compliance_skills(request):
    """
    Get a list of available AI Act compliance skills from the artifacts.
    Uses GovernanceAgentService which handles discovery and metadata.
    """
    try:
        from .infrastructure.services.governance_agent_service import get_governance_agent_service
        agent = get_governance_agent_service()
        
        # Format for frontend
        skills_list = []
        for skill_id in agent.list_available_skills():
            meta = agent.skills.get(skill_id)
            skills_list.append({
                'id': skill_id,
                'name': skill_id.replace('-', ' ').title(),
                'description': meta.description if meta else "",
                'path': meta.path if meta else ""
            })
            
        return JsonResponse({
            'success': True,
            'skills': skills_list
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in api_compliance_skills: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_ai_scan(request):
    """
    Perform an AI Agent Scan for a compliance project.
    Supports Logic 1 (no upload) and Logic 2 (with code/dataset upload).
    
    Expected JSON:
    {
        "project_id": "...",
        "tool_id": "...",
        "code_files": ["path/to/file1.py", ...],  # Optional - Logic 2
        "dataset_files": ["path/to/file1.csv", ...]  # Optional - Logic 2
    }
    """
    import logging
    from pathlib import Path
    import json
    
    logger = logging.getLogger(__name__)
    
    try:
        body = json.loads(request.body)
        project_id = body.get('project_id')
        tool_id = body.get('tool_id', 'ai-governance')
        # Optional: specific AI System / agent to use for this scan
        requested_agent_id = body.get('agent_id')
        code_files = body.get('code_files', [])
        dataset_files = body.get('dataset_files', [])
        
        if not project_id:
            return JsonResponse({'success': False, 'error': 'project_id is required'}, status=400)
            
        # Get project detail
        from .mock_data import get_compliance_detail, get_mock_agents
        project = get_compliance_detail(project_id)
        if not project:
            return JsonResponse({'success': False, 'error': f'Project {project_id} not found'}, status=404)
        
        # Check if files are uploaded (Logic 2)
        if code_files or dataset_files:
            logger.info(f"[COMPLIANCE AI SCAN] Logic 2: Processing uploaded files for project {project_id}")
            logger.info(f"  Code files: {len(code_files)}")
            logger.info(f"  Dataset files: {len(dataset_files)}")
            
            # Determine agent_id: prefer explicit agent_id from request, fallback to first AI system in project
            agent_id = requested_agent_id
            if not agent_id:
                ai_systems = project.get('ai_systems', [])
                if not ai_systems:
                    return JsonResponse({'success': False, 'error': 'Project has no AI systems'}, status=400)
                
                first_system = ai_systems[0] if isinstance(ai_systems[0], dict) else {'id': ai_systems[0]}
                agent_id = first_system.get('id') if isinstance(first_system, dict) else first_system
            
            # Create a temporary request-like object to call api_assess_risk_evaluation
            # We'll manually call the logic instead
            from django.http import HttpRequest
            from io import BytesIO
            
            temp_request = HttpRequest()
            temp_request.method = 'POST'
            # Set body using _body (private attribute) since body is read-only
            body_data = json.dumps({
                'code_files': code_files,
                'dataset_files': dataset_files,
                'tool_id': tool_id  # Pass tool_id to focus assessment on specific skill
            }).encode('utf-8')
            temp_request._body = body_data
            temp_request._stream = BytesIO(body_data)
            temp_request.META = request.META.copy()
            
            # Call the risk evaluation AI scan logic (Logic 2)
            result = api_risk_evaluation_ai_scan(temp_request, agent_id)
            
            # Convert response to compliance scan report format
            if hasattr(result, 'content'):
                result_data = json.loads(result.content)
                if result_data.get('success') and result_data.get('assessment'):
                    assessment = result_data['assessment']
                    
                    # Map to compliance report format
                    report = {
                        'score': 75,  # Default score
                        'compliance_status': 'Completed',
                        'risk_classification': assessment.get('risk_classification', {}),
                        'summary': assessment.get('initial_assessment', 'Assessment completed from uploaded code execution.'),
                        'detailed_output': [],
                        'recommended_skills': assessment.get('recommended_skills', []),
                        'next_steps': [],
                        'report_md': assessment.get('markdown_output', ''),
                        'report_file': assessment.get('markdown_output_file', '')
                    }
                    
                    return JsonResponse({
                        'success': True,
                        'report': report
                    })
            
            return result  # Return original response if mapping fails
            
        else:
            # Logic 1: No upload - Use Governance AI Agent full flow
            logger.info(f"[COMPLIANCE AI SCAN] Logic 1: Running Governance AI Agent for project {project_id}")
            
            # Determine agent_id: prefer explicit agent_id from request, fallback to first AI system in project
            agent_id = requested_agent_id
            if not agent_id:
                ai_systems = project.get('ai_systems', [])
                if not ai_systems:
                    return JsonResponse({'success': False, 'error': 'Project has no AI systems'}, status=400)
                
                first_system = ai_systems[0] if isinstance(ai_systems[0], dict) else {'id': ai_systems[0]}
                agent_id = first_system.get('id') if isinstance(first_system, dict) else first_system
            
            # Get agent data to build system description
            agents_data = get_mock_agents()
            agent = next((a for a in agents_data if str(a.get('id')) == str(agent_id)), None)
            
            if not agent:
                # Fallback: Use project name and description
                system_description = f"Compliance project: {project.get('name', 'Unknown Project')}. {project.get('description', '')}"
            else:
                # Build system_description from agent profile (same as risk evaluation)
                profile = agent.get('profile', {})
                agent_name = agent.get('name', '') or agent.get('system_name', '')
                
                system_description_parts = []
                if agent_name:
                    system_description_parts.append(f"AI System Name: {agent_name}")
                if profile.get('purpose'):
                    system_description_parts.append(f"Purpose: {profile.get('purpose')}")
                if profile.get('deployment_context'):
                    system_description_parts.append(f"Deployment context: {profile.get('deployment_context')}")
                if agent.get('risk_classification'):
                    system_description_parts.append(f"Risk Classification: {agent.get('risk_classification')}")
                
                system_description = ". ".join(system_description_parts) if system_description_parts else f"AI System: {agent_name}"
            
            # Create temporary request to call api_assess_risk_evaluation (Logic 1)
            from django.http import HttpRequest
            from io import BytesIO
            
            temp_request = HttpRequest()
            temp_request.method = 'POST'
            # Set body using _body (private attribute) since body is read-only
            body_data = json.dumps({
                'tool_id': tool_id  # Pass tool_id to focus assessment on specific skill
            }).encode('utf-8')  # No files = Logic 1
            temp_request._body = body_data
            temp_request._stream = BytesIO(body_data)
            temp_request.META = request.META.copy()
            
            # Call the risk evaluation AI scan logic (Logic 1)
            result = api_risk_evaluation_ai_scan(temp_request, agent_id)
            
            # Convert response to compliance scan report format
            if hasattr(result, 'content'):
                result_data = json.loads(result.content)
                if result_data.get('success') and result_data.get('assessment'):
                    assessment = result_data['assessment']
                    
                    # Calculate score from risk classification
                    risk_category = assessment.get('risk_classification', {})
                    if isinstance(risk_category, dict):
                        category = risk_category.get('category', 'Not assessed')
                    else:
                        category = str(risk_category)
                    
                    score = 75  # Default
                    if isinstance(category, str):
                        cat_lower = category.lower()
                        if 'unacceptable' in cat_lower or 'prohibited' in cat_lower:
                            score = 20
                        elif 'high' in cat_lower:
                            score = 40
                        elif 'limited' in cat_lower:
                            score = 70
                        elif 'minimal' in cat_lower:
                            score = 90
                    
                    # Map to compliance report format
                    report = {
                        'score': score,
                        'compliance_status': 'Completed',
                        'risk_classification': assessment.get('risk_classification', {}),
                        'summary': assessment.get('initial_assessment', 'Assessment completed using Governance AI Agent.'),
                        'detailed_output': [],
                        'recommended_skills': assessment.get('recommended_skills', []),
                        'next_steps': [],
                        'report_md': assessment.get('markdown_output', ''),
                        'report_file': assessment.get('markdown_output_file', '')
                    }
                    
                    return JsonResponse({
                        'success': True,
                        'report': report
                    })
            
            return result  # Return original response if mapping fails
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in api_ai_scan: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def serve_scan_report(request, filename):
    """
    Serve a scan report MD file for download or inline viewing.
    GET ?download=true → download as .md file
    GET → return JSON with markdown content for rendering in UI
    """
    from pathlib import Path

    reports_dir = Path(settings.BASE_DIR) / "scan_reports"
    file_path = reports_dir / filename

    # Security: prevent path traversal
    try:
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(reports_dir.resolve())):
            return JsonResponse({'success': False, 'error': 'Invalid path'}, status=403)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid path'}, status=403)

    if not file_path.exists():
        return JsonResponse({'success': False, 'error': 'Report not found'}, status=404)

    content = file_path.read_text(encoding='utf-8')

    # Download mode
    if request.GET.get('download') == 'true':
        from django.http import HttpResponse
        response = HttpResponse(content, content_type='text/markdown; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    # Inline mode: return MD content as JSON for frontend rendering
    return JsonResponse({
        'success': True,
        'filename': filename,
        'content': content
    })


def compliance_detail(request, project_id):

    """
    Compliance Project Detail page.
    Data loaded from mock_data/compliance_details.json.
    """
    ensure_governance_platform(request)
    company = MockCompany()
    
    project = get_compliance_detail(project_id)
    if not project:
        from django.http import Http404
        raise Http404("Compliance project not found")
    
    # Ensure project has an explicit agent_id for the linked AI System
    try:
        if 'agent_id' not in project:
            ai_systems = project.get('ai_systems', [])
            if ai_systems:
                first_system = ai_systems[0] if isinstance(ai_systems[0], dict) else {'id': ai_systems[0]}
                project['agent_id'] = first_system.get('id') if isinstance(first_system, dict) else first_system
    except Exception:
        # Fail silently; template will just not have data-agent-id
        pass
    
    breadcrumbs = [
        {"name": "Compliance", "url": "/compliance/"},
        {"name": "EU AI Act", "url": "/compliance/projects/?framework=eu_ai_act"},
        {"name": project.get('name', 'Detail'), "url": request.build_absolute_uri()},
    ]
    return render(request, 'governance/pages/compliance_detail.html', {
        'company': company,
        'subpage': 'compliance',
        'breadcrumbs': breadcrumbs,
        'project': project,
    })


@require_POST
def update_task_status_view(request):
    """
    Update a compliance task status.
    Expects JSON data: { "project_id": "...", "task_id": "...", "status": "..." }
    """
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        task_id = data.get('task_id')
        status = data.get('status')
        
        if not all([project_id, task_id, status]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
            
        from .mock_data import update_compliance_task_status
        success = update_compliance_task_status(project_id, task_id, status)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to update status'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_task_notes_view(request):
    """
    Get notes for a specific task.
    Params: project_id, task_id
    """
    project_id = request.GET.get('project_id')
    task_id = request.GET.get('task_id')
    
    if not all([project_id, task_id]):
        return JsonResponse({'success': False, 'error': 'Missing required params'}, status=400)
        
    from .mock_data import get_compliance_task_notes
    notes = get_compliance_task_notes(project_id, task_id)
    return JsonResponse({'success': True, 'notes': notes})


@require_POST
def add_task_note_view(request):
    """
    Add a note to a task.
    Expects JSON: { "project_id", "task_id", "content" }
    """
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        task_id = data.get('task_id')
        content = data.get('content')
        
        if not all([project_id, task_id, content]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
            
        from .mock_data import add_compliance_task_note
        new_note = add_compliance_task_note(project_id, task_id, content)
        
        if new_note:
            return JsonResponse({'success': True, 'note': new_note})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to add note'}, status=500)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_assignees_view(request):
    """
    Get list of assignees for a project.
    Params: project_id
    """
    project_id = request.GET.get('project_id')
    if not project_id:
        return JsonResponse({'success': False, 'error': 'Missing project_id'}, status=400)
    
    from .mock_data import get_compliance_assignees
    assignees = get_compliance_assignees(project_id)
    return JsonResponse({'success': True, 'assignees': assignees})


@require_POST
def add_new_assignee_view(request):
    """
    Add a new assignee to the project.
    Expects JSON: { "project_id", "name", "email" }
    """
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        name = data.get('name')
        email = data.get('email')
        
        if not all([project_id, name, email]):
             return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
             
        from .mock_data import add_new_assignee_to_project
        new_assignee = add_new_assignee_to_project(project_id, name, email)
        
        if new_assignee:
            return JsonResponse({'success': True, 'assignee': new_assignee})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to add assignee'}, status=500)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def update_task_assignee_view(request):
    """
    Update a task's assignee.
    Expects JSON: { "project_id", "task_id", "assignee_name" }
    """
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        task_id = data.get('task_id')
        assignee_name = data.get('assignee_name')
        
        if not all([project_id, task_id, assignee_name]):
             return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
             
        from .mock_data import update_compliance_task_assignee
        success = update_compliance_task_assignee(project_id, task_id, assignee_name)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to update assignee'}, status=500)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@require_POST
def create_compliance_project_view(request):
    """
    Create a new compliance project.
    Expects JSON: { "name": "...", "ai_system_ids": ["1", "2"] }
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        ai_system_ids = data.get('ai_system_ids', [])
        
        if not ai_system_ids:
            return JsonResponse({'success': False, 'error': 'No AI systems selected'}, status=400)
            
        # Resolve AI system details using the helper
        all_systems = _ai_systems_for_compliance_modal()
        selected_systems = [s for s in all_systems if str(s['id']) in map(str, ai_system_ids)]
        
        if not selected_systems:
            return JsonResponse({'success': False, 'error': 'Selected AI systems not found'}, status=404)
        
        from .mock_data import create_compliance_project
        new_project = create_compliance_project(name, selected_systems)
        
        if new_project:
            return JsonResponse({'success': True, 'project': new_project})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to create project'}, status=500)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def archive_projects_view(request):
    """Archive a list of projects."""
    try:
        data = json.loads(request.body)
        project_ids = data.get('project_ids', [])
        
        if not project_ids:
            return JsonResponse({'success': False, 'error': 'No projects selected'}, status=400)
            
        from .mock_data import archive_compliance_projects
        success = archive_compliance_projects(project_ids)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to archive projects'}, status=500)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def delete_projects_view(request):
    """Delete a list of projects."""
    try:
        data = json.loads(request.body)
        project_ids = data.get('project_ids', [])
        
        if not project_ids:
            return JsonResponse({'success': False, 'error': 'No projects selected'}, status=400)
            
        from .mock_data import delete_compliance_projects
        success = delete_compliance_projects(project_ids)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to delete projects'}, status=500)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def restore_projects_view(request):
    """Restore a list of projects."""
    try:
        data = json.loads(request.body)
        project_ids = data.get('project_ids', [])
        
        if not project_ids:
            return JsonResponse({'success': False, 'error': 'No projects selected'}, status=400)
            
        from .mock_data import restore_compliance_projects
        success = restore_compliance_projects(project_ids)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to restore projects'}, status=500)
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def ai_system_detail(request, agent_id):
    """
    AI System Detail page - Shows detailed information about a specific AI system.
    Displays Profile, Assessment, and Result tabs.
    """
    ensure_governance_platform(request)
    
    company = MockCompany()
    
    # Get agent data from agents.json
    agents_data = get_mock_agents()
    agent = next((a for a in agents_data if str(a.get('id')) == str(agent_id)), None)
    
    if not agent:
        from django.http import Http404
        raise Http404("AI System not found")
    
    # Load uploaded documents from agent data (if document field exists)
    uploaded_documents = []
    if agent.get('document'):
        # Single document
        doc = agent.get('document')
        from datetime import datetime
        uploaded_at = doc.get('uploaded_at', datetime.now().isoformat())
        try:
            uploaded_date = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
            time_ago = (datetime.now() - uploaded_date.replace(tzinfo=None)).total_seconds() / 60
            if time_ago < 1:
                uploaded_text = 'just now'
            elif time_ago < 60:
                uploaded_text = f'{int(time_ago)} mins ago'
            elif time_ago < 1440:
                uploaded_text = f'{int(time_ago / 60)} hours ago'
            else:
                uploaded_text = f'{int(time_ago / 1440)} days ago'
        except:
            uploaded_text = 'recently'
        
        uploaded_documents.append({
            'name': doc.get('name', 'Unknown'),
            'uploaded': uploaded_text,
            'url': doc.get('url', ''),
            'path': doc.get('path', ''),
            'size': doc.get('size', 0)
        })
    elif agent.get('documents'):
        # Multiple documents (if array exists)
        for doc in agent.get('documents', []):
            from datetime import datetime
            uploaded_at = doc.get('uploaded_at', datetime.now().isoformat())
            try:
                uploaded_date = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
                time_ago = (datetime.now() - uploaded_date.replace(tzinfo=None)).total_seconds() / 60
                if time_ago < 1:
                    uploaded_text = 'just now'
                elif time_ago < 60:
                    uploaded_text = f'{int(time_ago)} mins ago'
                elif time_ago < 1440:
                    uploaded_text = f'{int(time_ago / 60)} hours ago'
                else:
                    uploaded_text = f'{int(time_ago / 1440)} days ago'
            except:
                uploaded_text = 'recently'
            
            uploaded_documents.append({
                'name': doc.get('name', 'Unknown'),
                'uploaded': uploaded_text,
                'url': doc.get('url', ''),
                'path': doc.get('path', ''),
                'size': doc.get('size', 0)
            })

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

    # Q1 "In what context will this AI system be deployed?" – same options as Deployment Context list; Other: handled separately in template
    deployment_contexts = _load_deployment_context_options()

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
    
    # Get organization default roles from organization.json Section 3 Q2 (if available)
    from pathlib import Path
    mock_data_dir = Path(__file__).parent.parent / 'mock_data'
    org_file = mock_data_dir / 'organization.json'
    role_map = {
        'provider': 'Provider',
        'deployer': 'Deployer',
        'distributor': 'Distributor',
        'importer': 'Importer'
    }
    org_default_role = 'Deployer'  # fallback single (for JS backward compat)
    org_default_roles_list = []   # list of display names e.g. ['Provider', 'Deployer']
    org_default_roles_display = 'Deployer'  # "Provider, Deployer" for question text
    org_default_roles_json = '[]'  # JSON array for JS

    if org_file.exists():
        try:
            with open(org_file, 'r', encoding='utf-8') as f:
                org_data = json.load(f)
                scope_data = org_data.get('scope', {})
                roles = scope_data.get('q2_roles', [])
                if roles and len(roles) > 0:
                    org_default_roles_list = [
                        role_map.get(r.lower(), r.title()) for r in roles
                    ]
                    org_default_roles_display = ', '.join(org_default_roles_list)
                    org_default_role = org_default_roles_list[0]
                    org_default_roles_json = json.dumps(org_default_roles_list)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not load organization data for default role: {e}")

    return render(request, 'governance/pages/ai_system_detail.html', {
        'company': company,
        'subpage': 'ai_system_detail',
        'breadcrumbs': breadcrumbs,
        'agent': agent,
        'agent_id': agent_id,  # Pass agent_id to template for API calls
        'org_default_role': org_default_role,
        'org_default_roles_display': org_default_roles_display,
        'org_default_roles_list': org_default_roles_list,
        'org_default_roles_json': org_default_roles_json,
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

@csrf_exempt
@require_POST
def governance_autofill_api(request):
    """
    API endpoint for AI-assisted form autofill from documents.
    Accepts: { 'file_paths': [...], 'form_type': 'organization'|'ai_system' }
    """
    try:
        data = json.loads(request.body)
        file_paths = data.get('file_paths', [])
        form_type = data.get('form_type', 'organization')
        
        if not file_paths:
            return JsonResponse({'success': False, 'error': 'No file paths provided'})
            
        from .infrastructure.services.autofill.autofill_service import AutofillService
        service = AutofillService()
        
        # Define fields metadata based on form_type
        fields_metadata = []
        if form_type == 'organization':
            fields_metadata = [
                # Section 2: Organization Profile
                {"name": "entity_name", "type": "text"},
                {"name": "registration_number", "type": "text"},
                {"name": "headquarter_address", "type": "text"},
                {"name": "country", "type": "select", "options": ["United Kingdom", "United States", "France", "Germany", "Vietnam", "Other"]},
                {"name": "postal_code", "type": "text"},
                {"name": "legal_representative", "type": "text"},
                {"name": "contact_email", "type": "email"},
                {"name": "contact_phone", "type": "phone"},
                {"name": "public_authority", "type": "radio", "options": ["Yes", "No"]},
                {"name": "compliance_owner_name", "type": "text"},
                {"name": "compliance_owner_email", "type": "email"},
                {"name": "department", "type": "text"},
                
                # Section 3: Scope / Applicability Screening
                {"name": "scope_use_default_roles", "type": "radio", "options": ["Yes", "No"]},
                {"name": "scope_typical_roles", "type": "checkbox", "options": ["Provider", "Deployer", "Importer", "Distributor"]},
                {"name": "scope_place_on_eu_market", "type": "radio", "options": ["Yes", "No"]},
                {"name": "scope_deployed_in_eu", "type": "radio", "options": ["Yes", "No"]},
                {"name": "scope_affects_eu_persons", "type": "radio", "options": ["Yes", "No"]},
                
                # Section 4: Governance Setup (Internal Controls)
                {"name": "governance_has_policies", "type": "radio", "options": ["Yes", "No", "In progress"]},
                {"name": "governance_policy_link", "type": "text"},
                {"name": "governance_has_escalation_path", "type": "radio", "options": ["Yes", "No"]},
                {"name": "governance_has_register", "type": "radio", "options": ["Yes", "No"]},
                {"name": "governance_register_link", "type": "text"},
                {"name": "governance_has_version_history", "type": "radio", "options": ["Yes (You will be asked to provide evidence per system)", "No"]},
                {"name": "governance_has_vendor_assessment", "type": "radio", "options": ["Yes", "No", "Not Applicable"]},
                
                # Section 5: AI Literacy (Mandatory Requirement)
                {"name": "literacy_teams_using_ai", "type": "checkbox", "options": ["Product / Engineering", "Data / ML team", "Operations / Analysts", "HR / Recruitment", "Compliance / Legal", "Customer support", "Sales / Marketing", "Senior management", "External contractors / service providers", "Other"]},
                {"name": "literacy_number_of_users", "type": "number"},
                {"name": "literacy_has_training", "type": "radio", "options": ["Yes [implemented]", "Partly implemented", "No", "Planned"]},
                {"name": "literacy_training_content", "type": "checkbox", "options": ["Understanding AI limitations and errors", "Bias and discrimination risks", "Proper human oversight / how to challenge AI outputs", "Security and misuse risks", "Reporting issues or incidents", "Role-specific guidance (e.g., HR / compliance / operations)"]},
                {"name": "literacy_has_evidence", "type": "radio", "options": ["Yes", "No"]},
                {"name": "literacy_training_refreshed", "type": "radio", "options": ["Yes", "No", "Not sure"]},
            ]
        elif form_type == 'ai_system' or form_type == 'ai_system_full':
            # Full profile autofill for AI System Detail page
            # Includes all 8 sections for comprehensive document analysis
            fields_metadata = [
                # Section 2: System Identity
                {"name": "ai_system_name", "type": "text"},
                {"name": "internal_system_id", "type": "text"},
                {"name": "commercial_name", "type": "text"},
                {"name": "owner_name", "type": "text"},
                {"name": "owner_email", "type": "email"},
                {"name": "owner_department", "type": "text"},
                {"name": "system_status", "type": "select", "options": ["Planned", "In development", "Testing / Pilot", "In use (production)", "Retired"]},
                {"name": "go_live_date", "type": "date"},
                {"name": "part_of_product", "type": "radio", "options": ["Yes", "No"]},
                {"name": "product_service_name", "type": "text"},
                {"name": "vendor_name", "type": "text"},
                {"name": "business_unit", "type": "text"},
                {"name": "intended_purpose", "type": "text"},
                
                # Section 3: Source & Operator Role
                {"name": "default_role_apply", "type": "radio", "options": ["Yes", "No"]},
                {"name": "roles", "type": "checkbox", "options": ["Provider", "Deployer", "Distributor", "Importer"]},
                {"name": "system_source", "type": "radio", "options": ["In-house", "Vendor / Third-party", "Mixed", "Unknown"]},
                {"name": "modify_customize", "type": "radio", "options": ["Yes", "No", "Unknown"]},
                {"name": "eu_usage", "type": "radio", "options": ["Yes", "No", "Planned", "Unknown"]},
                {"name": "eu_effect", "type": "radio", "options": ["Yes", "No", "Planned", "Unknown"]},
                
                # Section 4: Intended Purpose
                {"name": "sector_domain", "type": "checkbox", "options": ["Biometric identification and categorisation", "Critical infrastructure management", "Education & vocational training", "Employment & workforce management", "Access to essential private or public services & benefits", "Law enforcement", "Migration, asylum & border control", "Justice & democratic processes"]},
                {"name": "safety_component", "type": "radio", "options": ["Yes", "No"]},
                {"name": "third_party_conformity", "type": "radio", "options": ["Yes", "No"]},
                
                # Sections 5-6: Deployment & Workflow
                {"name": "deployment_context", "type": "text"},
                {"name": "system_users", "type": "checkbox", "options": ["Internal employees", "External contractors / service providers", "Customers / consumers", "Students", "Patients", "Public authority staff"]},
                {"name": "affected_outputs", "type": "checkbox", "options": ["Employees", "Job applicants", "Students", "Patients", "Customers / consumers", "Citizens / residents"]},
                {"name": "vulnerable_groups", "type": "checkbox", "options": ["Children / minors", "Persons with disabilities", "Persons in socio-economic vulnerability", "None / not applicable", "Unknown"]},
                {"name": "workflow_role", "type": "radio", "options": ["Provides insights / recommendations only (human decides)", "Supports decisions (human approval required)", "Automatically makes decisions / actions (no human approval)", "Mixed / depends on case", "Unknown"]},
                {"name": "output_types", "type": "checkbox", "options": ["Score / rating", "Ranking", "Recommendation", "Classification / label", "Prediction / forecasting", "Matching (e.g., job matching, content matching)", "Detection (e.g., fraud detection)", "Identification / verification", "Generated content (text / image / audio / video)", "Automated decision (system executes action)"]},
                {"name": "decision_influence", "type": "radio", "options": ["Yes", "No", "Not sure"]},
                {"name": "auto_execute", "type": "radio", "options": ["No (advisory only)", "Yes (automatic actions)", "Mixed", "Unknown"]},
                
                # Section 7: Capabilities
                {"name": "capability_practices", "type": "checkbox", "options": ["Subliminal / manipulative / deceptive techniques that materially distort behaviour and are likely to cause significant harm", "Exploitation of vulnerabilities (age, disability, or social / economic situation) to distort behaviour likely causing significant harm", "Social scoring leading to detrimental / unfavourable treatment (esp. unjustified / disproportionate)", "Criminal offence risk assessment / prediction based solely on profiling or personality traits (individual predictive policing)", "Untargeted scraping of facial images from the internet or CCTV to build / expand facial recognition databases", "Emotion recognition in the workplace or in education settings", "Biometric categorisation that infers or predicts sensitive traits (e.g., race, political opinions, religion, trade union membership, sexual orientation)", "Real-time remote biometric identification (RBI) in publicly accessible spaces for law enforcement purposes", "None of the above"]},
                {"name": "interacts_persons", "type": "radio", "options": ["Yes", "No", "Unknown"]},
                {"name": "synthetic_content", "type": "checkbox", "options": ["Text", "Image", "Audio", "Video", "No", "Unknown"]},
                
                # Section 8: Technical Profile
                {"name": "ai_kind", "type": "radio", "options": ["Rules-based automation", "Machine learning", "Deep learning", "Generative AI", "Hybrid", "Unknown"]},
                {"name": "gpai_integration", "type": "radio", "options": ["Yes", "No", "Unknown"]},
                {"name": "gpai_provider", "type": "text"},
                {"name": "training_source", "type": "radio", "options": ["In-house training", "Vendor-trained model (no training by us)", "Fine-tuned by us", "Unknown / not applicable"]},
                {"name": "update_frequency", "type": "radio", "options": ["Static / never", "Periodic retraining", "Continuous learning", "Unknown"]},
                {"name": "data_types", "type": "checkbox", "options": ["Personal data", "Sensitive data (health, biometric, etc.)", "Employee data", "Children / minors data", "Public web data", "Non-personal / industrial data", "Unknown"]},
            ]
        elif form_type == 'ai_system_quick':
            # Quick add modal for AI Inventory page - Minimal fields only
            fields_metadata = [
                {"name": "system_name", "type": "text"},
                {"name": "owner", "type": "text"},
                {"name": "status", "type": "select", "options": ["Planned", "Testing", "In production", "Retired"]},
                {"name": "role", "type": "checkbox", "options": ["Provider", "Deployer", "Distributor", "Importer"]},
                {"name": "provider_type", "type": "select", "options": ["In-house", "External", "Mixed", "Unknown"]},
                {"name": "risk_classification", "type": "select", "options": ["Not assessed", "Prohibited", "High-risk", "Limited transparency", "Minimal", "Not in scope"]},
                {"name": "compliance_status", "type": "select", "options": ["Not started", "In progress", "Compliant", "Non-compliant"]},
                {"name": "deployment_context", "type": "text"},
            ]
            
        result = service.run_bulk_autofill(file_paths, fields_metadata)
        return JsonResponse(result)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in governance_autofill_api: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
@csrf_exempt
def api_risk_evaluation_profile(request, agent_id):
    """
    Get basic risk profile for Risk Evaluations tab (no AI Agent execution).
    This endpoint only calculates and returns basic risk profile information.
    """
    import logging
    from pathlib import Path
    import json
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get agent data from mock_data
        agents_data = get_mock_agents()
        agent = next((a for a in agents_data if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        # Get basic profile info
        profile = agent.get('profile', {})
        agent_name = agent.get('name', '') or agent.get('system_name', '')
        risk_classification = agent.get('risk_classification', 'not_assessed')
        
        # Calculate basic risk profile fields (no AI Agent execution)
        # These are simple calculations based on profile data
        
        # Prohibited Practices - check if system has prohibited practices
        prohibited_practices = "Not Prohibited"
        capability_practices = profile.get('capability_practices', [])
        if isinstance(capability_practices, list):
            prohibited_keywords = ['social_scoring', 'real_time_biometric', 'emotion_recognition', 'manipulation']
            if any(keyword in str(capability_practices).lower() for keyword in prohibited_keywords):
                prohibited_practices = "Potential Prohibited Practice"
        
        # High-Risk Classification - based on risk_classification field
        high_risk_classification = "Not High-Risk"
        if risk_classification == 'high_risks':
            high_risk_classification = "High-Risk"
        elif risk_classification in ['limited_risks', 'minimal_risks']:
            high_risk_classification = "Limited/Minimal Risk"
        
        # GPAI Applicability - check if system uses GPAI
        gpai_applicability = "Not Applicable"
        gpai_integration = profile.get('gpai_integration', '')
        if gpai_integration in ['yes', 'Yes', 'YES', True]:
            gpai_applicability = "GPAI Applicable"
        
        # GPAI Risk Level
        gpai_risk_level = "N/A"
        if gpai_applicability == "GPAI Applicable":
            gpai_provider = profile.get('gpai_provider', '')
            if gpai_provider:
                gpai_risk_level = "Systemic Risk"  # Default for GPAI systems
        
        return JsonResponse({
            'success': True,
            'profile': {
                'prohibited_practices': prohibited_practices,
                'high_risk_classification': high_risk_classification,
                'gpai_applicability': gpai_applicability,
                'gpai_risk_level': gpai_risk_level,
                'risk_classification': risk_classification,
                'agent_name': agent_name
            }
        })
        
    except Exception as e:
        logger.error(f"Error in api_risk_evaluation_profile: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def api_risk_evaluation_ai_scan(request, agent_id):
    """
    Run AI Agent Scan (Logic 1 or Logic 2) for risk evaluation.
    This endpoint runs the full Governance AI Agent flow.
    
    Expected JSON body (optional):
    {
        "code_files": ["path/to/file1.py", ...],
        "dataset_files": ["path/to/file1.csv", ...],
        "tool_id": "..."  # Optional: specific skill/tool to focus assessment on
    }
    """
    # This function contains the full Logic 1 and Logic 2 moved from api_assess_risk_evaluation
    # Logic 1: No upload - runs Governance AI Agent
    # Logic 2: With upload - executes uploaded code
    
    # Import the full logic from api_assess_risk_evaluation
    # For now, we'll call the existing function but this will be refactored
    # TODO: Move all Logic 1 and Logic 2 code here
    return api_assess_risk_evaluation(request, agent_id)


@require_http_methods(["POST"])
@csrf_exempt
def api_assess_risk_evaluation(request, agent_id):
    """
    Assess risk evaluation using Governance AI Agent (Logic 1).
    
    When no files uploaded:
    - Uses system description from profile to assess
    - Does NOT use assessment from mock_data
    - Always generates fresh assessment from Governance AI Agent
    
    Expected JSON body (optional):
    {
        "code_files": ["path/to/file1.py", ...],
        "dataset_files": ["path/to/file1.csv", ...],
        "tool_id": "..."  # Optional: specific skill/tool to focus assessment on
    }
    """
    import logging
    from pathlib import Path
    import json
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("RISK EVALUATION: Governance AI Agent Started")
    logger.info("=" * 80)
    logger.info(f"Agent ID: {agent_id}")
    
    try:
        # Parse request body to get tool_id if provided
        tool_id = None
        try:
            body_data = json.loads(request.body) if request.body else {}
            tool_id = body_data.get('tool_id')
            if tool_id:
                logger.info(f"Tool ID provided: {tool_id}")
        except (json.JSONDecodeError, AttributeError):
            pass  # tool_id is optional
        # ==========================================
        # STEP 0: Get Input Data (Profile from mock_data ONLY - NO assessment data)
        # ==========================================
        logger.info("\n[STEP 0] Getting Input Data (Profile from mock_data)...")
        logger.info("-" * 80)
        
        # Get agent data from mock_data (ONLY for profile information)
        # NOTE: We do NOT use assessment from mock_data - we always generate fresh assessment from Governance AI Agent
        agents_data = get_mock_agents()
        agent = next((a for a in agents_data if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            logger.error(f"Agent ID {agent_id} not found in mock_data")
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        # Get system profile from agent data (Profile tab)
        # This profile data will be used to build system_description for Governance AI Agent
        profile = agent.get('profile', {})
        agent_name = agent.get('name', '') or agent.get('system_name', '')
        
        logger.info(f"✓ Retrieved agent profile for ID {agent_id}")
        logger.info(f"  Agent name: {agent_name}")
        logger.info(f"  Profile fields available: {list(profile.keys())}")
        logger.info(f"  Agent fields available: {list(agent.keys())}")
        
        # Log profile data (only non-empty values)
        logger.info(f"  Profile data (non-empty fields):")
        for key, value in profile.items():
            if value:  # Only log non-empty values
                if isinstance(value, str) and len(value) > 100:
                    logger.info(f"    - {key}: {value[:100]}...")
                else:
                    logger.info(f"    - {key}: {value}")
        
        # Log agent-level fields (fallback when profile is empty)
        logger.info(f"  Agent-level fields (fallback data):")
        if not profile:
            logger.info(f"    - deployment_context: {agent.get('deployment_context', 'N/A')}")
            logger.info(f"    - risk_classification: {agent.get('risk_classification', 'N/A')}")
            logger.info(f"    - roles: {agent.get('roles', [])}")
            logger.info(f"    - provider_type: {agent.get('provider_type', 'N/A')}")
        
        # Build system_profile dictionary for Governance AI Agent (as per generate_governance_plan requirements)
        # Use profile data if available, otherwise fallback to agent-level fields
        logger.info("\n[STEP 0.1] Building system_profile dictionary...")
        system_profile = {
            "name": agent_name,  # IMPORTANT: Always include system name
            "purpose": profile.get('purpose', '') or profile.get('intended_purpose', ''),
            "type": profile.get('ai_system_type', '') or profile.get('system_type', '') or profile.get('ai_kind', ''),
            "users": profile.get('system_users', '') or (', '.join(profile.get('system_users', [])) if isinstance(profile.get('system_users'), list) else ''),
            "data": profile.get('data_types', '') or profile.get('data', '') or (', '.join(profile.get('data_types', [])) if isinstance(profile.get('data_types'), list) else ''),
            "geography": profile.get('deployment_geography', '') or profile.get('geography', ''),
            "deployment_context": profile.get('deployment_context', '') or agent.get('deployment_context', ''),
            "sector": profile.get('sector', '') or (', '.join(profile.get('sector_domain', [])) if isinstance(profile.get('sector_domain'), list) else ''),
            "affected_outputs": profile.get('affected_outputs', '') or (', '.join(profile.get('affected_outputs', [])) if isinstance(profile.get('affected_outputs'), list) else ''),
            "role": profile.get('role', '') or (', '.join(agent.get('roles', [])) if agent.get('roles') else agent.get('ai_act_role', '')),
            "provider_type": profile.get('provider_type', '') or agent.get('provider_type', ''),
            "risk_classification": agent.get('risk_classification', '')  # IMPORTANT: Include risk classification
        }
        
        non_empty_fields = [k for k, v in system_profile.items() if v]
        logger.info(f"✓ system_profile built with {len(non_empty_fields)} non-empty fields")
        logger.info(f"  Non-empty fields: {non_empty_fields}")
        logger.info(f"  Full system_profile: {json.dumps(system_profile, indent=2)}")
        
        # Build system_description string for assess_ai_system (backward compatibility)
        # This is the input for Governance AI Agent's assess_ai_system() method
        logger.info("\n[STEP 0.2] Building system_description string (Input for assess_ai_system)...")
        system_description_parts = []
        
        # Always include system name (IMPORTANT - required field)
        if agent_name:
            system_description_parts.append(f"AI System Name: {agent_name}")
        else:
            # Fallback if name is missing
            agent_name = f"AI System ID {agent_id}"
            system_description_parts.append(f"AI System Name: {agent_name}")
        if system_profile.get('purpose'):
            system_description_parts.append(f"Purpose: {system_profile.get('purpose')}")
        if system_profile.get('type'):
            system_description_parts.append(f"System type: {system_profile.get('type')}")
        if system_profile.get('sector'):
            system_description_parts.append(f"Sector: {system_profile.get('sector')}")
        if system_profile.get('users'):
            system_description_parts.append(f"System users: {system_profile.get('users')}")
        if system_profile.get('data'):
            system_description_parts.append(f"Data types: {system_profile.get('data')}")
        if system_profile.get('deployment_context'):
            system_description_parts.append(f"Deployment context: {system_profile.get('deployment_context')}")
        if system_profile.get('geography'):
            system_description_parts.append(f"Deployment geography: {system_profile.get('geography')}")
        if system_profile.get('affected_outputs'):
            system_description_parts.append(f"Affected outputs: {system_profile.get('affected_outputs')}")
        if system_profile.get('role'):
            system_description_parts.append(f"Role: {system_profile.get('role')}")
        if system_profile.get('provider_type'):
            system_description_parts.append(f"Provider type: {system_profile.get('provider_type')}")
        
        # Always add risk classification if available (IMPORTANT field)
        risk_class = agent.get('risk_classification', '')
        if risk_class:
            risk_display = {
                'high_risks': 'High-Risk',
                'limited_risks': 'Limited Risk',
                'minimal_risks': 'Minimal Risk',
                'not_assessed': 'Not Assessed',
                'prohibited': 'Prohibited',
                'not_in_scope': 'Not in Scope'
            }.get(risk_class, risk_class.replace('_', ' ').title())
            system_description_parts.append(f"Risk Classification: {risk_display}")
        
        # Add fallback information from agent-level fields if system_description is still minimal
        if len(system_description_parts) <= 2:  # Only has name + risk classification
            # Add status
            status = agent.get('status', '')
            if status:
                system_description_parts.append(f"Status: {status}")
            
            # Add business unit/owner
            business_unit = agent.get('business_unit', '')
            if business_unit:
                system_description_parts.append(f"Owner: {business_unit}")
        
        system_description = ". ".join(system_description_parts) if system_description_parts else ""
        
        # If still empty, use a default description with available info
        if not system_description:
            fallback_parts = [f"AI system: {agent_name or 'Unnamed AI System'}"]
            if agent.get('deployment_context'):
                fallback_parts.append(f"deployed in {agent.get('deployment_context')}")
            if agent.get('risk_classification'):
                fallback_parts.append(f"classified as {agent.get('risk_classification')}")
            system_description = " ".join(fallback_parts) + " for automated risk assessment"
        
        # Add tool/skill information to system_description if tool_id is provided
        if tool_id:
            logger.info(f"\n[STEP 0.3] Adding tool/skill context to system_description...")
            logger.info(f"  Tool ID: {tool_id}")
            
            # Get tool information from compliance skills API or use a mapping
            tool_info = None
            try:
                from .infrastructure.services.governance_agent_service import GovernanceAgentService
                service = GovernanceAgentService()
                skills = service.get_skills()
                # Find skill by ID or name
                for skill in skills:
                    skill_id = skill.get('id', '').lower().replace('_', '-').replace(' ', '-')
                    skill_name = skill.get('name', '').lower().replace('_', '-').replace(' ', '-')
                    tool_id_lower = tool_id.lower().replace('_', '-').replace(' ', '-')
                    if tool_id_lower in skill_id or tool_id_lower in skill_name or skill_id in tool_id_lower or skill_name in tool_id_lower:
                        tool_info = {
                            'name': skill.get('name', tool_id),
                            'description': skill.get('description', ''),
                            'category': skill.get('category', '')
                        }
                        break
            except Exception as e:
                logger.warning(f"Could not fetch tool info from service: {e}")
            
            # If not found, use a simple mapping based on common tool IDs
            if not tool_info:
                tool_mapping = {
                    'ai-governance': {'name': 'AI Governance Assessment', 'description': 'Establishes governance structures and processes for responsible AI development and deployment.'},
                    'risk-assessment': {'name': 'Risk Assessment and Management', 'description': 'Systematic identification, analysis, and management of risks in AI systems.'},
                    'fria-assessment': {'name': 'Fundamental Rights Impact Assessment (FRIA)', 'description': 'Comprehensive assessment of AI system impact on fundamental rights including privacy, non-discrimination, and human dignity.'},
                    'data-classification': {'name': 'Data Classification Assessment', 'description': 'Automatically classifies and labels sensitive data including personal data, special categories of data, and confidential information.'},
                    'gdpr-compliance': {'name': 'GDPR Compliance', 'description': 'Toolkit for ensuring GDPR compliance in AI systems.'},
                    'qms-tracker': {'name': 'Quality Management System Tracker Assessment', 'description': 'Tracks quality management system implementation and maintenance for AI systems.'},
                    'ai-logging-system': {'name': 'AI Logging System Assessment', 'description': 'Automated logging system for AI operations capturing decisions, inputs, outputs, and system events.'},
                }
                tool_info = tool_mapping.get(tool_id.lower(), {'name': tool_id.replace('-', ' ').title(), 'description': f'Assessment focused on {tool_id.replace("-", " ")} compliance requirements.'})
            
            # Add tool context to system_description
            tool_context_parts = []
            tool_context_parts.append(f"Assessment Focus: This assessment is specifically focused on {tool_info['name']}")
            if tool_info.get('description'):
                tool_context_parts.append(f"Tool Description: {tool_info['description']}")
            if tool_info.get('category'):
                tool_context_parts.append(f"Tool Category: {tool_info['category']}")
            
            tool_context = ". ".join(tool_context_parts)
            system_description = f"{system_description}. {tool_context}"
            
            logger.info(f"✓ Tool context added to system_description")
            logger.info(f"  Tool name: {tool_info['name']}")
            logger.info(f"  Tool description: {tool_info.get('description', 'N/A')[:100]}...")
        
        logger.info(f"✓ system_description built ({len(system_description)} characters)")
        logger.info(f"  system_description_parts count: {len(system_description_parts)}")
        logger.info(f"  Full system_description:")
        logger.info(f"  {system_description}")
        
        # Check for uploaded files (Logic 2 - not implemented in this function, handled separately)
        # For Logic 1, we only use profile data
        logger.info("\n[STEP 0.3] Checking for uploaded files...")
        code_files = []
        dataset_files = []
        
        try:
            request_data = json.loads(request.body) if request.body else {}
            code_files = request_data.get('code_files', [])
            dataset_files = request_data.get('dataset_files', [])
        except:
            pass
        
        # Check if files are uploaded in agent data
        risk_evaluation = agent.get('risk_evaluation', {})
        if not code_files and risk_evaluation.get('code_files'):
            code_files = risk_evaluation.get('code_files', [])
        if not dataset_files and risk_evaluation.get('dataset_files'):
            dataset_files = risk_evaluation.get('dataset_files', [])
        
        # ==========================================
        # LOGIC 2: Handle Code + Dataset Upload (Execute uploaded code)
        # ==========================================
        code_execution_output = ""
        markdown_output_content = ""
        markdown_output_file = None  # Path to saved markdown file (relative to BASE_DIR)
        
        if code_files or dataset_files:
            logger.info("\n" + "=" * 80)
            logger.info("[LOGIC 2] Processing Uploaded Files (Code + Dataset)")
            logger.info("=" * 80)
            logger.info(f"  Code files: {len(code_files)}")
            logger.info(f"  Dataset files: {len(dataset_files)}")
            
            # Get ai_act_articles directory (where datasets are saved)
            ai_act_articles_dir = Path(settings.BASE_DIR) / 'ai_act_articles'
            ai_act_articles_dir.mkdir(exist_ok=True)
            logger.info(f"  AI Act articles directory: {ai_act_articles_dir}")
            
            # Step 1: Save dataset files to ai_act_articles/
            uploaded_dataset_file = None
            if dataset_files:
                logger.info("\n[LOGIC 2.1] Saving dataset files to ai_act_articles/...")
                for dataset_path_str in dataset_files:
                    try:
                        dataset_path = Path(settings.BASE_DIR) / dataset_path_str
                        if dataset_path.exists() and dataset_path.is_file():
                            # Check if file is already in ai_act_articles/ (don't copy to itself)
                            if dataset_path.parent == ai_act_articles_dir:
                                # File is already in ai_act_articles/, use it directly
                                uploaded_dataset_file = dataset_path
                                logger.info(f"  ✓ Dataset file already in ai_act_articles/: {dataset_path.name}")
                            else:
                                # Copy to ai_act_articles/
                                dest_path = ai_act_articles_dir / dataset_path.name
                                # Check if destination is same as source
                                if dataset_path.resolve() == dest_path.resolve():
                                    uploaded_dataset_file = dataset_path
                                    logger.info(f"  ✓ Dataset file already at destination: {dataset_path.name}")
                                else:
                                    import shutil
                                    shutil.copy2(dataset_path, dest_path)
                                    logger.info(f"  ✓ Saved: {dataset_path.name} -> {dest_path}")
                                    if not uploaded_dataset_file:
                                        uploaded_dataset_file = dest_path
                            if not uploaded_dataset_file:
                                uploaded_dataset_file = dataset_path
                        else:
                            logger.warning(f"  ⚠ Dataset file not found: {dataset_path}")
                    except Exception as e:
                        logger.error(f"  ✗ Error saving dataset {dataset_path_str}: {e}")
            
            # Step 2: Execute code files (modify to use uploaded dataset, then run)
            if code_files:
                logger.info("\n[LOGIC 2.2] Executing code files...")
                code_file_names = []
                execution_outputs = []
                
                for file_path_str in code_files:
                    try:
                        file_path = Path(settings.BASE_DIR) / file_path_str
                        if file_path.exists() and file_path.is_file():
                            code_file_names.append(file_path.name)
                            
                            # Check if it's a Python file
                            if file_path.suffix.lower() == '.py':
                                logger.info(f"  Processing Python file: {file_path.name}")
                                
                                try:
                                    # Read original code file
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        original_code = f.read()
                                    
                                    # Create temporary modified copy
                                    import tempfile
                                    temp_code_file = None
                                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                                        temp_code_file = Path(temp_file.name)
                                        
                                        # Modify code: Update paths to use uploaded dataset
                                        modified_code = original_code
                                        
                                        # Update ARTICLES_DIR to point to ai_act_articles/
                                        if 'ARTICLES_DIR' in modified_code:
                                            # Replace ARTICLES_DIR definition with absolute path
                                            import re
                                            # Use absolute path to ai_act_articles_dir
                                            articles_dir_absolute = str(ai_act_articles_dir.resolve())
                                            modified_code = re.sub(
                                                r'ARTICLES_DIR\s*=\s*[^\n]+',
                                                f'ARTICLES_DIR = Path(r"{articles_dir_absolute}")',
                                                modified_code
                                            )
                                            logger.info(f"    ✓ Updated ARTICLES_DIR to absolute path: {articles_dir_absolute}")
                                        
                                        # Note: No longer updating AI_ACT_TEXT_PATH in code files
                                        # Code files should handle their own dataset file selection
                                        
                                        # Ensure GEMINI_API_KEY is read from environment
                                        # Only replace assignment statements, not string literals
                                        if 'GEMINI_API_KEY' in modified_code:
                                            # Match: GEMINI_API_KEY = ... (assignment, not in string)
                                            # Use a more precise pattern that avoids string literals
                                            lines = modified_code.split('\n')
                                            modified_lines = []
                                            for line in lines:
                                                # Check if this line contains GEMINI_API_KEY assignment (not in string)
                                                if re.match(r'^\s*GEMINI_API_KEY\s*=', line) and 'os.environ.get' not in line:
                                                    # Replace assignment with os.environ.get
                                                    line = re.sub(
                                                        r'GEMINI_API_KEY\s*=\s*[^\n]+',
                                                        'GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")',
                                                        line
                                                    )
                                                    logger.info(f"    ✓ Updated GEMINI_API_KEY assignment to use environment")
                                                modified_lines.append(line)
                                            modified_code = '\n'.join(modified_lines)
                                        
                                        temp_file.write(modified_code)
                                    
                                    # Set environment variables
                                    env = os.environ.copy()
                                    env['GEMINI_API_KEY'] = settings.GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY', '')
                                    env['ARTICLES_DIR'] = str(ai_act_articles_dir)
                                    
                                    # Set PYTHONPATH to include governance directory (for setup_ai_act_store module)
                                    governance_dir = Path(settings.BASE_DIR)
                                    pythonpath = env.get('PYTHONPATH', '')
                                    if pythonpath:
                                        env['PYTHONPATH'] = f"{governance_dir}:{pythonpath}"
                                    else:
                                        env['PYTHONPATH'] = str(governance_dir)
                                    
                                    # Also add scripts directory to PYTHONPATH if it exists
                                    scripts_dir = governance_dir / 'scripts'
                                    if scripts_dir.exists():
                                        env['PYTHONPATH'] = f"{scripts_dir}:{env['PYTHONPATH']}"
                                    
                                    logger.info(f"    PYTHONPATH: {env['PYTHONPATH']}")
                                    
                                    # Prepare question = Map info from profile to question for ai_act_cli.py
                                    # Question should include all relevant info from profile
                                    question_parts = []
                                    if agent_name:
                                        question_parts.append(f"AI System Name: {agent_name}")
                                    if system_profile.get('purpose'):
                                        question_parts.append(f"Purpose: {system_profile.get('purpose')}")
                                    if system_profile.get('type'):
                                        question_parts.append(f"Type: {system_profile.get('type')}")
                                    if system_profile.get('deployment_context'):
                                        question_parts.append(f"Deployment Context: {system_profile.get('deployment_context')}")
                                    if system_profile.get('sector'):
                                        question_parts.append(f"Sector: {system_profile.get('sector')}")
                                    if system_profile.get('users'):
                                        question_parts.append(f"Users: {system_profile.get('users')}")
                                    if system_profile.get('data'):
                                        question_parts.append(f"Data: {system_profile.get('data')}")
                                    if system_profile.get('geography'):
                                        question_parts.append(f"Geography: {system_profile.get('geography')}")
                                    if system_profile.get('risk_classification'):
                                        question_parts.append(f"Risk Classification: {system_profile.get('risk_classification')}")
                                    
                                    # Build question string from profile info
                                    question = ". ".join(question_parts) if question_parts else (agent_name or f"AI System ID {agent_id}")
                                    logger.info(f"    Question (mapped from profile): {question[:200]}...")
                                    logger.info(f"    Executing: python {file_path.name} \"{question}\"")
                                    
                                    # Execute the modified Python file with question as argument
                                    # Run from governance directory so setup_ai_act_store can be found
                                    import subprocess
                                    import sys
                                    
                                    print(f"  [VIEWS] Executing code file: {temp_code_file}")
                                    print(f"  [VIEWS] Command: {sys.executable} {temp_code_file.name} \"{question[:100]}...\"")
                                    print(f"  [VIEWS] Working directory: {governance_dir}")
                                    print(f"  [VIEWS] Environment GEMINI_API_KEY: {'SET' if env.get('GEMINI_API_KEY') else 'NOT SET'}")
                                    print(f"  [VIEWS] Python executable: {sys.executable}")
                                    
                                    result = subprocess.run(
                                        [sys.executable, str(temp_code_file), question],
                                        capture_output=True,
                                        text=True,
                                        timeout=120,  # 120 second timeout
                                        env=env,
                                        cwd=str(governance_dir)  # Run from governance directory, not temp directory
                                    )
                                    
                                    print(f"  [VIEWS] Execution completed")
                                    print(f"  [VIEWS] Exit code: {result.returncode}")
                                    print(f"  [VIEWS] STDOUT length: {len(result.stdout)} chars")
                                    print(f"  [VIEWS] STDERR length: {len(result.stderr)} chars")
                                    
                                    print(f"\n  [VIEWS] ========== STDOUT CONTENT ==========")
                                    if result.stdout:
                                        print(result.stdout)
                                    else:
                                        print("  (empty)")
                                    print(f"  [VIEWS] ======================================\n")
                                    
                                    print(f"\n  [VIEWS] ========== STDERR CONTENT ==========")
                                    if result.stderr:
                                        print(result.stderr)
                                    else:
                                        print("  (empty)")
                                    print(f"  [VIEWS] ======================================\n")
                                    
                                    # Check for missing modules
                                    if result.returncode != 0:
                                        print(f"  [VIEWS] ⚠ Non-zero exit code: {result.returncode}")
                                        if 'ModuleNotFoundError' in result.stderr or 'ModuleNotFoundError' in result.stdout:
                                            import re
                                            error_text = result.stderr + result.stdout
                                            match = re.search(r"No module named '([^']+)'", error_text)
                                            if match:
                                                missing_module = match.group(1)
                                                print(f"  [VIEWS] ⚠ Missing module: {missing_module}")
                                                print(f"  [VIEWS] 💡 Install with: pip install {missing_module}")
                                                logger.warning(f"    ⚠ Missing module {missing_module}. Install with: pip install {missing_module}")
                                        else:
                                            print(f"  [VIEWS] ⚠ Error details:")
                                            if result.stderr:
                                                print(f"    STDERR: {result.stderr[:500]}")
                                            if result.stdout:
                                                print(f"    STDOUT: {result.stdout[:500]}")
                                    
                                    # Capture stdout as markdown output (ai_act_cli.py outputs markdown to stdout)
                                    if result.stdout:
                                        # Try to extract markdown from stdout
                                        stdout_text = result.stdout
                                        # Look for markdown patterns (headers, lists, etc.)
                                        if any(marker in stdout_text for marker in ['# ', '## ', '* ', '- ', '```']):
                                            markdown_output_content = stdout_text
                                            logger.info(f"    ✓ Captured markdown output from stdout ({len(markdown_output_content)} chars)")
                                    
                                    # Also check for markdown files in output directory
                                    output_md_files = list(temp_code_file.parent.glob("*.md"))
                                    if not output_md_files:
                                        # Also check in original code file directory
                                        output_md_files = list(file_path.parent.glob("*.md"))
                                    if not output_md_files:
                                        # Check in ai_act_articles directory
                                        output_md_files = list(ai_act_articles_dir.glob("*.md"))
                                    
                                    # Read markdown output if found
                                    if output_md_files:
                                        try:
                                            markdown_content = output_md_files[0].read_text(encoding='utf-8', errors='ignore')
                                            if markdown_content:
                                                markdown_output_content = markdown_content
                                                logger.info(f"    ✓ Read markdown file: {output_md_files[0].name} ({len(markdown_output_content)} chars)")
                                        except Exception as e:
                                            logger.debug(f"    Could not read markdown output: {e}")
                                    
                                    execution_output = f"""
=== CODE EXECUTION: {file_path.name} ===
Exit Code: {result.returncode}
Question: {question}
STDOUT:
{result.stdout}
STDERR:
{result.stderr}
"""
                                    if markdown_output_content:
                                        execution_output += f"Markdown Output Length: {len(markdown_output_content)} characters\n"
                                    
                                    execution_output += "=== END OF EXECUTION ===\n"
                                    execution_outputs.append(execution_output)
                                    
                                    logger.info(f"    ✓ Execution completed (exit code: {result.returncode})")
                                    if result.returncode != 0:
                                        logger.warning(f"    ⚠ Non-zero exit code: {result.stderr[:200]}")
                                    
                                    # Clean up temp file
                                    try:
                                        if temp_code_file and temp_code_file.exists():
                                            temp_code_file.unlink()
                                    except:
                                        pass
                                    
                                except subprocess.TimeoutExpired:
                                    logger.error(f"    ✗ Timeout after 120 seconds")
                                    execution_outputs.append(f"\n=== CODE EXECUTION: {file_path.name} ===\nTimeout after 120 seconds\n=== END OF EXECUTION ===\n")
                                except Exception as e:
                                    logger.error(f"    ✗ Error executing code file {file_path}: {e}", exc_info=True)
                                    execution_outputs.append(f"\n=== CODE EXECUTION: {file_path.name} ===\nError: {str(e)}\n=== END OF EXECUTION ===\n")
                            else:
                                # For non-Python files, read content
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        execution_outputs.append(f"\n=== CODE FILE: {file_path.name} (non-executable) ===\n{content}\n=== END OF FILE ===\n")
                                except Exception as e:
                                    logger.debug(f"Could not read file {file_path}: {e}")
                                    execution_outputs.append(f"\n=== CODE FILE: {file_path.name} ===\nError reading file: {str(e)}\n=== END OF FILE ===\n")
                    except Exception as e:
                        logger.error(f"Error processing code file {file_path_str}: {e}", exc_info=True)
                
                if code_file_names:
                    code_execution_output = f"\n\n=== EXECUTED CODE FILES ({len(code_file_names)} files) ===\n"
                    code_execution_output += f"Files: {', '.join(code_file_names)}\n"
                    if uploaded_dataset_file:
                        code_execution_output += f"Dataset used: {uploaded_dataset_file.name}\n"
                    if execution_outputs:
                        code_execution_output += "\n".join(execution_outputs)
                    code_execution_output += "\n=== END OF CODE EXECUTION ===\n"
            
            # Logic 2: Only run uploaded code, do NOT call Governance AI Agent
            # The markdown output from code execution is the final result
            logger.info("\n[LOGIC 2] Code execution completed. Using markdown output as final result.")
            logger.info("  Note: Logic 2 does NOT call Governance AI Agent - only executes uploaded code.")
            
            # Step 3: Save markdown output to file (if available)
            if markdown_output_content:
                logger.info(f"  ✓ Markdown output captured: {len(markdown_output_content)} characters")
                
                # Create Output directory
                output_dir = Path(settings.BASE_DIR) / 'Output'
                output_dir.mkdir(exist_ok=True)
                logger.info(f"  Output directory: {output_dir}")
                
                # Generate output filename
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_agent_name = (agent_name or f"AI_System_{agent_id}").replace(' ', '_').replace('/', '_')
                output_filename = f"AI_GOVERNANCE_ASSESSMENT_{safe_agent_name}_{timestamp}.md"
                output_file_path = output_dir / output_filename
                
                # Save markdown content to file
                try:
                    with open(output_file_path, 'w', encoding='utf-8') as f:
                        # Add header with metadata
                        f.write(f"# AI Governance Framework Assessment\n")
                        f.write(f"## {agent_name or f'AI System ID {agent_id}'}\n\n")
                        f.write(f"**Assessment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"**System:** {agent_name or 'Unnamed AI System'}\n")
                        f.write(f"**Framework:** EU AI Act + NIST AI RMF + ISO/IEC 42001\n")
                        f.write(f"**Assessment Type:** Code Execution (Logic 2)\n\n")
                        f.write("---\n\n")
                        f.write(markdown_output_content)
                    
                    logger.info(f"  ✓ Saved markdown output to: {output_file_path}")
                    logger.info(f"    File size: {output_file_path.stat().st_size} bytes")
                    
                    # Store output file path in response (relative to BASE_DIR)
                    output_file_relative = str(output_file_path.relative_to(settings.BASE_DIR))
                    markdown_output_file = output_file_relative
                except Exception as e:
                    logger.error(f"  ✗ Error saving markdown output file: {e}", exc_info=True)
                    markdown_output_file = None
            else:
                markdown_output_file = None
            
            # ==========================================
            # LOGIC 2: Return markdown output directly (no Governance AI Agent)
            # ==========================================
            logger.info("\n" + "=" * 80)
            logger.info("[LOGIC 2] Returning markdown output from code execution")
            logger.info("=" * 80)
            
            # Parse markdown output to extract assessment data for UI
            # For Logic 2, we return the markdown output directly
            return JsonResponse({
                'success': True,
                'assessment': {
                    'prohibited_practices': 'Not assessed',
                    'high_risk_classification': 'Not assessed',
                    'gpai_applicability': 'Not assessed',
                    'gpai_risk_level': 'N/A',
                    'risk_classification': {
                        'category': 'Not assessed',
                        'confidence': 'N/A',
                        'reasoning': 'Assessment from code execution'
                    },
                    'applicable_regulations': [],
                    'recommended_skills': [],
                    'initial_assessment': 'Assessment generated from uploaded code execution.',
                    'detailed_risk_assessment': [],
                    'governance_plan': None,
                    'markdown_output': markdown_output_content,  # Output from code execution
                    'markdown_output_file': markdown_output_file  # Path to saved markdown file
                }
            })
        else:
            # ==========================================
            # LOGIC 1: No uploaded files -> run full Governance AI Agent flow
            # ==========================================
            logger.info("\n" + "=" * 80)
            logger.info("[LOGIC 1] No uploaded files detected – proceeding with full Governance AI Agent flow")
            logger.info("=" * 80)
            # Do NOT return here; continue to Governance AI Agent initialization below
        
        # ==========================================
        # NOTE: The code below should NOT be reached
        # Logic 1 returns early, Logic 2 returns early
        # This section is kept for backward compatibility but should not execute
        # ==========================================
        logger.warning("WARNING: Reached code that should not execute. Logic 1 and Logic 2 should return early.")
        
        # ==========================================
        # INIT: Initialize Governance AI Agent (DEPRECATED - should not run)
        # ==========================================
        logger.info("\n" + "=" * 80)
        logger.info("[INIT] Initializing Governance AI Agent (Core Engine)...")
        logger.info("-" * 80)
        
        try:
            from governance_agent.governance_agent import GovernanceAIAgent, AgentConfig
            agent_config = AgentConfig()
            governance_agent = GovernanceAIAgent(agent_config)
            logger.info(f"✓ Governance AI Agent initialized successfully")
            logger.info(f"  Available skills: {len(governance_agent.skills)}")
            skills_preview = [s.get('name', s.get('skill', 'Unknown'))[:50] for s in list(governance_agent.skills.values())[:5]]
            logger.info(f"  Skills preview: {skills_preview}...")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Governance AI Agent: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Governance AI Agent initialization failed: {str(e)}',
                'assessment': {
                    'risk_classification': {
                        'category': 'Not assessed',
                        'confidence': 'low',
                        'reasoning': f'Governance AI Agent not available: {str(e)}'
                    },
                    'prohibited_practices': 'Not assessed',
                    'high_risk_classification': 'Not assessed',
                    'gpai_applicability': 'Not assessed',
                    'gpai_risk_level': 'N/A',
                    'recommended_skills': [],
                    'detailed_risk_assessment': []
                }
            })
        
        # ==========================================
        # STEP 1: Assess AI System (Initial Assessment - Advisory Layer)
        # ==========================================
        logger.info("\n" + "=" * 80)
        logger.info("[STEP 1] Assess AI System (Initial Assessment - Advisory Layer)")
        logger.info("=" * 80)
        logger.info("This step provides:")
        logger.info("  - Risk Classification (4 levels: Unacceptable, High, Limited, Minimal)")
        logger.info("  - Regulation Identification (EU AI Act, GDPR, NIST AI RMF)")
        logger.info("  - Skill Discovery & Recommendation (50+ skills)")
        logger.info("  - Initial Assessment")
        logger.info("-" * 80)
        logger.info(f"INPUT for assess_ai_system():")
        logger.info(f"  system_description length: {len(system_description)} characters")
        logger.info(f"  system_description preview: {system_description[:200]}...")
        
        try:
            logger.info("\n[STEP 1.1] Calling governance_agent.assess_ai_system(system_description)...")
            assessment = governance_agent.assess_ai_system(system_description)
            logger.info("✓ assess_ai_system() completed successfully")
            
            # Log output from assess_ai_system
            logger.info("\n[STEP 1.2] OUTPUT from assess_ai_system():")
            logger.info("-" * 80)
            risk_classification = assessment.get('risk_classification', {})
            risk_category = risk_classification.get('category', 'Not assessed')
            risk_confidence = risk_classification.get('confidence', 'N/A')
            risk_reasoning = risk_classification.get('reasoning', 'N/A')
            
            logger.info(f"  Risk Classification:")
            logger.info(f"    - Category: {risk_category}")
            logger.info(f"    - Confidence: {risk_confidence}")
            if isinstance(risk_reasoning, str):
                logger.info(f"    - Reasoning: {risk_reasoning[:200]}...")
            else:
                logger.info(f"    - Reasoning: {risk_reasoning}")
            
            applicable_regulations = assessment.get('applicable_regulations', [])
            logger.info(f"  Applicable Regulations: {len(applicable_regulations)}")
            for reg in applicable_regulations[:5]:  # Show first 5
                logger.info(f"    - {reg}")
            
            recommended_skills = assessment.get('recommended_skills', [])
            logger.info(f"  Recommended Skills: {len(recommended_skills)}")
            for skill in recommended_skills[:10]:  # Show first 10
                skill_name = skill.get('skill', skill.get('name', 'Unknown'))
                logger.info(f"    - {skill_name}")
            
            initial_assessment = assessment.get('initial_assessment', '')
            logger.info(f"  Initial Assessment length: {len(initial_assessment)} characters")
            logger.info(f"  Initial Assessment preview: {initial_assessment[:300]}...")
            
        except Exception as e:
            logger.error(f"✗ Error in assess_ai_system: {e}", exc_info=True)
            raise
        
        # Extract results from assess_ai_system
        risk_classification = assessment.get('risk_classification', {})
        risk_category = risk_classification.get('category', 'Not assessed')
        applicable_regulations = assessment.get('applicable_regulations', [])
        recommended_skills = assessment.get('recommended_skills', [])
        initial_assessment = assessment.get('initial_assessment', '')
        
        # ==========================================
        # STEP 2: Generate Governance Plan (Comprehensive Planning - Advisory Layer)
        # ==========================================
        logger.info("\n" + "=" * 80)
        logger.info("[STEP 2] Generate Governance Plan (Comprehensive Planning - Advisory Layer)")
        logger.info("=" * 80)
        logger.info("This step provides:")
        logger.info("  - Executive Summary")
        logger.info("  - Architecture Recommendations")
        logger.info("  - Safety Implementation")
        logger.info("  - Testing Strategy")
        logger.info("  - Operational Procedures")
        logger.info("  - Next Steps")
        logger.info("  - NIST AI RMF structure (Govern, Map, Measure, Manage)")
        logger.info("-" * 80)
        logger.info(f"INPUT for generate_governance_plan():")
        logger.info(f"  system_profile: {json.dumps(system_profile, indent=2)}")
        
        governance_plan = None
        try:
            # Generate governance plan if we have sufficient profile data OR agent-level data
            # Check if we have at least name + deployment_context or other key fields
            has_profile_data = (
                system_profile.get('purpose') or 
                system_profile.get('type') or 
                system_profile.get('deployment_context') or
                system_profile.get('sector') or
                agent_name  # At least we have a name
            )
            
            if has_profile_data:
                logger.info("\n[STEP 2.1] Calling governance_agent.generate_governance_plan(system_profile)...")
                logger.info(f"  Using system_profile with {len([v for v in system_profile.values() if v])} non-empty fields")
                governance_plan = governance_agent.generate_governance_plan(system_profile)
                logger.info("✓ generate_governance_plan() completed successfully")
                
                # Log output from generate_governance_plan
                logger.info("\n[STEP 2.2] OUTPUT from generate_governance_plan():")
                logger.info("-" * 80)
                if governance_plan:
                    logger.info(f"  Governance Plan structure:")
                    for key in governance_plan.keys():
                        value = governance_plan[key]
                        if isinstance(value, str):
                            logger.info(f"    - {key}: {len(value)} characters")
                            logger.info(f"      Preview: {value[:200]}...")
                        elif isinstance(value, list):
                            logger.info(f"    - {key}: {len(value)} items")
                        elif isinstance(value, dict):
                            logger.info(f"    - {key}: {len(value)} keys")
                        else:
                            logger.info(f"    - {key}: {type(value).__name__}")
                else:
                    logger.warning("  Governance plan is None")
            else:
                logger.warning("  Skipping governance plan generation (insufficient profile data)")
        except Exception as e:
            logger.warning(f"✗ Could not generate governance plan: {e}", exc_info=True)
            # Continue with assessment results even if governance plan fails
        
        # Determine prohibited practices, high-risk, GPAI applicability
        prohibited_practices = 'Not assessed'
        high_risk_classification = 'Not assessed'
        gpai_applicability = 'Not assessed'
        gpai_risk_level = 'N/A'
        
        # Check for prohibited practices (simplified logic)
        description_lower = system_description.lower()
        if any(word in description_lower for word in ['social scoring', 'real-time biometric', 'subliminal manipulation']):
            prohibited_practices = 'Prohibited'
        else:
            prohibited_practices = 'Not prohibited'
        
        # Check high-risk classification
        if risk_category == 'High-Risk':
            high_risk_classification = 'High-Risk'
        else:
            high_risk_classification = 'Not High-Risk'
        
        # Check GPAI applicability (simplified - if it's a general-purpose AI)
        if any(word in description_lower for word in ['general purpose', 'foundation model', 'gpt', 'llm', 'language model']):
            gpai_applicability = 'Applicable'
            if risk_category == 'High-Risk':
                gpai_risk_level = 'Systemic Risk'
            else:
                gpai_risk_level = 'Limited Risk'
        else:
            gpai_applicability = 'Not Applicable'
        
        # Build detailed risk assessment with recommended tools
        detailed_risk_assessment = []
        
        # Cybersecurity section
        cybersecurity_tools = []
        if any(skill.get('skill', '') in ['security-frameworks', 'sbom-management'] for skill in recommended_skills):
            cybersecurity_tools = [
                'Prompt Injection Detection Assessment',
                'Security Frameworks',
                'Grype Vulnerability Scanner',
                'Safety (PyUp)',
                'Snyk',
                'OSS Scorecard'
            ]
        
        if cybersecurity_tools or 'security' in description_lower:
            detailed_risk_assessment.append({
                'category': 'Cybersecurity',
                'description': 'Standard cybersecurity best practices recommended to protect system integrity and user data.',
                'recommended_tools': cybersecurity_tools or [
                    'Prompt Injection Detection Assessment',
                    'Security Frameworks',
                    'Grype Vulnerability Scanner',
                    'Safety (PyUp)',
                    'Snyk',
                    'OSS Scorecard'
                ],
                'color': 'red'
            })
        
        # Privacy section
        privacy_tools = []
        if any(skill.get('skill', '') in ['gdpr-compliance', 'hipaa-compliance', 'pci-dss-compliance'] for skill in recommended_skills):
            privacy_tools = [
                'Data Classification',
                'GDPR Compliance',
                'HIPAA Compliance',
                'PCI DSS Compliance'
            ]
        
        if privacy_tools or any(word in description_lower for word in ['privacy', 'personal data', 'gdpr']):
            detailed_risk_assessment.append({
                'category': 'Privacy',
                'description': 'Standard privacy requirements. Ensure GDPR compliance and appropriate data protection measures.',
                'recommended_tools': privacy_tools or [
                    'Data Classification',
                    'GDPR Compliance',
                    'HIPAA Compliance',
                    'PCI DSS Compliance'
                ],
                'color': 'purple'
            })
        
        # FRIA section
        fria_tools = []
        if any(skill.get('skill', '') in ['bias-assessment', 'ai-ethics', 'validating-ai-ethics-and-fairness'] for skill in recommended_skills):
            fria_tools = [
                'FRIA Assessment',
                'Bias Assessment',
                'AI Fairness 360',
                'HITL Design'
            ]
        
        if fria_tools or risk_category == 'High-Risk' or any(word in description_lower for word in ['bias', 'fairness', 'ethics']):
            detailed_risk_assessment.append({
                'category': 'Fundamental Rights Impact Assessment (FRIA)',
                'description': 'FRIA recommended for systems with potential fundamental rights impact. Evaluate effects on privacy, equality, and human dignity to ensure compliance with EU Charter of Fundamental Rights.',
                'recommended_tools': fria_tools or [
                    'FRIA Assessment',
                    'Bias Assessment',
                    'AI Fairness 360',
                    'HITL Design'
                ],
                'color': 'blue'
            })
        
        # ==========================================
        # OUTPUT: Final Assessment Response
        # ==========================================
        logger.info("\n" + "=" * 80)
        logger.info("[OUTPUT] Final Assessment Response")
        logger.info("=" * 80)
        logger.info("Response structure:")
        logger.info(f"  - prohibited_practices: {prohibited_practices}")
        logger.info(f"  - high_risk_classification: {high_risk_classification}")
        logger.info(f"  - gpai_applicability: {gpai_applicability}")
        logger.info(f"  - gpai_risk_level: {gpai_risk_level}")
        logger.info(f"  - risk_classification: {risk_category}")
        logger.info(f"  - applicable_regulations: {len(applicable_regulations)} regulations")
        logger.info(f"  - recommended_skills: {len(recommended_skills)} skills")
        logger.info(f"  - initial_assessment: {len(initial_assessment)} characters")
        logger.info(f"  - detailed_risk_assessment: {len(detailed_risk_assessment)} items")
        logger.info(f"  - governance_plan: {'Present' if governance_plan else 'None'}")
        logger.info(f"  - markdown_output: {len(markdown_output_content) if markdown_output_content else 0} characters")
        logger.info("=" * 80)
        
        # ==========================================
        # Generate Markdown Output File (for both Logic 1 and Logic 2)
        # ==========================================
        # If Logic 1: Generate markdown from assessment + governance_plan
        # If Logic 2: Use markdown from code execution (already captured)
        # Always generate markdown for Logic 1 (even if Logic 2 already has markdown)
        if (not code_files and not dataset_files) or (not markdown_output_content and (assessment or governance_plan)):
            logger.info("\n[OUTPUT] Generating markdown file from assessment results (Logic 1)...")
            try:
                # Prefer exporting governance_plan if available (as per examples)
                # Otherwise export assessment data
                if governance_plan:
                    # Export governance plan (matches example_governance_plan.py pattern)
                    markdown_output_content = governance_agent.export_assessment(governance_plan, format='markdown')
                    logger.info(f"  ✓ Generated markdown from governance_plan ({len(markdown_output_content)} chars)")
                    
                    # Append Detailed Risk Assessment section if not already included
                    if detailed_risk_assessment and '## Detailed Risk Assessment' not in markdown_output_content and '## 📋 Detailed Risk Assessment' not in markdown_output_content:
                        detailed_section = "\n\n---\n\n## 📋 Detailed Risk Assessment\n\n"
                        for item in detailed_risk_assessment:
                            category = item.get('category', 'Unknown')
                            description = item.get('description', '')
                            tools = item.get('recommended_tools', [])
                            
                            detailed_section += f"### {category}\n\n"
                            detailed_section += f"{description}\n\n"
                            if tools:
                                detailed_section += "**Recommended Tools:**\n\n"
                                for tool in tools:
                                    detailed_section += f"- {tool}\n"
                                detailed_section += "\n"
                        
                        markdown_output_content += detailed_section
                        logger.info(f"  ✓ Added Detailed Risk Assessment section to governance plan markdown")
                elif assessment:
                    # Export assessment data (matches example_basic.py pattern but with export)
                    # Create assessment dict matching assess_ai_system output structure
                    assessment_data = {
                        'system_description': system_description,
                        'risk_classification': risk_classification,
                        'applicable_regulations': applicable_regulations,
                        'recommended_skills': recommended_skills,
                        'initial_assessment': initial_assessment,
                        'detailed_risk_assessment': detailed_risk_assessment  # Add detailed risk assessment
                    }
                    markdown_output_content = governance_agent.export_assessment(assessment_data, format='markdown')
                    logger.info(f"  ✓ Generated markdown from assessment ({len(markdown_output_content)} chars)")
                    
                    # Append Detailed Risk Assessment section if not already included
                    if detailed_risk_assessment and '## Detailed Risk Assessment' not in markdown_output_content:
                        detailed_section = "\n\n---\n\n## 📋 Detailed Risk Assessment\n\n"
                        for item in detailed_risk_assessment:
                            category = item.get('category', 'Unknown')
                            description = item.get('description', '')
                            tools = item.get('recommended_tools', [])
                            
                            detailed_section += f"### {category}\n\n"
                            detailed_section += f"{description}\n\n"
                            if tools:
                                detailed_section += "**Recommended Tools:**\n\n"
                                for tool in tools:
                                    detailed_section += f"- {tool}\n"
                                detailed_section += "\n"
                        
                        markdown_output_content += detailed_section
                        logger.info(f"  ✓ Added Detailed Risk Assessment section to markdown")
                else:
                    raise ValueError("No assessment or governance_plan available for export")
            except Exception as e:
                logger.warning(f"  ⚠ Could not generate markdown from assessment: {e}")
                # Fallback: Create simple markdown
                detailed_risk_section = ""
                if detailed_risk_assessment:
                    detailed_risk_section = "\n## Detailed Risk Assessment\n\n"
                    for item in detailed_risk_assessment:
                        detailed_risk_section += f"### {item.get('category', 'Unknown')}\n\n"
                        detailed_risk_section += f"{item.get('description', '')}\n\n"
                        if item.get('recommended_tools'):
                            detailed_risk_section += "**Recommended Tools:**\n"
                            for tool in item.get('recommended_tools', []):
                                detailed_risk_section += f"- {tool}\n"
                            detailed_risk_section += "\n"
                
                markdown_output_content = f"""# AI Governance Assessment

## System Information
**Name:** {agent_name or f'AI System ID {agent_id}'}
**Assessment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Risk Classification
**Category:** {risk_category}
**Confidence:** {risk_classification.get('confidence', 'N/A')}
**Reasoning:** {risk_classification.get('reasoning', 'N/A')}

## Applicable Regulations
{chr(10).join(f'- {reg}' if isinstance(reg, str) else f'- {reg.get("name", reg)}' for reg in applicable_regulations[:10])}

## Recommended Skills
{chr(10).join(f'- {skill.get("skill", skill.get("name", "Unknown"))}' for skill in recommended_skills[:20])}

## Initial Assessment
{initial_assessment}
{detailed_risk_section}
## Governance Plan
{governance_plan.get('executive_summary', 'N/A') if governance_plan else 'N/A'}
"""
                logger.info(f"  ✓ Created fallback markdown ({len(markdown_output_content)} chars)")
        
        # Save markdown to file (for both Logic 1 and Logic 2)
        if markdown_output_content:
            logger.info("\n[OUTPUT] Saving markdown output to file...")
            try:
                # Create Output directory
                output_dir = Path(settings.BASE_DIR) / 'Output'
                output_dir.mkdir(exist_ok=True)
                logger.info(f"  Output directory: {output_dir}")
                
                # Generate output filename
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_agent_name = (agent_name or f"AI_System_{agent_id}").replace(' ', '_').replace('/', '_')
                output_filename = f"AI_GOVERNANCE_ASSESSMENT_{safe_agent_name}_{timestamp}.md"
                output_file_path = output_dir / output_filename
                
                # Save markdown content to file
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    # Add header with metadata
                    f.write(f"# AI Governance Framework Assessment\n")
                    f.write(f"## {agent_name or f'AI System ID {agent_id}'}\n\n")
                    f.write(f"**Assessment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"**System:** {agent_name or 'Unnamed AI System'}\n")
                    f.write(f"**Framework:** EU AI Act + NIST AI RMF + ISO/IEC 42001\n")
                    f.write(f"**Assessment Type:** {'Code Execution + Governance AI Agent' if code_files or dataset_files else 'Governance AI Agent (Advisory Layer)'}\n\n")
                    f.write("---\n\n")
                    f.write(markdown_output_content)
                
                logger.info(f"  ✓ Saved markdown output to: {output_file_path}")
                logger.info(f"    File size: {output_file_path.stat().st_size} bytes")
                
                # Store output file path in response (relative to BASE_DIR)
                output_file_relative = str(output_file_path.relative_to(settings.BASE_DIR))
                markdown_output_file = output_file_relative
            except Exception as e:
                logger.error(f"  ✗ Error saving markdown output file: {e}", exc_info=True)
                markdown_output_file = None
        
        if code_files or dataset_files:
            logger.info("LOGIC 2: Governance AI Agent + Code Execution - Completed Successfully")
        else:
            logger.info("LOGIC 1: Governance AI Agent - Full Flow Completed Successfully")
        logger.info("=" * 80 + "\n")
        
        return JsonResponse({
            'success': True,
            'assessment': {
                'prohibited_practices': prohibited_practices,
                'high_risk_classification': high_risk_classification,
                'gpai_applicability': gpai_applicability,
                'gpai_risk_level': gpai_risk_level,
                'risk_classification': risk_classification,
                'applicable_regulations': applicable_regulations,
                'recommended_skills': recommended_skills,
                'initial_assessment': initial_assessment,
                'detailed_risk_assessment': detailed_risk_assessment,
                'governance_plan': governance_plan,
                'markdown_output': markdown_output_content,  # Output from code execution (Logic 2)
                'markdown_output_file': markdown_output_file  # Path to saved markdown file (e.g., "Output/AI_GOVERNANCE_ASSESSMENT_...md")
            }
        })
        
    except Exception as e:
        logger.error(f"Error in api_assess_risk_evaluation: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def api_upload_risk_evaluation_files(request, agent_id):
    """
    Upload code and dataset files for risk evaluation.
    
    Expected form data:
    - code_files: File(s) to upload (can be multiple)
    - dataset_files: File(s) to upload (can be multiple)
    
    Returns JSON response with success status and file paths.
    """
    import logging
    from pathlib import Path
    from django.conf import settings
    import json
    import uuid



    import re
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("FILE UPLOAD: Risk Evaluation Files")
    logger.info("=" * 80)
    logger.info(f"Agent ID: {agent_id}")
    
    try:
        # Get agent data
        agents_data = get_mock_agents()
        agent = next((a for a in agents_data if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        # Get files from request
        print(f"\n{'='*80}")
        print(f"FILE UPLOAD DEBUG - REQUEST INFO:")
        print(f"  Request method: {request.method}")
        print(f"  Request content type: {request.content_type}")
        print(f"  Request FILES keys: {list(request.FILES.keys())}")
        print(f"  Request FILES count: {len(request.FILES)}")
        print(f"{'='*80}\n")
        
        code_files_uploaded = request.FILES.getlist('code_files')
        dataset_files_uploaded = request.FILES.getlist('dataset_files')
        
        print(f"\n{'='*80}")
        print(f"FILE UPLOAD DEBUG - FILES EXTRACTED:")
        print(f"  Code files count: {len(code_files_uploaded)}")
        print(f"  Dataset files count: {len(dataset_files_uploaded)}")
        for i, f in enumerate(dataset_files_uploaded):
            print(f"    Dataset file {i+1}: {f.name} ({f.size} bytes)")
        print(f"{'='*80}\n")
        
        logger.info(f"  Code files: {len(code_files_uploaded)}")
        logger.info(f"  Dataset files: {len(dataset_files_uploaded)}")
        logger.info(f"  Request FILES keys: {list(request.FILES.keys())}")
        
        if len(dataset_files_uploaded) == 0:
            print(f"  ⚠ WARNING: No dataset files found in request!")
            print(f"  This might mean:")
            print(f"    1. Frontend is not sending files correctly")
            print(f"    2. Field name mismatch (expected 'dataset_files')")
            print(f"    3. Request is not multipart/form-data")
            logger.warning(f"  ⚠ No dataset files found in request!")
        
        # Create upload directories
        BASE_DIR = Path(settings.BASE_DIR)
        uploads_dir = BASE_DIR / 'uploads' / 'risk_evaluation'
        code_dir = uploads_dir / 'code'
        dataset_dir = BASE_DIR / 'ai_act_articles'  # Datasets go to ai_act_articles/
        
        logger.info(f"  BASE_DIR: {BASE_DIR}")
        logger.info(f"  Dataset directory: {dataset_dir}")
        logger.info(f"  Dataset directory exists: {dataset_dir.exists()}")
        
        code_dir.mkdir(parents=True, exist_ok=True)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"  ✓ Created/verified directories")
        
        uploaded_code_files = []
        uploaded_dataset_files = []
        
        # Save code files
        print(f"\n{'='*80}")
        print(f"SAVING CODE FILES:")
        print(f"  Code files count: {len(code_files_uploaded)}")
        print(f"{'='*80}\n")
        logger.info(f"Processing {len(code_files_uploaded)} code file(s)...")
        
        for file in code_files_uploaded:
            try:
                print(f"\n  Processing code file: {file.name} ({file.size} bytes)")
                logger.info(f"  Processing code file: {file.name}")
                
                # Generate unique filename
                file_ext = Path(file.name).suffix
                unique_filename = f"{uuid.uuid4().hex}_{file.name}"
                file_path = code_dir / unique_filename
                
                # Save file first
                print(f"    Saving to: {file_path}")
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                # Update GEMINI_API_KEY in uploaded code file if it's a Python file
                if file_ext.lower() == '.py':
                    print(f"    Updating GEMINI_API_KEY in Python file...")
                    logger.info(f"    Updating GEMINI_API_KEY in code file: {file.name}")
                    
                    try:
                        # Read the saved file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code_content = f.read()
                        
                        original_content = code_content
                        modified = False
                        
                        # Ensure 'import os' is present if GEMINI_API_KEY is used
                        if 'GEMINI_API_KEY' in code_content and 'import os' not in code_content:
                            # Add import os at the top (after other imports if any)
                            lines = code_content.split('\n')
                            import_inserted = False
                            for i, line in enumerate(lines):
                                if line.strip().startswith('import ') or line.strip().startswith('from '):
                                    continue
                                elif line.strip() == '':
                                    continue
                                else:
                                    # Insert import os before first non-import line
                                    lines.insert(i, 'import os')
                                    import_inserted = True
                                    break
                            
                            if not import_inserted:
                                # If no imports found, add at the beginning
                                lines.insert(0, 'import os')
                            
                            code_content = '\n'.join(lines)
                            modified = True
                            print(f"      ✓ Added 'import os'")
                            logger.info(f"      ✓ Added 'import os'")
                        
                        # Update GEMINI_API_KEY to use os.environ.get
                        if 'GEMINI_API_KEY' in code_content:
                            lines = code_content.split('\n')
                            modified_lines = []
                            for line in lines:
                                # Check if this line contains GEMINI_API_KEY assignment
                                if re.match(r'^\s*GEMINI_API_KEY\s*=', line):
                                    # Check if it's already using os.environ.get
                                    if 'os.environ.get' not in line:
                                        # Replace with os.environ.get
                                        line = re.sub(
                                            r'GEMINI_API_KEY\s*=\s*[^\n]+',
                                            'GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")',
                                            line
                                        )
                                        modified = True
                                        print(f"      ✓ Updated GEMINI_API_KEY to use os.environ.get()")
                                        logger.info(f"      ✓ Updated GEMINI_API_KEY to use os.environ.get()")
                                    else:
                                        print(f"      ℹ GEMINI_API_KEY already uses os.environ.get()")
                                        logger.info(f"      ℹ GEMINI_API_KEY already uses os.environ.get()")
                                modified_lines.append(line)
                            
                            if modified:
                                code_content = '\n'.join(modified_lines)
                        
                        # Write updated content back to file
                        if modified:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(code_content)
                            print(f"      ✓ Saved updated code file")
                            logger.info(f"      ✓ Saved updated code file with GEMINI_API_KEY fix")
                    except Exception as update_error:
                        print(f"      ⚠ Could not update GEMINI_API_KEY: {update_error}")
                        logger.warning(f"      ⚠ Could not update GEMINI_API_KEY in code file: {update_error}")
                        # Continue anyway - file is saved, just not updated
                
                # Store relative path
                relative_path = str(file_path.relative_to(BASE_DIR))
                uploaded_code_files.append(relative_path)
                
                print(f"  ✓ Saved code file: {file.name} -> {relative_path}")
                logger.info(f"  ✓ Saved code file: {file.name} -> {relative_path}")
            except Exception as e:
                print(f"  ✗ Error saving code file {file.name}: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"  ✗ Error saving code file {file.name}: {e}", exc_info=True)
        
        # Save dataset files
        print(f"\n{'='*80}")
        print(f"SAVING DATASET FILES:")
        print(f"  Dataset files count: {len(dataset_files_uploaded)}")
        print(f"  Dataset directory: {dataset_dir}")
        print(f"  Dataset directory exists: {dataset_dir.exists()}")
        print(f"{'='*80}\n")
        logger.info(f"Processing {len(dataset_files_uploaded)} dataset file(s)...")
        
        if len(dataset_files_uploaded) == 0:
            print(f"  ⚠ WARNING: No dataset files to save!")
            print(f"  Check if frontend is sending files correctly.")
            logger.warning(f"  ⚠ No dataset files to save")
        else:
            for file in dataset_files_uploaded:
                try:
                    print(f"\n  Processing dataset file: {file.name} ({file.size} bytes)")
                    logger.info(f"  Processing dataset file: {file.name}")
                    
                    # Use original filename for datasets (they need to be referenced by name)
                    file_path = dataset_dir / file.name
                    
                    print(f"    Destination: {file_path}")
                    logger.info(f"  Saving dataset file: {file.name}")
                    logger.info(f"    Destination: {file_path}")
                    logger.info(f"    Dataset dir exists: {dataset_dir.exists()}")
                    logger.info(f"    File size: {file.size} bytes")
                    
                    # Save file
                    with open(file_path, 'wb+') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    # Verify file was saved
                    if file_path.exists():
                        saved_size = file_path.stat().st_size
                        print(f"    ✓ File saved successfully: {saved_size} bytes")
                        logger.info(f"    ✓ File saved successfully: {saved_size} bytes")
                    else:
                        print(f"    ✗ File was not saved: {file_path}")
                        logger.error(f"    ✗ File was not saved: {file_path}")
                        continue
                    
                    # Store relative path
                    relative_path = str(file_path.relative_to(BASE_DIR))
                    uploaded_dataset_files.append(relative_path)
                    
                    print(f"  ✓ Saved dataset file: {file.name} -> {relative_path}")
                    logger.info(f"  ✓ Saved dataset file: {file.name} -> {relative_path}")
                    
                    # Run setup_ai_act_store for this uploaded file only (not the entire ai_act_articles directory)
                    print(f"\n{'='*80}")
                    print(f"SETUP_AI_ACT_STORE: Starting for file: {file.name}")
                    print(f"{'='*80}")
                    print(f"  [VIEWS] About to run setup_ai_act_store for: {file.name}")
                    print(f"  [VIEWS] File path: {file_path}")
                    print(f"  [VIEWS] File exists: {file_path.exists()}")
                    logger.info(f"  Running setup_ai_act_store for uploaded file only: {file.name}")
                    
                    # Check GEMINI_API_KEY
                    import os
                    gemini_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, 'GEMINI_API_KEY', None)
                    print(f"  [VIEWS] Checking GEMINI_API_KEY...")
                    if not gemini_key:
                        print(f"  ⚠ WARNING: GEMINI_API_KEY not found in environment or settings!")
                        logger.warning(f"    ⚠ GEMINI_API_KEY not found, upload may fail")
                    else:
                        print(f"  ✓ GEMINI_API_KEY found (length: {len(gemini_key)})")
                        logger.info(f"    ✓ GEMINI_API_KEY found")
                    
                    print(f"  [VIEWS] Starting try block to import setup_ai_act_store...")
                    try:
                        import sys
                        import importlib.util
                        
                        print(f"  [VIEWS] sys and importlib.util imported")
                        
                        # Import setup_ai_act_store module
                        setup_script_path = BASE_DIR / 'setup_ai_act_store.py'
                        print(f"  [VIEWS] Checking for setup_ai_act_store.py at: {setup_script_path}")
                        print(f"  [VIEWS] Path exists: {setup_script_path.exists()}")
                        logger.info(f"    Looking for setup_ai_act_store.py at: {setup_script_path}")
                            
                        if not setup_script_path.exists():
                            # Try scripts directory
                            setup_script_path = BASE_DIR / 'scripts' / 'setup_ai_act_store.py'
                            print(f"  [VIEWS] Not found, trying: {setup_script_path}")
                            print(f"  [VIEWS] Alternative path exists: {setup_script_path.exists()}")
                            logger.info(f"    Not found, trying: {setup_script_path}")
                        
                        if setup_script_path.exists():
                            print(f"  [VIEWS] ✓ Found setup_ai_act_store.py")
                            print(f"  [VIEWS] About to load module...")
                            logger.info(f"    ✓ Found setup_ai_act_store.py at: {setup_script_path}")
                            
                            print(f"  [VIEWS] Creating spec...")
                            spec = importlib.util.spec_from_file_location("setup_ai_act_store", setup_script_path)
                            print(f"  [VIEWS] Creating module from spec...")
                            setup_module = importlib.util.module_from_spec(spec)
                            print(f"  [VIEWS] Adding to sys.modules...")
                            sys.modules["setup_ai_act_store"] = setup_module
                            print(f"  [VIEWS] Executing module (this should trigger module-level prints)...")
                            spec.loader.exec_module(setup_module)
                            print(f"  [VIEWS] ✓ Module loaded successfully")
                            logger.info(f"    ✓ Module loaded successfully")
                                
                            # Create client and store
                            print(f"  [VIEWS] Initializing Gemini API client...")
                            logger.info(f"    Initializing Gemini API client...")
                            print(f"  [VIEWS] Calling setup_module.create_client()...")
                            client = setup_module.create_client()
                            print(f"  [VIEWS] ✓ Client initialized")
                            logger.info(f"    ✓ Client initialized")
                            
                            print(f"  [VIEWS] Creating/getting File Search Store...")
                            logger.info(f"    Creating/getting File Search Store...")
                            print(f"  [VIEWS] Calling setup_module.create_file_search_store()...")
                            store = setup_module.create_file_search_store(client, quiet=False)
                            print(f"  [VIEWS] ✓ Store ready: {store.display_name}")
                            logger.info(f"    ✓ Store ready: {store.display_name}")
                            
                            # Upload only this uploaded file (not all files in ai_act_articles directory)
                            display_name = file.name
                            print(f"  [VIEWS] Uploading file to store:")
                            print(f"    File name: {file.name}")
                            print(f"    File path: {file_path}")
                            print(f"    Display name: {display_name}")
                            logger.info(f"    Running setup_ai_act_store for file: {file.name}")
                            logger.info(f"    File path: {file_path}")
                            logger.info(f"    Display name: {display_name}")
                            
                            print(f"  [VIEWS] Calling setup_module.upload_single_file()...")
                            success = setup_module.upload_single_file(client, store, file_path, display_name=display_name, quiet=False)
                            print(f"  [VIEWS] upload_single_file returned: {success}")
                            
                            if success:
                                print(f"  ✓ Successfully uploaded {file.name} to File Search Store")
                                logger.info(f"    ✓ Successfully uploaded {file.name} to File Search Store")
                            else:
                                print(f"  ℹ File {file.name} already exists in store, skipped")
                                logger.info(f"    ℹ File {file.name} already exists in store, skipped")
                            
                            print(f"{'='*80}\n")
                        else:
                            print(f"  ✗ setup_ai_act_store.py not found at: {setup_script_path}")
                            logger.warning(f"    ⚠ setup_ai_act_store.py not found, skipping store upload")
                    except Exception as e:
                        import traceback
                        error_msg = f"Error uploading to File Search Store: {e}"
                        print(f"  ✗ {error_msg}")
                        print(f"  Traceback:")
                        traceback.print_exc()
                        logger.error(f"    ✗ Could not upload to File Search Store: {e}", exc_info=True)
                        # Don't fail the upload if store upload fails
                        
                except Exception as e:
                    print(f"  ✗ Error saving dataset file {file.name}: {e}")
                    import traceback
                    traceback.print_exc()
                    logger.error(f"  ✗ Error saving dataset file {file.name}: {e}", exc_info=True)
                    logger.error(f"  Traceback: {traceback.format_exc()}")
        
        # Note: No longer updating AI_ACT_TEXT_PATH in code files
        # Code files should handle their own dataset file selection
        
        # Update agent data with uploaded files
        if 'risk_evaluation' not in agent:
            agent['risk_evaluation'] = {}
        
        # Merge with existing files
        existing_code_files = agent['risk_evaluation'].get('code_files', [])
        existing_dataset_files = agent['risk_evaluation'].get('dataset_files', [])
        
        agent['risk_evaluation']['code_files'] = list(set(existing_code_files + uploaded_code_files))
        agent['risk_evaluation']['dataset_files'] = list(set(existing_dataset_files + uploaded_dataset_files))
        
        # Save to agents.json
        try:
            mock_data_dir = Path(__file__).parent.parent / 'mock_data'
            agents_file = mock_data_dir / 'agents.json'
            
            # Update agent in list
            for i, a in enumerate(agents_data):
                if str(a.get('id')) == str(agent_id):
                    agents_data[i] = agent
                    break
            
            with open(agents_file, 'w', encoding='utf-8') as f:
                json.dump(agents_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"  ✓ Updated agents.json with uploaded files")
        except Exception as e:
            logger.warning(f"  ⚠ Could not save to agents.json: {e}")
        
        logger.info("=" * 80)
        logger.info("FILE UPLOAD: Completed Successfully")
        logger.info("=" * 80)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_code_files)} code file(s) and {len(uploaded_dataset_files)} dataset file(s)',
            'code_files': agent['risk_evaluation']['code_files'],
            'dataset_files': agent['risk_evaluation']['dataset_files']
        })
        
    except Exception as e:
        logger.error(f"Error in api_upload_risk_evaluation_files: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def api_delete_risk_evaluation_files(request, agent_id):
    """
    Delete code and dataset files for risk evaluation.
    
    Expected JSON body:
    {
        "code_files": ["path/to/file1.py", ...],  # Optional: list of code file paths to delete
        "dataset_files": ["path/to/file1.csv", ...]  # Optional: list of dataset file paths to delete
    }
    
    If empty lists or not provided, no files will be deleted.
    
    Returns JSON response with success status.
    """
    import logging
    from pathlib import Path
    from django.conf import settings
    import json
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("FILE DELETE: Risk Evaluation Files")
    logger.info("=" * 80)
    logger.info(f"Agent ID: {agent_id}")
    
    try:
        # Get agent data
        agents_data = get_mock_agents()
        agent = next((a for a in agents_data if str(a.get('id')) == str(agent_id)), None)
        
        if not agent:
            return JsonResponse({
                'success': False,
                'error': 'AI System not found'
            }, status=404)
        
        # Get file paths from request body
        request_data = json.loads(request.body) if request.body else {}
        code_files_to_delete = request_data.get('code_files', [])
        dataset_files_to_delete = request_data.get('dataset_files', [])
        
        logger.info(f"  Code files to delete: {len(code_files_to_delete)}")
        logger.info(f"  Dataset files to delete: {len(dataset_files_to_delete)}")
        
        BASE_DIR = Path(settings.BASE_DIR)
        deleted_code_files = []
        deleted_dataset_files = []
        errors = []
        
        # Delete code files
        for file_path_str in code_files_to_delete:
            try:
                file_path = BASE_DIR / file_path_str
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    deleted_code_files.append(file_path_str)
                    logger.info(f"  ✓ Deleted code file: {file_path_str}")
                else:
                    logger.warning(f"  ⚠ Code file not found: {file_path_str}")
            except Exception as e:
                error_msg = f"Error deleting code file {file_path_str}: {e}"
                logger.error(f"  ✗ {error_msg}", exc_info=True)
                errors.append(error_msg)
        
        # Delete dataset files
        for file_path_str in dataset_files_to_delete:
            try:
                file_path = BASE_DIR / file_path_str
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    deleted_dataset_files.append(file_path_str)
                    logger.info(f"  ✓ Deleted dataset file: {file_path_str}")
                else:
                    logger.warning(f"  ⚠ Dataset file not found: {file_path_str}")
            except Exception as e:
                error_msg = f"Error deleting dataset file {file_path_str}: {e}"
                logger.error(f"  ✗ {error_msg}", exc_info=True)
                errors.append(error_msg)
        
        # Update agent data to remove deleted files
        if 'risk_evaluation' not in agent:
            agent['risk_evaluation'] = {}
        
        # Remove deleted files from agent data
        existing_code_files = agent['risk_evaluation'].get('code_files', [])
        existing_dataset_files = agent['risk_evaluation'].get('dataset_files', [])
        
        agent['risk_evaluation']['code_files'] = [
            f for f in existing_code_files if f not in deleted_code_files
        ]
        agent['risk_evaluation']['dataset_files'] = [
            f for f in existing_dataset_files if f not in deleted_dataset_files
        ]
        
        # Save to agents.json
        try:
            mock_data_dir = Path(__file__).parent.parent / 'mock_data'
            agents_file = mock_data_dir / 'agents.json'
            
            # Update agent in list
            for i, a in enumerate(agents_data):
                if str(a.get('id')) == str(agent_id):
                    agents_data[i] = agent
                    break
            
            with open(agents_file, 'w', encoding='utf-8') as f:
                json.dump(agents_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"  ✓ Updated agents.json")
        except Exception as e:
            logger.warning(f"  ⚠ Could not save to agents.json: {e}")
        
        logger.info("=" * 80)
        logger.info("FILE DELETE: Completed")
        logger.info("=" * 80)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {len(deleted_code_files)} code file(s) and {len(deleted_dataset_files)} dataset file(s)',
            'deleted_code_files': deleted_code_files,
            'deleted_dataset_files': deleted_dataset_files,
            'errors': errors if errors else None
        })
        
    except Exception as e:
        logger.error(f"Error in api_delete_risk_evaluation_files: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
