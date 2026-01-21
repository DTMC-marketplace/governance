"""
Agent Factory - Factory Pattern for creating Agent entities
"""
from typing import Dict, Any
from ..entities.agent import Agent, ComplianceStatus, AIActRole, RiskClassification
from ...application.exceptions.domain_exceptions import InvalidEntityException


class AgentFactory:
    """Factory for creating Agent entities"""
    
    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> Agent:
        """
        Create Agent entity from dictionary
        Factory Pattern: Encapsulates object creation logic
        """
        try:
            # Normalize compliance_status
            compliance_status = data.get('compliance_status', 'assessing')
            if compliance_status not in [s.value for s in ComplianceStatus]:
                compliance_status = 'assessing'  # Default to assessing if invalid
            
            # Normalize risk_classification
            risk_classification = data.get('risk_classification', 'limited_risks')
            if risk_classification not in [r.value for r in RiskClassification]:
                risk_classification = 'limited_risks'  # Default to limited_risks if invalid
            
            # Normalize ai_act_role
            ai_act_role = data.get('ai_act_role', 'deployer')
            if ai_act_role not in [r.value for r in AIActRole]:
                ai_act_role = 'deployer'  # Default to deployer if invalid
            
            return Agent(
                id=data.get('id'),
                name=data.get('name', ''),
                business_unit=data.get('business_unit'),
                compliance_status=ComplianceStatus(compliance_status),
                ai_act_role=AIActRole(ai_act_role),
                vendor=data.get('vendor'),
                risk_classification=RiskClassification(risk_classification),
                investment_type=data.get('investment_type'),
            )
        except (ValueError, KeyError) as e:
            raise InvalidEntityException(f"Invalid agent data: {str(e)}")
    
    @staticmethod
    def create(
        id: int,
        name: str,
        business_unit: str = None,
        compliance_status: str = 'assessing',
        ai_act_role: str = 'deployer',
        vendor: str = None,
        risk_classification: str = 'limited_risks',
        investment_type: str = None,
    ) -> Agent:
        """Create Agent with explicit parameters"""
        return Agent(
            id=id,
            name=name,
            business_unit=business_unit,
            compliance_status=ComplianceStatus(compliance_status),
            ai_act_role=AIActRole(ai_act_role),
            vendor=vendor,
            risk_classification=RiskClassification(risk_classification),
            investment_type=investment_type,
        )
