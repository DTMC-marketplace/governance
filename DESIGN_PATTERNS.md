# Design Patterns Documentation

## Overview

This project implements **essential design patterns** following international best practices, optimized for a hackathon demo project. Patterns are kept simple and practical, focusing on maintainability and clarity.

## Implemented Design Patterns

### 1. Repository Pattern ✅

**Purpose**: Abstracts data access layer, making it easy to work with mock data.

**Location**:
- Interfaces: `domain/repositories/`
- Implementations: `infrastructure/repositories/`

**Why it's useful for hackathon**:
- Clean separation between business logic and data access
- Easy to swap mock data sources (JSON files)
- Makes code testable and maintainable
- Can easily migrate to database later

**Example**:
```python
# Interface
class IAgentRepository(ABC):
    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        pass

# Implementation (Mock)
class MockAgentRepository(IAgentRepository):
    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        # Load from JSON file
        pass
```

### 2. Factory Pattern ✅

**Purpose**: Encapsulates object creation logic, ensures valid entities.

**Location**: `domain/factories/`

**Why it's useful for hackathon**:
- Centralized validation during entity creation
- Prevents invalid data from entering the system
- Clean, readable code
- Easy to maintain

**Example**:
```python
# Factory
class AgentFactory:
    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> Agent:
        # Validate and create
        return Agent(...)

# Usage in repository
agent = AgentFactory.create_from_dict(data)
```

### 3. Strategy Pattern ✅

**Purpose**: Different algorithms for compliance calculation (GDPR, EU AI Act, Data Act).

**Location**: `domain/strategies/`

**Why it's useful for hackathon**:
- Easy to add new compliance frameworks
- Clear separation of compliance rules
- Algorithms can be tested independently
- Business logic is organized and maintainable

**Example**:
```python
# Strategy interface
class ComplianceStrategy(ABC):
    def calculate(self, use_case: UseCase) -> Compliance:
        pass

# Concrete strategies
class GDPRComplianceStrategy(ComplianceStrategy): ...
class EUAIActComplianceStrategy(ComplianceStrategy): ...

# Usage
strategy = ComprehensiveComplianceStrategy()
compliance = strategy.calculate(use_case)
```

### 4. Dependency Injection ✅

**Purpose**: Inverts dependencies, enables loose coupling and testing.

**Location**: `presentation/dependency_injection.py`

**Why it's useful for hackathon**:
- Clean separation of concerns
- Easy to test with mock dependencies
- Centralized dependency management
- Makes code more maintainable

**Example**:
```python
class DependencyContainer:
    def __init__(self, base_dir: Path):
        self._agent_repository = MockAgentRepository(data_dir)
        self._use_case_repository = MockUseCaseRepository(data_dir)
```

### 5. Use Case Pattern ✅

**Purpose**: Encapsulates application-specific business logic.

**Location**: `application/use_cases/`

**Why it's useful for hackathon**:
- Each use case represents a single user action
- Clear business operations
- Easy to understand and maintain
- Testable business logic

**Example**:
```python
class GetDashboardDataUseCase:
    def __init__(self, repositories...):
        self._repositories = repositories
    
    def execute(self) -> DashboardDTO:
        # Orchestrate business logic
        pass
```

### 6. DTO Pattern ✅

**Purpose**: Transfers data between layers without exposing domain entities.

**Location**: `application/dtos/`

**Why it's useful for hackathon**:
- Decouples layers
- Clear data contracts
- Prevents domain logic leakage to presentation
- Makes API responses predictable

**Example**:
```python
@dataclass
class DashboardDTO:
    total_use_cases: int
    assessed_use_cases: int
    # ...
```

### 7. Domain Service Pattern ✅

**Purpose**: Business logic that doesn't belong to a single entity.

**Location**: `domain/services/`

**Why it's useful for hackathon**:
- Encapsulates cross-entity logic (compliance calculation)
- Reusable business rules
- Clear domain boundaries
- Organized business logic

