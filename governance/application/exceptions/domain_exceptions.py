"""
Domain Exceptions
"""


class DomainException(Exception):
    """Base domain exception"""
    pass


class EntityNotFoundException(DomainException):
    """Raised when an entity is not found"""
    def __init__(self, entity_type: str, entity_id: int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID {entity_id} not found")


class InvalidEntityException(DomainException):
    """Raised when entity data is invalid"""
    pass
