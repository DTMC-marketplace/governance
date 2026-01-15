"""
Compliance Strategy - Strategy Pattern for different compliance calculation algorithms
"""
from abc import ABC, abstractmethod
from typing import Dict
from ..entities.use_case import UseCase
from ..entities.compliance import Compliance, ComplianceStatus


class ComplianceStrategy(ABC):
    """Abstract base class for compliance strategies"""
    
    @abstractmethod
    def calculate(self, use_case: UseCase) -> Compliance:
        """Calculate compliance for a use case"""
        pass


class GDPRComplianceStrategy(ComplianceStrategy):
    """Strategy for GDPR compliance calculation"""
    
    def calculate(self, use_case: UseCase) -> Compliance:
        """Calculate GDPR compliance"""
        if not use_case.compliance_assessed:
            return Compliance(
                status=ComplianceStatus.NOT_STARTED,
                gdpr=False,
                models_count=len(use_case.models),
                datasets_count=len(use_case.datasets)
            )
        
        # GDPR requires models and datasets
        gdpr_compliant = use_case.has_models and use_case.has_datasets
        
        return Compliance(
            status=ComplianceStatus.COMPLIANT if gdpr_compliant else ComplianceStatus.PARTIAL,
            gdpr=gdpr_compliant,
            models_count=len(use_case.models),
            datasets_count=len(use_case.datasets)
        )


class EUAIActComplianceStrategy(ComplianceStrategy):
    """Strategy for EU AI Act compliance calculation"""
    
    def calculate(self, use_case: UseCase) -> Compliance:
        """Calculate EU AI Act compliance"""
        if not use_case.compliance_assessed:
            return Compliance(
                status=ComplianceStatus.NOT_STARTED,
                eu_ai_act=False,
                models_count=len(use_case.models),
                datasets_count=len(use_case.datasets)
            )
        
        # EU AI Act requires models, datasets, and review status
        eu_ai_act_compliant = (
            use_case.has_models and 
            use_case.has_datasets and 
            use_case.review_status.value in ['partial', 'complete']
        )
        
        return Compliance(
            status=ComplianceStatus.COMPLIANT if eu_ai_act_compliant else ComplianceStatus.PARTIAL,
            eu_ai_act=eu_ai_act_compliant,
            models_count=len(use_case.models),
            datasets_count=len(use_case.datasets)
        )


class DataActComplianceStrategy(ComplianceStrategy):
    """Strategy for Data Act compliance calculation"""
    
    def calculate(self, use_case: UseCase) -> Compliance:
        """Calculate Data Act compliance"""
        if not use_case.compliance_assessed:
            return Compliance(
                status=ComplianceStatus.NOT_STARTED,
                data_act=False,
                models_count=len(use_case.models),
                datasets_count=len(use_case.datasets)
            )
        
        # Data Act requires datasets
        data_act_compliant = use_case.has_datasets
        
        return Compliance(
            status=ComplianceStatus.COMPLIANT if data_act_compliant else ComplianceStatus.PARTIAL,
            data_act=data_act_compliant,
            models_count=len(use_case.models),
            datasets_count=len(use_case.datasets)
        )


class ComprehensiveComplianceStrategy(ComplianceStrategy):
    """Strategy that combines all compliance frameworks"""
    
    def __init__(self):
        self._strategies = {
            'gdpr': GDPRComplianceStrategy(),
            'eu_ai_act': EUAIActComplianceStrategy(),
            'data_act': DataActComplianceStrategy(),
        }
    
    def calculate(self, use_case: UseCase) -> Compliance:
        """Calculate comprehensive compliance across all frameworks"""
        results = {}
        for framework, strategy in self._strategies.items():
            compliance = strategy.calculate(use_case)
            results[framework] = compliance
        
        # Combine results
        gdpr = results['gdpr'].gdpr
        eu_ai_act = results['eu_ai_act'].eu_ai_act
        data_act = results['data_act'].data_act
        
        # Determine overall status
        if gdpr and eu_ai_act and data_act:
            status = ComplianceStatus.COMPLIANT
        elif gdpr or eu_ai_act or data_act:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.NOT_STARTED
        
        return Compliance(
            status=status,
            gdpr=gdpr,
            eu_ai_act=eu_ai_act,
            data_act=data_act,
            models_count=len(use_case.models),
            datasets_count=len(use_case.datasets)
        )
