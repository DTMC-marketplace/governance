# Clean Architecture Documentation

## Overview

This project has been restructured following **Clean Architecture** principles and international design patterns. The architecture separates concerns into distinct layers, making the codebase more maintainable, testable, and scalable.

## Architecture Layers

### 1. Domain Layer (`governance/domain/`)

**Purpose**: Contains core business logic and entities. This layer has no dependencies on external frameworks.

#### Structure:
```
domain/
├── entities/          # Domain entities (Agent, UseCase, Model, Dataset, Compliance)
├── repositories/      # Repository interfaces (contracts)
└── services/         # Domain services (business logic that spans multiple entities)
```

**Key Principles**:
- Pure business logic
- No framework dependencies
- Entities are rich domain objects with business rules
- Repository interfaces define contracts (not implementations)

**Example Entities**:
- `Agent`: Represents an AI agent with compliance status, risk classification
- `UseCase`: Represents an AI use case with models, datasets, compliance assessment
- `Compliance`: Represents compliance status across multiple frameworks (GDPR, EU AI Act, Data Act)

### 2. Application Layer (`governance/application/`)

**Purpose**: Orchestrates domain objects to fulfill use cases. Contains application-specific business logic.

#### Structure:
```
application/
├── use_cases/        # Use case implementations (GetDashboardDataUseCase, etc.)
├── dtos/            # Data Transfer Objects
└── exceptions/      # Application exceptions
```

**Key Principles**:
- Each use case represents a single user action
- Use cases coordinate between repositories and domain services
- DTOs transfer data between layers
- No direct database access

**Example Use Cases**:
- `GetDashboardDataUseCase`: Orchestrates dashboard statistics calculation

### 3. Infrastructure Layer (`governance/infrastructure/`)

**Purpose**: Implements technical details - data access, external services, file I/O.

#### Structure:
```
infrastructure/
└── repositories/    # Concrete repository implementations (MockAgentRepository, etc.)
```

**Key Principles**:
- Implements repository interfaces from domain layer
- Handles data persistence (currently mock JSON files)
- Can be swapped without changing domain/application layers

**Example Repositories**:
- `MockAgentRepository`: Loads agents from JSON files
- `MockUseCaseRepository`: Loads use cases from JSON files

### 4. Presentation Layer (`governance/presentation/`)

**Purpose**: Handles user interface, HTTP requests/responses, input validation.

#### Structure:
```
presentation/
├── views/           # Django views (controllers)
└── dependency_injection.py  # Dependency injection container
```

**Key Principles**:
- Thin layer that delegates to use cases
- Handles HTTP concerns (request/response)
- Uses dependency injection for loose coupling

## Design Patterns Used

This project implements **7 essential design patterns** optimized for a hackathon demo:

### Core Patterns

1. **Repository Pattern** - Abstracts data access (works with mock data)
2. **Factory Pattern** - Encapsulates object creation with validation
3. **Strategy Pattern** - Interchangeable algorithms (compliance strategies)
4. **Dependency Injection** - Inverts dependencies for loose coupling
5. **Use Case Pattern** - Encapsulates application logic
6. **DTO Pattern** - Transfers data between layers
7. **Domain Service Pattern** - Cross-entity business logic

**Why these patterns?**
- ✅ Practical and useful for hackathon demo
- ✅ Not over-engineered
- ✅ Easy to understand and maintain
- ✅ Appropriate for mock data (no database)
- ✅ Can easily scale to production later

See [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md) for detailed documentation on each pattern.

## Dependency Flow

```
Presentation → Application → Domain
     ↓              ↓
Infrastructure ←────┘
```

**Rules**:
- Inner layers (Domain) don't know about outer layers
- Dependencies point inward
- Outer layers depend on inner layers

## Benefits of This Architecture

1. **Testability**: Each layer can be tested independently
2. **Maintainability**: Clear separation of concerns
3. **Scalability**: Easy to add new features without breaking existing code
4. **Flexibility**: Can swap implementations (e.g., mock → database) without changing business logic
5. **Team Collaboration**: Different teams can work on different layers

## Migration Path

The old code structure is still present for backward compatibility. New features should use the Clean Architecture structure:

- ✅ **New**: Use `presentation/views/` for new views
- ✅ **New**: Use `application/use_cases/` for business logic
- ✅ **New**: Use `domain/entities/` for domain models
- ✅ **New**: Use `infrastructure/repositories/` for data access

## Example: Adding a New Feature

1. **Define Domain Entity** (`domain/entities/new_entity.py`)
2. **Create Repository Interface** (`domain/repositories/new_repository.py`)
3. **Implement Repository** (`infrastructure/repositories/mock_new_repository.py`)
4. **Create Use Case** (`application/use_cases/new_use_case.py`)
5. **Create View** (`presentation/views/new_view.py`)
6. **Wire Dependencies** (`presentation/dependency_injection.py`)

## Testing Strategy

Each layer can be tested independently:

- **Domain**: Unit tests for entities and domain services
- **Application**: Unit tests for use cases (mock repositories)
- **Infrastructure**: Integration tests for repositories
- **Presentation**: Integration tests for views

## Future Enhancements

1. Add database repositories (replace mock repositories)
2. Add API layer (REST/GraphQL)
3. Add caching layer
4. Add event-driven architecture
5. Add comprehensive test suite
