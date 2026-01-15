"""
Dependency Injection Container
Following Dependency Injection pattern
"""
from pathlib import Path
from ..infrastructure.repositories.mock_agent_repository import MockAgentRepository
from ..infrastructure.repositories.mock_use_case_repository import MockUseCaseRepository
from ..infrastructure.repositories.mock_model_repository import MockModelRepository
from ..infrastructure.repositories.mock_dataset_repository import MockDatasetRepository
from ..infrastructure.repositories.mock_evidence_repository import (
    MockEvidenceRepository,
    MockEvaluationReportRepository
)
from ..infrastructure.repositories.mock_review_comment_repository import MockReviewCommentRepository
from ..application.use_cases.get_dashboard_data import GetDashboardDataUseCase
from ..application.use_cases.get_assessment_data import GetAssessmentDataUseCase
from ..application.use_cases.get_multi_agent_use_cases import GetMultiAgentUseCasesUseCase


class DependencyContainer:
    """Dependency injection container"""
    
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._data_dir = base_dir / 'mock_data'
        
        # Initialize repositories
        self._agent_repository = MockAgentRepository(self._data_dir)
        self._use_case_repository = MockUseCaseRepository(self._data_dir)
        self._model_repository = MockModelRepository(self._data_dir)
        self._dataset_repository = MockDatasetRepository(self._data_dir)
        self._evidence_repository = MockEvidenceRepository(self._data_dir)
        self._evaluation_report_repository = MockEvaluationReportRepository(self._data_dir)
        self._review_comment_repository = MockReviewCommentRepository(self._data_dir)
        
        # Initialize use cases
        self._get_dashboard_data_use_case = GetDashboardDataUseCase(
            agent_repository=self._agent_repository,
            use_case_repository=self._use_case_repository,
            model_repository=self._model_repository,
            dataset_repository=self._dataset_repository,
            evidence_repository=self._evidence_repository,
            evaluation_report_repository=self._evaluation_report_repository,
        )
        
        self._get_assessment_data_use_case = GetAssessmentDataUseCase(
            agent_repository=self._agent_repository,
            use_case_repository=self._use_case_repository,
            model_repository=self._model_repository,
            dataset_repository=self._dataset_repository,
            evidence_repository=self._evidence_repository,
            evaluation_report_repository=self._evaluation_report_repository,
            review_comment_repository=self._review_comment_repository,
        )
        
        self._get_multi_agent_use_cases_use_case = GetMultiAgentUseCasesUseCase(
            agent_repository=self._agent_repository,
            use_case_repository=self._use_case_repository,
            model_repository=self._model_repository,
            dataset_repository=self._dataset_repository,
            evidence_repository=self._evidence_repository,
            evaluation_report_repository=self._evaluation_report_repository,
            review_comment_repository=self._review_comment_repository,
        )
    
    @property
    def get_dashboard_data_use_case(self) -> GetDashboardDataUseCase:
        """Get dashboard data use case"""
        return self._get_dashboard_data_use_case
    
    @property
    def agent_repository(self):
        """Get agent repository"""
        return self._agent_repository
    
    @property
    def use_case_repository(self):
        """Get use case repository"""
        return self._use_case_repository
    
    @property
    def model_repository(self):
        """Get model repository"""
        return self._model_repository
    
    @property
    def dataset_repository(self):
        """Get dataset repository"""
        return self._dataset_repository
    
    @property
    def get_assessment_data_use_case(self) -> GetAssessmentDataUseCase:
        """Get assessment data use case"""
        return self._get_assessment_data_use_case
    
    @property
    def get_multi_agent_use_cases_use_case(self) -> GetMultiAgentUseCasesUseCase:
        """Get multi-agent use cases use case"""
        return self._get_multi_agent_use_cases_use_case


# Global container instance (will be initialized in views)
_container: DependencyContainer = None


def get_container(base_dir: Path = None) -> DependencyContainer:
    """Get or create dependency container"""
    global _container
    if _container is None and base_dir:
        _container = DependencyContainer(base_dir)
    return _container
