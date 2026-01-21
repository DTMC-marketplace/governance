"""
Get Multi-Agent Use Cases Use Case
Encapsulates business logic for multi-agent use cases page
"""
from typing import Optional, Protocol
from ...domain.repositories.agent_repository import IAgentRepository
from ...domain.repositories.use_case_repository import IUseCaseRepository
from ...domain.repositories.model_repository import IModelRepository
from ...domain.repositories.dataset_repository import IDatasetRepository
from ...domain.services.compliance_service import ComplianceService


class IEvidenceRepository(Protocol):
    """Protocol for evidence repository"""
    def get_by_use_case_id(self, use_case_id: int) -> list:
        pass


class IEvaluationReportRepository(Protocol):
    """Protocol for evaluation report repository"""
    def get_by_use_case_id(self, use_case_id: int) -> list:
        pass


class IReviewCommentRepository(Protocol):
    """Protocol for review comment repository"""
    def get_by_use_case_id(self, use_case_id: int) -> list:
        pass


class GetMultiAgentUseCasesUseCase:
    """Use case for getting multi-agent use cases data"""
    
    def __init__(
        self,
        agent_repository: IAgentRepository,
        use_case_repository: IUseCaseRepository,
        model_repository: IModelRepository,
        dataset_repository: IDatasetRepository,
        evidence_repository: IEvidenceRepository,
        evaluation_report_repository: IEvaluationReportRepository,
        review_comment_repository: IReviewCommentRepository,
    ):
        self._agent_repository = agent_repository
        self._use_case_repository = use_case_repository
        self._model_repository = model_repository
        self._dataset_repository = dataset_repository
        self._evidence_repository = evidence_repository
        self._evaluation_report_repository = evaluation_report_repository
        self._review_comment_repository = review_comment_repository
        self._compliance_service = ComplianceService()
    
    def execute(
        self,
        search_term: str = '',
        agent_name: Optional[str] = None,
        use_case_id: Optional[int] = None,
        page_number: int = 1,
        limit: int = 10,
    ) -> dict:
        """Execute the use case"""
        # Get all data
        use_cases_data = self._use_case_repository.get_all()
        models_data = self._model_repository.get_all()
        datasets_data = self._dataset_repository.get_all()
        agents_data = self._agent_repository.get_all()
        
        # Filter by agent if provided
        agent = None
        if agent_name:
            # Use case-insensitive matching to handle URL encoding
            agent_name_lower = agent_name.lower().strip()
            agent = next(
                (a for a in agents_data if a.name.lower().strip() == agent_name_lower), 
                None
            )
            if agent:
                use_cases_data = [
                    uc for uc in use_cases_data 
                    if uc.agent_id == agent.id
                ]
        
        # Filter by search term
        if search_term:
            use_cases_data = [
                uc for uc in use_cases_data 
                if search_term.lower() in uc.name.lower()
            ]
        
        # Build use cases list
        use_cases_list = []
        for use_case in use_cases_data:
            # Find and assign agent to use_case
            agent_id = use_case.agent_id
            if agent_id:
                use_case_agent = next(
                    (a for a in agents_data if a.id == agent_id), 
                    None
                )
                if use_case_agent:
                    use_case.agent = use_case_agent
                else:
                    # Create a default agent if not found using factory
                    from ...domain.factories.agent_factory import AgentFactory
                    use_case.agent = AgentFactory.create_from_dict({
                        'id': agent_id,
                        'name': 'Unknown Agent',
                        'description': '',
                        'compliance_status': 'assessing',
                        'risk_classification': 'limited_risks',
                    })
            else:
                # Create a default agent using factory
                from ...domain.factories.agent_factory import AgentFactory
                use_case.agent = AgentFactory.create_from_dict({
                    'id': None,
                    'name': 'No Agent',
                    'description': '',
                    'compliance_status': 'assessing',
                    'risk_classification': 'limited_risks',
                })
            
            compliance = self._compliance_service.calculate_compliance(use_case)
            risks = self._compliance_service.calculate_risks(use_case)
            
            models = [
                m for m in models_data 
                if m.id in use_case.models
            ]
            datasets = [
                d for d in datasets_data 
                if d.id in use_case.datasets
            ]
            
            use_cases_list.append({
                'use_case': use_case,
                'compliance': {
                    'status': compliance.status.value,
                    'gdpr': compliance.gdpr,
                    'eu_ai_act': compliance.eu_ai_act,
                    'data_act': compliance.data_act,
                },
                'risks': risks,
                'models': models,
                'datasets': datasets,
            })
        
        # Return all use cases, pagination handled in view layer
        
        # Get selected use case
        selected_use_case = None
        if use_case_id:
            selected_use_case = next(
                (uc for uc in use_cases_list 
                 if uc['use_case'].id == use_case_id), 
                None
            )
            if selected_use_case:
                selected_use_case = selected_use_case['use_case']
        
        # Get evidences, reports, comments
        evidences_data = self._evidence_repository.get_by_use_case_id(None)
        evaluation_reports_data = self._evaluation_report_repository.get_by_use_case_id(None)
        review_comments_data = self._review_comment_repository.get_by_use_case_id(None)
        
        if selected_use_case:
            # Filter by selected use case
            evidences_data = [
                e for e in evidences_data 
                if e.get('use_case_id') == selected_use_case.id
            ]
            evaluation_reports_data = [
                r for r in evaluation_reports_data 
                if r.get('use_case_id') == selected_use_case.id
            ]
            review_comments_data = [
                c for c in review_comments_data 
                if c.get('use_case_id') == selected_use_case.id
            ]
        elif agent and use_cases_list:
            # Filter by all use cases of the agent
            agent_use_case_ids = [uc['use_case'].id for uc in use_cases_list]
            evidences_data = [
                e for e in evidences_data 
                if e.get('use_case_id') in agent_use_case_ids
            ]
            evaluation_reports_data = [
                r for r in evaluation_reports_data 
                if r.get('use_case_id') in agent_use_case_ids
            ]
            review_comments_data = [
                c for c in review_comments_data 
                if c.get('use_case_id') in agent_use_case_ids
            ]
        
        # Build reports dict
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
        for report in evaluation_reports_data:
            report_type = report.get('report_type')
            if report_type:
                reports_dict[report_type] = report
        
        return {
            'agent_name': agent_name,
            'agent': agent,
            'use_cases_data': use_cases_list,  # Return all, pagination in view
            'search_term': search_term,
            'limit': limit,
            'all_models': models_data,
            'all_datasets': datasets_data,
            'all_agents': agents_data,
            'selected_use_case': selected_use_case,
            'evidences': evidences_data,
            'evaluation_reports': evaluation_reports_data,
            'review_comments': review_comments_data,
            'report_types': report_types,
            'reports_dict': reports_dict,
        }
