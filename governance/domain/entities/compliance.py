"""
Compliance Domain Entity
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ComplianceStatus(Enum):
    """Compliance status"""
    NOT_STARTED = "not_started"
    PARTIAL = "partial"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"


@dataclass
class Compliance:
    """Compliance domain entity"""
    status: ComplianceStatus
    gdpr: bool = False
    eu_ai_act: bool = False
    data_act: bool = False
    dsa: bool = False
    models_count: int = 0
    datasets_count: int = 0
    
    @property
    def is_compliant(self) -> bool:
        """Check if fully compliant"""
        return self.status == ComplianceStatus.COMPLIANT
    
    @property
    def compliance_score(self) -> float:
        """Calculate compliance score (0-1)"""
        frameworks = [self.gdpr, self.eu_ai_act, self.data_act, self.dsa]
        if not frameworks:
            return 0.0
        return sum(frameworks) / len(frameworks)
