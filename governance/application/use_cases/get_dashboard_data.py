"""
Get Dashboard Data Use Case
"""
from typing import Protocol
from ..dtos.dashboard_dto import DashboardDTO, DataCollectionProgressDTO, RiskScoringDTO, ReportingProgressDTO, FrameworkProgressDTO
from ...domain.entities.use_case import UseCase
from ...domain.entities.agent import Agent
from ...domain.services.compliance_service import ComplianceService
from ...domain.repositories.agent_repository import IAgentRepository
from ...domain.repositories.use_case_repository import IUseCaseRepository
from ...domain.repositories.model_repository import IModelRepository
from ...domain.repositories.dataset_repository import IDatasetRepository


class IEvidenceRepository(Protocol):
    """Protocol for evidence repository"""
    def get_by_use_case_id(self, use_case_id: int) -> list:
        pass


class IEvaluationReportRepository(Protocol):
    """Protocol for evaluation report repository"""
    def get_by_use_case_id(self, use_case_id: int) -> list:
        pass


class GetDashboardDataUseCase:
    """Use case for getting dashboard data"""
    
    def __init__(
        self,
        agent_repository: IAgentRepository,
        use_case_repository: IUseCaseRepository,
        model_repository: IModelRepository,
        dataset_repository: IDatasetRepository,
        evidence_repository: IEvidenceRepository,
        evaluation_report_repository: IEvaluationReportRepository,
    ):
        self._agent_repository = agent_repository
        self._use_case_repository = use_case_repository
        self._model_repository = model_repository
        self._dataset_repository = dataset_repository
        self._evidence_repository = evidence_repository
        self._evaluation_report_repository = evaluation_report_repository
        self._compliance_service = ComplianceService()
    
    def execute(self) -> DashboardDTO:
        """Execute the use case"""
        # Get all data
        all_use_cases = self._use_case_repository.get_all()
        all_agents = self._agent_repository.get_all()
        all_evidences = self._evidence_repository.get_by_use_case_id(None)
        all_reports = self._evaluation_report_repository.get_by_use_case_id(None)
        
        # Calculate statistics
        total_use_cases = len(all_use_cases)
        assessed_use_cases = sum(1 for uc in all_use_cases if uc.compliance_assessed)
        
        # Under reviewed
        under_reviewed = sum(
            1 for uc in all_use_cases 
            if uc.review_status.value in ['partial', 'complete']
        )
        under_reviewed += sum(
            1 for agent in all_agents 
            if agent.compliance_status.value == 'reviewing'
        )
        
        # Data collection
        data_collection_completed = len(all_evidences) + len(all_reports)
        
        # Data collection progress
        data_progress = self._calculate_data_collection_progress(
            all_use_cases, all_evidences, all_reports
        )
        
        # Risk scoring
        risk_scoring = self._calculate_risk_scoring(all_use_cases, all_agents)
        
        # Reporting progress
        reporting_progress = self._calculate_reporting_progress(all_use_cases)
        
        # Framework progress
        frameworks_data = self._calculate_framework_progress(all_use_cases)
        
        return DashboardDTO(
            total_use_cases=total_use_cases,
            assessed_use_cases=assessed_use_cases,
            under_reviewed=under_reviewed,
            data_collection_completed=data_collection_completed,
            data_collection_progress=data_progress,
            risk_scoring=risk_scoring,
            reporting_progress=reporting_progress,
            frameworks_data=frameworks_data,
        )
    
    def _calculate_data_collection_progress(
        self, use_cases: list, evidences: list, reports: list
    ) -> DataCollectionProgressDTO:
        """Calculate data collection progress"""
        completed = 0
        in_progress = 0
        not_started = 0
        
        for use_case in use_cases:
            has_evidences = any(
                e.get('use_case_id') == use_case.id for e in evidences
            )
            has_reports = any(
                r.get('use_case_id') == use_case.id for r in reports
            )
            
            if (use_case.has_models and use_case.has_datasets and 
                has_evidences and has_reports and use_case.compliance_assessed):
                completed += 1
            elif (use_case.has_models or use_case.has_datasets or 
                  has_evidences or has_reports):
                in_progress += 1
            else:
                not_started += 1
        
        total = completed + in_progress + not_started
        if total > 0:
            completed_pct = round((completed / total) * 100)
            in_progress_pct = round((in_progress / total) * 100)
            not_started_pct = round((not_started / total) * 100)
        else:
            completed_pct = in_progress_pct = not_started_pct = 0
        
        return DataCollectionProgressDTO(
            completed=completed,
            in_progress=in_progress,
            not_started=not_started,
            completed_pct=completed_pct,
            in_progress_pct=in_progress_pct,
            not_started_pct=not_started_pct,
        )
    
    def _calculate_risk_scoring(self, use_cases: list, agents: list) -> RiskScoringDTO:
        """Calculate risk scoring"""
        # AI Risks
        ai_risks_map = {
            'high_risks': 4.0,
            'limited_risks': 2.5,
            'minimal_risks': 1.5
        }
        ai_risk_scores = [
            ai_risks_map.get(agent.risk_classification.value, 2.5)
            for agent in agents
        ]
        avg_ai_risk = (
            sum(ai_risk_scores) / len(ai_risk_scores) 
            if ai_risk_scores else 2.5
        )
        avg_ai_risk = max(1.0, min(4.0, avg_ai_risk))
        
        # Data Risks
        data_risk_scores = []
        for use_case in use_cases:
            compliance = self._compliance_service.calculate_compliance(use_case)
            if not compliance.gdpr:
                data_risk_scores.append(3.5)
            elif compliance.status.value == 'partial':
                data_risk_scores.append(2.5)
            else:
                data_risk_scores.append(1.5)
        avg_data_risk = (
            sum(data_risk_scores) / len(data_risk_scores)
            if data_risk_scores else 2.5
        )
        avg_data_risk = max(1.0, min(4.0, avg_data_risk))
        
        # Cyber Risks
        cyber_risk_scores = []
        for use_case in use_cases:
            compliance = self._compliance_service.calculate_compliance(use_case)
            if not compliance.data_act:
                cyber_risk_scores.append(3.0)
            else:
                cyber_risk_scores.append(2.0)
        avg_cyber_risk = (
            sum(cyber_risk_scores) / len(cyber_risk_scores)
            if cyber_risk_scores else 2.5
        )
        avg_cyber_risk = max(1.0, min(4.0, avg_cyber_risk))
        
        return RiskScoringDTO(
            ai_risk=round(avg_ai_risk, 1),
            data_risk=round(avg_data_risk, 1),
            cyber_risk=round(avg_cyber_risk, 1),
        )
    
    def _calculate_reporting_progress(self, use_cases: list) -> ReportingProgressDTO:
        """Calculate reporting progress"""
        completed = 0
        in_progress = 0
        not_started = 0
        deprioritized = 0
        
        for use_case in use_cases:
            compliance = self._compliance_service.calculate_compliance(use_case)
            if (compliance.status.value == 'compliant' and 
                use_case.compliance_assessed):
                completed += 1
            elif (compliance.status.value == 'partial' or 
                  (use_case.compliance_assessed and 
                   compliance.status.value != 'compliant')):
                in_progress += 1
            elif not use_case.compliance_assessed:
                not_started += 1
            else:
                deprioritized += 1
        
        total = completed + in_progress + not_started + deprioritized
        if total > 0:
            completed_pct = round((completed / total) * 100)
            in_progress_pct = round((in_progress / total) * 100)
            not_started_pct = round((not_started / total) * 100)
            deprioritized_pct = round((deprioritized / total) * 100)
        else:
            completed_pct = in_progress_pct = not_started_pct = deprioritized_pct = 0
        
        return ReportingProgressDTO(
            completed=completed,
            in_progress=in_progress,
            not_started=not_started,
            deprioritized=deprioritized,
            completed_pct=completed_pct,
            in_progress_pct=in_progress_pct,
            not_started_pct=not_started_pct,
            deprioritized_pct=deprioritized_pct,
        )
    
    def _calculate_framework_progress(self, use_cases: list) -> dict:
        """Calculate framework progress"""
        frameworks_data = {
            'GDPR': {'completed': 0, 'in_progress': 0, 'not_started': 0, 'deprioritized': 0},
            'EU_AI_Act': {'completed': 0, 'in_progress': 0, 'not_started': 0, 'deprioritized': 0},
            'DSA': {'completed': 0, 'in_progress': 0, 'not_started': 0, 'deprioritized': 0},
            'Data_Act': {'completed': 0, 'in_progress': 0, 'not_started': 0, 'deprioritized': 0},
        }
        
        for use_case in use_cases:
            compliance = self._compliance_service.calculate_compliance(use_case)
            
            # GDPR
            if compliance.gdpr and use_case.compliance_assessed:
                frameworks_data['GDPR']['completed'] += 1
            elif use_case.compliance_assessed:
                frameworks_data['GDPR']['in_progress'] += 1
            else:
                frameworks_data['GDPR']['not_started'] += 1
            
            # EU AI Act
            if compliance.eu_ai_act and use_case.compliance_assessed:
                frameworks_data['EU_AI_Act']['completed'] += 1
            elif use_case.compliance_assessed:
                frameworks_data['EU_AI_Act']['in_progress'] += 1
            else:
                frameworks_data['EU_AI_Act']['not_started'] += 1
            
            # Data Act
            if compliance.data_act and use_case.compliance_assessed:
                frameworks_data['Data_Act']['completed'] += 1
            elif use_case.compliance_assessed:
                frameworks_data['Data_Act']['in_progress'] += 1
            else:
                frameworks_data['Data_Act']['not_started'] += 1
            
            # DSA (placeholder)
            frameworks_data['DSA']['not_started'] += 1
        
        # Convert to DTOs
        return {
            key: FrameworkProgressDTO(**value)
            for key, value in frameworks_data.items()
        }