**Example**:
```python
class ComplianceService:
    def calculate_compliance(self, use_case: UseCase) -> Compliance:
        # Business logic spanning multiple entities
        pass
```

## Architecture Pattern

### Clean Architecture ✅

**Purpose**: Separates concerns into distinct layers with dependency rules.

**Layers**:
1. **Domain**: Core business logic (innermost) - Entities, Services, Strategies, Factories
2. **Application**: Use cases and orchestration - Use Cases, DTOs
3. **Infrastructure**: Technical implementations - Repositories (Mock)
4. **Presentation**: UI and HTTP handling - Views, Dependency Injection

**Why it's useful for hackathon**:
- Clear separation of concerns
- Easy to understand code structure
- Maintainable and testable
- Can easily add database later without changing business logic

**Dependency Rule**: Dependencies point inward. Inner layers don't know about outer layers.

## Pattern Relationships

```
Presentation Layer (Views)
    ↓ uses
Application Layer (Use Cases, DTOs)
    ↓ uses
Domain Layer (Entities, Services, Strategies, Factories)
    ↑ implements
Infrastructure Layer (Repositories - Mock)
```

## Why These Patterns (Not Others)?

### ✅ Included Patterns
- **Repository**: Essential for clean data access, even with mock data
- **Factory**: Ensures valid entity creation
- **Strategy**: Perfect for different compliance frameworks
- **Dependency Injection**: Essential for testability and loose coupling
- **Use Case**: Clear business operations
- **DTO**: Clean layer separation
- **Domain Service**: Cross-entity business logic

### ❌ Excluded Patterns (Not needed for hackathon)
- **Query Pattern (CQRS)**: Not needed without database, adds unnecessary complexity
- **Command Pattern**: Overkill for simple CRUD operations with mock data
- **Builder Pattern**: Can use simple constructors for DTOs
- **Observer Pattern**: No event-driven requirements
- **Adapter Pattern**: No external service integration needed

## Best Practices for Hackathon

1. **Keep it simple**: Use patterns that solve real problems, not theoretical ones
2. **Focus on clarity**: Code should be easy to understand for judges
3. **Maintainability**: Structure should be clear and organized
4. **Testability**: Patterns should make testing easier
5. **Future-proof**: Easy to add database/features later

## When to Use Each Pattern

### Repository Pattern
- ✅ When working with data (even mock data)
- ✅ When you want clean separation of data access
- ✅ When you might add database later

### Factory Pattern
- ✅ When creating entities from external data (JSON)
- ✅ When you need validation during creation
- ✅ When you want centralized creation logic

### Strategy Pattern
- ✅ When you have multiple algorithms (compliance frameworks)
- ✅ When algorithms should be interchangeable
- ✅ When you want to add new algorithms easily

### Dependency Injection
- ✅ Always - for loose coupling and testing
- ✅ When you have dependencies between components

### Use Case Pattern
- ✅ For all business operations
- ✅ When you want clear business logic organization

### DTO Pattern
- ✅ When transferring data between layers
- ✅ When you want to decouple layers

### Domain Service Pattern
- ✅ When business logic spans multiple entities
- ✅ When logic doesn't belong to a single entity

## Code Examples

### Creating an Agent (Factory + Repository)
```python
# In repository
agent = AgentFactory.create_from_dict(data)
return agent
```

### Calculating Compliance (Strategy)
```python
# In service
strategy = ComprehensiveComplianceStrategy()
compliance = strategy.calculate(use_case)
```

### Getting Dashboard Data (Use Case)
```python
# In view
use_case = container.get_dashboard_data_use_case
dashboard_dto = use_case.execute()
```

## Summary

This project uses **7 essential design patterns** that are:
- ✅ Practical and useful
- ✅ Not over-engineered
- ✅ Easy to understand
- ✅ Maintainable
- ✅ Testable
- ✅ Appropriate for hackathon demo

The architecture follows **Clean Architecture** principles with clear layer separation, making it professional and maintainable while keeping complexity appropriate for a hackathon project.
