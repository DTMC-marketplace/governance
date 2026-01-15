"""
Compliance Service - Domain service for compliance calculations
Uses Strategy Pattern for different compliance calculation algorithms
"""
from typing import List
from ..entities.use_case import UseCase
from ..entities.compliance import Compliance, ComplianceStatus
from ..strategies.compliance_strategy import ComprehensiveComplianceStrategy


class ComplianceService:
    """Service for compliance calculations using Strategy Pattern"""
    
    def __init__(self, strategy=None):
        """
        Initialize with compliance strategy
        Defaults to ComprehensiveComplianceStrategy
        """
        self._strategy = strategy or ComprehensiveComplianceStrategy()
    
    def calculate_compliance(self, use_case: UseCase) -> Compliance:
        """
        Calculate compliance for a use case using Strategy Pattern
        This is domain logic that determines compliance status
        """
        return self._strategy.calculate(use_case)
    
    @staticmethod
    def calculate_risks(use_case: UseCase) -> List[str]:
        """
        Calculate risks for a use case
        Returns list of risk types
        """
        risks = []
        
        if use_case.risk_type:
            risks.append(use_case.risk_type)
        else:
            risks.append('limited_risks')
        
        return risks
