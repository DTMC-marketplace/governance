"""
Agent Domain Entity
"""
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class ComplianceStatus(Enum):
    """Agent compliance status"""
    ASSESSING = "assessing"
    REVIEWING = "reviewing"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"


class AIActRole(Enum):
    """EU AI Act role"""
    PROVIDER = "provider"
    DEPLOYER = "deployer"
    IMPORTER = "importer"
    DISTRIBUTOR = "distributor"


class RiskClassification(Enum):
    """Risk classification"""
    HIGH_RISKS = "high_risks"
    LIMITED_RISKS = "limited_risks"
    MINIMAL_RISKS = "minimal_risks"
    PROHIBITED = "prohibited"


@dataclass
class Agent:
    """Agent domain entity"""
    id: int
    name: str
    business_unit: Optional[str] = None
    compliance_status: ComplianceStatus = ComplianceStatus.ASSESSING
    ai_act_role: AIActRole = AIActRole.DEPLOYER
    vendor: Optional[str] = None
    risk_classification: RiskClassification = RiskClassification.LIMITED_RISKS
    investment_type: Optional[str] = None
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if not self.name:
            raise ValueError("Agent name is required")
        if self.id <= 0:
            raise ValueError("Agent ID must be positive")
