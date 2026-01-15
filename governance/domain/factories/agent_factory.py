"""
Agent Factory - Factory Pattern for creating Agent entities
"""
from typing import Dict, Any
from ..entities.agent import Agent, ComplianceStatus, AIActRole, RiskClassification
from ..application.exceptions.domain_exceptions import InvalidEntityException


class AgentFactory:
    """Factory for creating Agent entities"""
    
    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> Agent:
        """
        Create Agent entity from dictionary
        Factory Pattern: Encapsulates object creation logic
        """
        try:
            return Agent(
                id=data.get('id'),
                name=data.get('name', ''),
                business_unit=data.get('business_unit'),
                compliance_status=ComplianceStatus(
                    data.get('compliance_status', 'assessing')
                ),
                ai_act_role=AIActRole(
                    data.get('ai_act_role', 'deployer')
                ),
                vendor=data.get('vendor'),
                risk_classification=RiskClassification(
                    data.get('risk_classification', 'limited_risks')
                ),
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
