"""
Governance Platform URLs - Standalone Hackathon Version
Simplified URLs without company_id
"""
from django.urls import path
from . import views

urlpatterns = [
    # Main Dashboard
    path("", views.governance_dashboard, name="dashboard"),
    
    # AI Systems
    path("ai-systems/", views.ai_systems, name="ai_systems"),
    path("ai-models/", views.ai_models, name="ai_models"),
    path("ai-assistant/", views.ai_assistant, name="ai_assistant"),
    # AI Assistant Chat API (must be before parameterized path)
    path("ai-assistant/chat", views.ai_act_chat_api, name="ai_assistant_chat_api"),
    path("ai-assistant/chat/delete/<str:chat_id>/", views.api_delete_chat_history, name="api_delete_chat_history"),
    path("ai-assistant/chat/clear_history/<str:agent_id>/", views.api_clear_chat_history, name="api_clear_chat_history"),
    path("ai-assistant/chat/<str:id>/", views.ai_assistant, name="ai_assistant_chat"),
    
    # AI Systems API
    path("api/ai-systems/agents/", views.api_create_ai_agent, name="api_create_ai_agent"),
    path("api/ai-systems/use-cases/", views.api_create_ai_use_case, name="api_create_ai_use_case"),
    path("api/ai-systems/models-datasets/", views.api_get_models_datasets, name="api_get_models_datasets"),
    path("api/ai-systems/models/", views.api_create_model, name="api_create_model"),
    path("api/ai-systems/datasets/", views.api_create_dataset, name="api_create_dataset"),
    
    # File Upload API
    path("api/upload/", views.api_upload, name="api_upload"),
    path("api/check-store-info/", views.api_check_store_info, name="api_check_store_info"),
    
    # Use Case Details API
    path("api/use-cases/<int:use_case_id>/evidences/", views.api_use_case_evidences, name="api_use_case_evidences"),
    path("api/use-cases/<int:use_case_id>/evidences/<int:evidence_id>/", views.api_delete_evidence, name="api_delete_evidence"),
    path("api/use-cases/<int:use_case_id>/evaluation-reports/", views.api_use_case_evaluation_reports, name="api_use_case_evaluation_reports"),
    path("api/use-cases/<int:use_case_id>/evaluation-reports/<int:report_id>/", views.api_delete_evaluation_report, name="api_delete_evaluation_report"),
    path("api/use-cases/<int:use_case_id>/review-comments/", views.api_use_case_review_comments, name="api_use_case_review_comments"),
    
    # Assessment/Questionnaires
    path("assessment/", views.assessment, name="assessment"),
    path("questionnaires/", views.assessment, name="questionnaires"),  # Alias
    path("assessment/library/", views.assessment_library, name="assessment_library"),
    path("assessment/<int:assessment_id>/", views.assessment_detail, name="assessment_detail"),
    
    # Questionnaire/Data Collection
    path("questionnaire/library/", views.questionnaire_library, name="questionnaire_library"),
    path("questionnaire/<int:questionnaire_id>/", views.questionnaire_detail, name="questionnaire_detail"),
    
    # Use Cases
    path("datasets/", views.datasets, name="datasets"),
    path("vendors/", views.vendors, name="vendors"),
    path("investment/", views.investment, name="investment"),
    path("multi-agent-use-cases/", views.multi_agent_use_cases, name="multi_agent_use_cases"),
    
    # Reporting/Framework
    path("framework/", views.framework, name="framework"),
    path("digital-regulations/", views.digital_regulations, name="digital_regulations"),
    # Digital Regulations nested EU Act pages
    path("digital-regulations/eu-act/gpihr/", views.eu_act_gpihr, name="digital_regulations_eu_act_gpihr"),
    path("digital-regulations/eu-act/gpilr/", views.eu_act_gpilr, name="digital_regulations_eu_act_gpilr"),
    path("digital-regulations/eu-act/hr/", views.eu_act_hr, name="digital_regulations_eu_act_hr"),
    path("digital-regulations/eu-act/lr/", views.eu_act_lr, name="digital_regulations_eu_act_lr"),
    
    # Agent Creation
    path("agent/creation/", views.agent_creation, name="agent_creation"),
    
    # Questionnaire Responses
    path("questionnaire/responses/", views.questionnaire_response, name="questionnaire_response"),
    path("questionnaire/responses/<int:response_id>/", views.questionnaire_response_detail, name="questionnaire_response_detail"),
    
    # Assessment Responses
    path("assessment/responses/", views.assessment_response, name="assessment_response"),
    path("assessment/responses/<int:response_id>/", views.assessment_response_detail, name="assessment_response_detail"),
    
    # EU Act Pages (keep for backward compatibility)
    path("eu-act/gpihr/", views.eu_act_gpihr, name="eu_act_gpihr"),
    path("eu-act/gpilr/", views.eu_act_gpilr, name="eu_act_gpilr"),
    path("eu-act/hr/", views.eu_act_hr, name="eu_act_hr"),
    path("eu-act/lr/", views.eu_act_lr, name="eu_act_lr"),
    path("eu-ai-act/framework/", views.eu_ai_act_framework, name="eu_ai_act_framework"),
    
    # Main EU Act Pages
    path("main/eu-act/gpihr/", views.main_eu_act_gpihr, name="main_eu_act_gpihr"),
    path("main/eu-act/gpilr/", views.main_eu_act_gpilr, name="main_eu_act_gpilr"),
    path("main/eu-act/hr/", views.main_eu_act_hr, name="main_eu_act_hr"),
    path("main/eu-act/lr/", views.main_eu_act_lr, name="main_eu_act_lr"),
    
    # Risk Registry & MRA
    path("mra/", views.mra, name="mra"),
    path("risk-overview/", views.risk_overview, name="risk_overview"),
]
