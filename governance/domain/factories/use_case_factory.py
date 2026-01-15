"""
Use Case Factory - Factory Pattern for creating UseCase entities
"""
from typing import Dict, Any, List
from ..entities.use_case import UseCase, ReviewStatus
from ..application.exceptions.domain_exceptions import InvalidEntityException


class UseCaseFactory:
    """Factory for creating UseCase entities"""
    
    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> UseCase:
        """
        Create UseCase entity from dictionary
        Factory Pattern: Encapsulates object creation logic
        """
        try:
            return UseCase(
                id=data.get('id'),
                name=data.get('name', ''),
                display_name=data.get('display_name'),
                overview=data.get('overview'),
                risk_type=data.get('risk_type'),
                review_status=ReviewStatus(
                    data.get('review_status', 'missing')
                ),
                compliance_assessed=data.get('compliance_assessed', False),
                agent_id=data.get('agent_id'),
                models=data.get('models', []),
                datasets=data.get('datasets', []),
            )
        except (ValueError, KeyError) as e:
            raise InvalidEntityException(f"Invalid use case data: {str(e)}")
    
    @staticmethod
    def create(
        id: int,
        name: str,
        display_name: str = None,
        overview: str = None,
        risk_type: str = None,
        review_status: str = 'missing',
        compliance_assessed: bool = False,
        agent_id: int = None,
        models: List[int] = None,
        datasets: List[int] = None,
    ) -> UseCase:
        """Create UseCase with explicit parameters"""
        return UseCase(
            id=id,
            name=name,
            display_name=display_name,
            overview=overview,
            risk_type=risk_type,
            review_status=ReviewStatus(review_status),
            compliance_assessed=compliance_assessed,
            agent_id=agent_id,
            models=models or [],
            datasets=datasets or [],
        )
