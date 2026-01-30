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
from django.views.decorators.csrf import csrf_exempt
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
    get_compliance_projects,
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
            # Return detail data
            detail_data = {
                'profile': agent.get('profile', {}),
                'assessment': agent.get('assessment', {}),
                'result': agent.get('result', {}),
                'documents': agent.get('documents', [])
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
                
                # Run assessment logic when profile is saved (Block 1, 2, 3, 4 - run in parallel)
                # This runs on BE as AI detection and assessment logic should be server-side
                # Pass existing assessment state to preserve user confirmations
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
    AI Detection Function (Random - will be updated later with actual AI logic).
    Returns True if AI detects prohibited practice, False otherwise.
    """
    return False


def run_assessment_logic(profile_data, assessment_state=None, reset_state=False):
    """
    Run assessment logic for Block 1, 2, 3, 4 in parallel (based on flowchart).
    
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
        'block2': get_block2_status(profile_data, block1_result=block1_result, block2_state=block2_state),
        'block3': get_block3_status(profile_data, block1_result=block1_result, block3_state=block3_state),
        'block4': get_block4_status(profile_data, block1_result=block1_result, block4_state=block4_state)
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
    Block 1: Prohibited Practices Screening - Logic based on flowchart.
    
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
    
    # Check if user has confirmed (from flowchart: "User Confirms")
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
    
    # After user confirms - Check Exception Availability (from flowchart)
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
    
    # From flowchart: "At least one hasException: true" → "Exception Question"
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
    
    # Evaluate combined results
    results = [qualifies_map.get(p) for p in practices_with_exception]
    
    if 'No' in results:
        # If any is "No" -> Prohibited
        return {
            'status': 'Prohibited',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'One or more exception claims were denied (answered "No")',
                'has_exception_available': True,
                'has_no_exception': False
            }
        }
    
    if 'Not sure' in results:
        # If any is "Not sure" (and none are "No") -> Needs Review
        # (Technically "otherwise prohibited" could mean this too, but Needs Review is more helpful)
        return {
            'status': 'Needs Review',
            'selected_practices': selected_practices,
            'practices_info': {p: prohibited_practices_map.get(p, {'label': p, 'article': 'Unknown'}) for p in selected_practices},
            'details': {
                'reason': 'Uncertain about at least one exception qualification',
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
    AI Detection for Block 2: High-Risk Classification (random placeholder).
    Returns True if AI detects high-risk, False otherwise.
    Image/flowchart: "AI Detects High-risk classification" → Yes = Trigger High-risk.
    """
    return False


def get_block2_status(profile_data, block1_result=None, block2_state=None):
    """
    Block 2: High-Risk Classification - Logic theo flowchart image.
    
    Flowchart order:
    1. AI Detects High-risk = Yes → Trigger High-risk (status Triggered)
    2. AI = No → Check Block 1: Block 1 = Prohibited → Trigger High-risk; ≠ Prohibited → Section 4
    3. Section 4 (Q3 Safety, Q2 Sector): Not all answered → Not assessed; All answered → Condition 1/2
    4. No conditions met → De-activated; Condition 1 or 2 or both → Trigger High-risk
    5. Triggered + User Confirms → Condition 1 ONLY → High-risk; Condition 2 or Both → Annex III
    6. Annex III: Q1 (Material influence) → Q2 (Task type) → Q3 (Profiling) → Evidence
    """
    if block2_state is None:
        block2_state = {}
    ip = profile_data.get('intended_purpose', {}) or {}
    sector_domain = ip.get('sector_domain') or []
    if not isinstance(sector_domain, list):
        sector_domain = []
    safety_component = ip.get('safety_component', '')
    third_party_conformity = ip.get('third_party_conformity', '')

    # 1) AI Detects High-risk = Yes → Trigger High-risk (flowchart)
    # IMPORTANT: If user already confirmed, return High-risk (prevents confirmation being
    # overridden by the random AI-detection placeholder on subsequent re-runs).
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

    # 2) Check Block 1 Status (flowchart)
    block1_prohibited = False
    if block1_result is not None:
        s = block1_result.get('status', '') if isinstance(block1_result, dict) else str(block1_result)
        block1_prohibited = (s == 'Prohibited')

    if block1_prohibited:
        high_risk_confirmed = block2_state.get('high_risk_confirmed', False)
        if high_risk_confirmed:
            return {
                'status': 'High-risk',
                'details': {
                    'reason': 'Block 1 Prohibited, user confirmed high-risk',
                    'trigger': 'block1_prohibited',
                },
            }
        return {
            'status': 'Triggered',
            'details': {
                'reason': 'Block 1 Prohibited – high-risk trigger; confirm or edit profile',
                'trigger': 'block1_prohibited',
            },
        }

    # 3) Section 4: Q3 Safety Component?, Q2 Sector Selected? – “Not all answered” → Not assessed
    has_sector = len(sector_domain) > 0
    has_safety = safety_component != ''
    if not has_sector and not has_safety:
        return {
            'status': 'Not assessed',
            'details': {'reason': 'Section 4 not answered (Q2 Sector, Q3 Safety)'},
        }
    if safety_component == 'Yes' and third_party_conformity == '':
        return {
            'status': 'Not assessed',
            'details': {'reason': 'Safety component Yes but third-party conformity not answered'},
        }

    # 4) Condition 1 (Safety + Third-party) / Condition 2 (Sector selected)
    condition1 = safety_component == 'Yes' and third_party_conformity == 'Yes'
    condition2 = any(
        s not in ('Other / not listed', 'Other / not listed:', '')
        for s in sector_domain
    )

    if not condition1 and not condition2:
        return {
            'status': 'De-activated',
            'details': {
                'reason': 'No high-risk conditions met',
                'condition1': False,
                'condition2': False,
            },
        }

    # 5) Condition 1 or 2 or both → Trigger; nếu chưa confirm → Triggered
    high_risk_confirmed = block2_state.get('high_risk_confirmed', False)
    if not high_risk_confirmed:
        return {
            'status': 'Triggered',
            'details': {
                'reason': 'High-risk conditions met, awaiting confirmation',
                'condition1': condition1,
                'condition2': condition2,
                'trigger': 'both' if (condition1 and condition2) else ('condition1' if condition1 else 'condition2'),
            },
        }

    # 6) User đã confirm → Which condition triggered?
    # Condition 1 ONLY → Status: High-risk (flowchart)
    if condition1 and not condition2:
        return {
            'status': 'High-risk',
            'details': {
                'reason': 'Safety component + third-party conformity (Condition 1 only)',
                'condition1': True,
                'condition2': False,
            },
        }

    # 7) Condition 2 or Both → Annex III Exemption Test (flowchart)
    material_influence = block2_state.get('material_influence', '')
    narrow_tasks = block2_state.get('narrow_tasks') or []
    if not isinstance(narrow_tasks, list):
        narrow_tasks = []
    profiling = block2_state.get('profiling', '')
    exemption_evidence = block2_state.get('exemption_evidence_uploaded', False) or bool(
        (block2_state.get('exemption_evidence_saved_link') or '').strip()
    )

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
            'status': 'Not high-risk',
            'details': {
                'reason': 'Annex III Q1: Material influence Yes → Not high-risk (per flowchart)',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q1',
            },
        }

    if material_influence != 'No':
        return {
            'status': 'Triggered',
            'details': {
                'reason': 'Annex III: awaiting Q1 (Material influence)',
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
            'status': 'Triggered',
            'details': {
                'reason': 'Annex III: awaiting Q2 (Task type selection)',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q2',
            },
        }
    if none_of_above:
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Annex III Q2: None of above → Needs review (per flowchart)',
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
            'status': 'Triggered',
            'details': {
                'reason': 'Annex III: awaiting Q3 (Profiling)',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'q3',
            },
        }

    # Profiling = No → Evidence (flowchart: Ask for Evidence & check Uploaded or Link Saved?)
    if exemption_evidence:
        return {
            'status': 'Not high-risk',
            'details': {
                'reason': 'Annex III: Profiling No + evidence provided → Not high-risk',
                'condition1': condition1,
                'condition2': condition2,
                'step': 'evidence',
            },
        }
    return {
        'status': 'High-risk',
        'details': {
            'reason': 'Annex III: Profiling No but no exemption evidence yet',
            'condition1': condition1,
            'condition2': condition2,
            'step': 'evidence',
        },
    }


def get_block3_status(profile_data, block1_result=None, block3_state=None):
    """
    Block 3: Transparency Obligation - Logic theo flowchart image.
    
    Flowchart order:
    1. Check Block 1 Status → Block 1 = Prohibited → De-activated
    2. Block 1 ≠ Prohibited → Check 6 Trigger Conditions
    3. Triggers + Unknowns và Questions not all answered → Not assessed
    4. Triggers met → Status: Triggered
    5. User Confirms → Exception Selection for Each Group
    6. Valid exceptions for all groups → Evidence check
    7. 'None of above' for any group → Applies
    8. Incomplete selections → Needs Review
    """
    if block3_state is None:
        block3_state = {}
    
    # 1) Check Block 1 Status (flowchart)
    block1_prohibited = False
    if block1_result is not None:
        s = block1_result.get('status', '') if isinstance(block1_result, dict) else str(block1_result)
        block1_prohibited = (s == 'Prohibited')
    
    if block1_prohibited:
        return {
            'status': 'De-activated',
            'details': {'reason': 'Block 1 Prohibited - transparency obligation assessment not applicable'}
        }
    
    # 2) Check 6 Trigger Conditions (flowchart)
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
    
    # Check if questions not all answered (flowchart: "Questions not all answered")
    if len(capability_practices) == 0:
        return {
            'status': 'Not assessed',
            'details': {'reason': 'Capabilities not answered (Section 7, Q1)'}
        }
    
    # Get 6 trigger cases
    triggers = []
    
    # Case 1: Biometric identification and categorisation
    if any('Biometric identification and categorisation' in p for p in capability_practices):
        triggers.append('case1')
    
    # Case 2: Emotion recognition in workplace/education
    if any('Emotion recognition in the workplace or in education settings' in p for p in capability_practices):
        triggers.append('case2')
    
    # Case 3: Biometric categorisation (sensitive traits)
    if any('Biometric categorisation that infers or predicts sensitive traits' in p for p in capability_practices):
        triggers.append('case3')
    
    # Case 4: Direct interaction with persons
    if interacts_persons == 'Yes':
        triggers.append('case4')
    
    # Case 5: Synthetic content (any choice other than No)
    if len(synthetic_content) > 0 and 'No' not in synthetic_content:
        triggers.append('case5')
    
    # Case 6: Citizens/residents OR General public facing
    if 'Citizens / residents' in affected_outputs or deployment_context == 'General public / consumer-facing':
        triggers.append('case6')
    
    # Check for unknowns (flowchart: "Triggers + Unknowns")
    has_unknowns = (interacts_persons == 'Unknown')
    
    # 3) Triggers + Unknowns và Questions not all answered → Not assessed (flowchart)
    if has_unknowns and len(triggers) > 0:
        return {
            'status': 'Not assessed',
            'details': {
                'reason': 'Triggers detected but questions not all answered (Unknown values)',
                'triggers': triggers,
                'has_unknowns': True
            }
        }
    
    # 4) No triggers met → Not Applicable (flowchart: implicit)
    if len(triggers) == 0:
        return {
            'status': 'Not Applicable',
            'details': {'reason': 'No transparency triggers detected'}
        }
    
    # 5) Triggers met → Status: Triggered (flowchart)
    transparency_confirmed = block3_state.get('transparency_confirmed', False)
    
    if not transparency_confirmed:
        # Check if has unknowns (flowchart: "Triggers + Unknowns")
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
    
    # 6) User Confirms → Exception Selection for Each Group (flowchart)
    exception_options = block3_state.get('exception_options', [])
    if not isinstance(exception_options, list):
        exception_options = []
    
    # Map triggers to case groups
    case_groups = []
    if 'case1' in triggers or 'case2' in triggers or 'case3' in triggers:
        case_groups.append('group1_2_3')  # Biometric/Emotion
    if 'case4' in triggers:
        case_groups.append('group4')  # Direct interaction
    if 'case5' in triggers:
        case_groups.append('group5')  # Synthetic content
    if 'case6' in triggers:
        case_groups.append('group6')  # Citizens/Public
    
    # Exception options by group
    group1_2_3_options = [
        'Permitted by law to detect, prevent or investigate criminal offences, as stated in Art. 50(3)',
        'None of the above (no exception for biometric/emotion recognition cases)'
    ]
    group4_options = [
        '"Obvious to the user" exception (no notice needed), as stated in Art. 50(1)',
        'Authorised by law to detect, prevent, investigate or prosecute criminal offences, as stated in Art. 50(1)',
        'None of the above (no exception for direct interaction case)'
    ]
    group5_options = [
        'Deepfake labelling exception (e.g., artistic / satire / fiction), as stated in Art. 50(4)',
        'None of the above (no exception for synthetic content case)'
    ]
    group6_options = [
        'Authorised by law to detect, prevent, investigate or prosecute criminal offences, as stated in Art. 50(4)',
        'Human review is in place or a natural or legal person holds editorial responsibility for the publication of the content, as stated in Art. 50(4)',
        'None of the above (no exception for citizens/public-facing case)'
    ]
    
    # Check if "None of above" for any group (flowchart)
    has_no_exception = False
    for opt in exception_options:
        if 'None of the above' in opt:
            has_no_exception = True
            break
    
    if has_no_exception:
        return {
            'status': 'Applies',
            'details': {
                'reason': '"None of the above" selected for at least one case group - transparency obligations apply',
                'triggers': triggers,
                'case_groups': case_groups
            }
        }
    
    # Check if valid exceptions for all groups (flowchart)
    has_exception_for_all = True
    if 'group1_2_3' in case_groups:
        has_group1_2_3 = any(opt in group1_2_3_options and 'None of the above' not in opt for opt in exception_options)
        if not has_group1_2_3:
            has_exception_for_all = False
    if 'group4' in case_groups:
        has_group4 = any(opt in group4_options and 'None of the above' not in opt for opt in exception_options)
        if not has_group4:
            has_exception_for_all = False
    if 'group5' in case_groups:
        has_group5 = any(opt in group5_options and 'None of the above' not in opt for opt in exception_options)
        if not has_group5:
            has_exception_for_all = False
    if 'group6' in case_groups:
        has_group6 = any(opt in group6_options and 'None of the above' not in opt for opt in exception_options)
        if not has_group6:
            has_exception_for_all = False
    
    # 7) Incomplete selections → Needs Review (flowchart)
    if not has_exception_for_all:
        return {
            'status': 'Needs Review',
            'details': {
                'reason': 'Incomplete exception selections - not all case groups have valid exceptions',
                'triggers': triggers,
                'case_groups': case_groups
            }
        }
    
    # 8) Valid exceptions for all groups → Evidence check (flowchart)
    evidence_uploaded = block3_state.get('transparency_evidence_uploaded', False)
    evidence_saved_link = block3_state.get('transparency_evidence_saved_link', '')
    evidence_provided = evidence_uploaded or bool((evidence_saved_link or '').strip())
    
    if evidence_provided:
        return {
            'status': 'Not Applicable',
            'details': {
                'reason': 'Valid exceptions for all groups with evidence provided - transparency obligations do not apply',
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


def get_block4_status(profile_data, block1_result=None, block4_state=None):
    """
    Block 4: GPAI Obligation - Logic theo flowchart image.
    
    Flowchart order:
    1. Check Block 1 Status → Block 1 = Prohibited → De-activated
    2. Block 1 ≠ Prohibited → Q2: Is this GPAI or integrates one?
    3. Q2 Not answered → Not assessed
    4. Q2 No → Needs Review
    5. Q2 Unknown → Triggered → Needs Review
    6. Q2 Yes → Show Reason Confirm or Edit?
    7. User Confirms → Are you the provider of AI model?
       - No → Not Applicable
       - Yes → Applies
       - Not sure → Needs Review
       - No selection → Needs Review
    """
    if block4_state is None:
        block4_state = {}
    
    # 1) Check Block 1 Status (flowchart)
    block1_prohibited = False
    if block1_result is not None:
        s = block1_result.get('status', '') if isinstance(block1_result, dict) else str(block1_result)
        block1_prohibited = (s == 'Prohibited')
    
    if block1_prohibited:
        return {
            'status': 'De-activated',
            'details': {'reason': 'Block 1 Prohibited - GPAI obligation assessment not applicable'}
        }
    
    # 2) Q2: Is this GPAI or integrates one? (flowchart)
    gpai_integration = profile_data.get('gpai_integration', '')
    
    # 3) Q2 Not answered → Not assessed (flowchart)
    if gpai_integration == '':
        return {
            'status': 'Not assessed',
            'details': {'reason': 'GPAI integration question not answered (Section 8, Q2)'}
        }
    
    # 4) Q2 No → Needs Review (flowchart)
    if gpai_integration == 'No':
        return {
            'status': 'Needs Review',
            'details': {'reason': 'GPAI integration = No - needs review (per flowchart)'}
        }
    
    # 5) Q2 Unknown → Triggered → Needs Review (flowchart)
    if gpai_integration == 'Unknown':
        gpai_confirmed = block4_state.get('gpai_confirmed', False)
        if not gpai_confirmed:
            return {
                'status': 'Triggered',
                'details': {
                    'reason': 'GPAI integration = Unknown - triggered, awaiting confirmation',
                    'gpai_integration': 'Unknown'
                }
            }
        # After confirmation, Unknown leads to Needs Review
        return {
            'status': 'Needs Review',
            'details': {'reason': 'GPAI integration = Unknown - requires review'}
        }
    
    # 6) Q2 Yes → Show Reason Confirm or Edit? (flowchart)
    if gpai_integration == 'Yes':
        gpai_confirmed = block4_state.get('gpai_confirmed', False)
        
        if not gpai_confirmed:
            return {
                'status': 'Triggered',
                'details': {
                    'reason': 'GPAI integration = Yes - awaiting confirmation',
                    'gpai_integration': 'Yes'
                }
            }
        
        # 7) User Confirms → Are you the provider of AI model? (flowchart)
        gpai_provider_answer = block4_state.get('gpai_provider_answer', '')
        
        # No selection → Needs Review (flowchart)
        if gpai_provider_answer == '':
            return {
                'status': 'Needs Review',
                'details': {
                    'reason': 'GPAI integration confirmed but provider question not answered',
                    'gpai_integration': 'Yes'
                }
            }
        
        # No → Not Applicable (flowchart)
        if gpai_provider_answer == 'No':
            return {
                'status': 'Not Applicable',
                'details': {
                    'reason': 'GPAI integration = Yes but not a provider - Chapter V does not apply',
                    'gpai_integration': 'Yes',
                    'gpai_provider_answer': 'No'
                }
            }
        
        # Not sure → Needs Review (flowchart)
        if gpai_provider_answer == 'Not sure':
            return {
                'status': 'Needs Review',
                'details': {
                    'reason': 'GPAI provider status uncertain - requires review',
                    'gpai_integration': 'Yes',
                    'gpai_provider_answer': 'Not sure'
                }
            }
        
        # Yes → Applies (flowchart)
        if gpai_provider_answer == 'Yes':
            return {
                'status': 'Applies',
                'details': {
                    'reason': 'GPAI provider - Chapter V obligations apply',
                    'gpai_integration': 'Yes',
                    'gpai_provider_answer': 'Yes'
                }
            }
    
    # Default fallback
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
                'exemption_evidence_saved_link': ''
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
        
        # Re-run assessment logic to get updated status
        if 'profile' in agent:
            assessment_state = agent.get('assessment', {})
            assessment_results = run_assessment_logic(agent['profile'], assessment_state)
            agent['assessment'].update(assessment_results)
        
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
            agent['assessment'].update(assessment_results)
        
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
            agent['assessment'].update(assessment_results)
        
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
            agent['assessment'].update(assessment_results)
        
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


def compliance(request):
    """
    Compliance page - Active projects overview (UI based on design).
    Data loaded from mock_data/compliance_projects.json.
    """
    ensure_governance_platform(request)

    company = MockCompany()
    breadcrumbs = [
        {"name": "Compliance", "url": request.build_absolute_uri()},
    ]

    projects = get_compliance_projects()
    total_projects = len(projects)
    active_projects = total_projects  # demo: all active
    not_compliant_count = 3  # demo for alert banner
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
    })

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
