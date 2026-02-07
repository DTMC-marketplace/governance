# Governance Hackathon Standalone Project

Standalone governance project for hackathon demo. This project focuses on AI/backend functionalities without requiring database setup, login credentials, or security measures.

## Features

- ✅ AI functionalities (AI agents, chat, risk assessment)
- ✅ Backend logic (compliance calculation, risk scoring)
- ✅ Frontend templates and UI
- ✅ Mock data for demo
- ❌ No database (PostgreSQL)
- ❌ No authentication/login
- ❌ No security measures (CSRF, etc.)

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone or navigate to the governance directory:
```bash
cd governance
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the development server:

**Option 1: Using enhanced script (recommended - shows detailed logs):**
```bash
python run_server.py
```

**Option 2: Using standard Django command:**
```bash
python manage.py runserver
```

**Note:** If you see "port is already in use", stop the existing server first:
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

5. You should see output like:
```
[INFO] ============================================================
[INFO] 🚀 Starting Governance Hackathon Project Server
[INFO] ============================================================
[INFO] ✅ System checks passed
[INFO] 🌐 Starting development server...
[INFO] 📝 Server will be available at: http://127.0.0.1:8000/
```

6. Open your browser and navigate to:
```
http://localhost:8000/
```

## Project Structure

This project follows **Clean Architecture** principles with clear separation of concerns:

```
governance/
├── manage.py                    # Django management script
├── settings.py                  # Django settings (no DB, no auth)
├── urls.py                      # Root URL configuration
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md          # Clean Architecture + system diagrams
│   └── PROJECT.md               # Hackathon submission + project description
├── governance/                  # Main app
│   ├── __init__.py
│   ├── views.py                 # Legacy views (backward compatibility)
│   ├── urls.py                  # URL patterns
│   ├── constants.py             # VIRTUAL_AGENT constants
│   ├── mock_data.py             # Legacy mock data loader
│   │
│   ├── domain/                  # Domain Layer (Core Business Logic)
│   │   ├── entities/            # Domain entities (Agent, UseCase, Model, Dataset, Compliance)
│   │   ├── repositories/        # Repository interfaces (contracts)
│   │   └── services/            # Domain services (ComplianceService)
│   │
│   ├── application/             # Application Layer (Use Cases)
│   │   ├── use_cases/           # Use case implementations
│   │   ├── dtos/                # Data Transfer Objects
│   │   └── exceptions/          # Application exceptions
│   │
│   ├── infrastructure/          # Infrastructure Layer (Data Access)
│   │   └── repositories/        # Repository implementations (Mock repositories)
│   │
│   └── presentation/            # Presentation Layer (Views)
│       ├── views/               # Django views using Clean Architecture
│       └── dependency_injection.py  # DI container
│
├── templates/                   # HTML templates
│   └── governance/
│       └── pages/               # Page templates
├── static/                      # Static files (CSS, JS, images)
│   └── governance/
└── mock_data/                   # JSON mock data files
    ├── agents.json
    ├── use_cases.json
    ├── models.json
    ├── datasets.json
    ├── evidences.json
    ├── evaluation_reports.json
    └── review_comments.json
```

### Architecture Layers

1. **Domain Layer** (`governance/domain/`): Core business entities and logic
2. **Application Layer** (`governance/application/`): Use cases and orchestration
3. **Infrastructure Layer** (`governance/infrastructure/`): Data access implementations
4. **Presentation Layer** (`governance/presentation/`): Views and HTTP handling

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed documentation.

### Design Patterns

This project implements **7 essential design patterns** optimized for hackathon demo:

- ✅ **Repository Pattern** - Abstracts data access (works with mock JSON data)
- ✅ **Factory Pattern** - Encapsulates object creation with validation
- ✅ **Strategy Pattern** - Interchangeable algorithms (compliance frameworks)
- ✅ **Dependency Injection** - Inverts dependencies for loose coupling
- ✅ **Use Case Pattern** - Encapsulates application logic
- ✅ **DTO Pattern** - Transfers data between layers
- ✅ **Domain Service Pattern** - Cross-entity business logic

**Why these patterns?**
- Practical and useful for hackathon demo
- Not over-engineered - appropriate complexity
- Easy to understand and maintain
- Works perfectly with mock data (no database needed)
- Can easily scale to production with database later

See [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md) for detailed documentation on each pattern.

## Mock Data

The project uses JSON files in the `mock_data/` directory instead of a database. You can modify these files to change the demo data:

- `agents.json` - AI agents
- `use_cases.json` - AI use cases
- `models.json` - AI models
- `datasets.json` - AI datasets
- `evidences.json` - Evidence files
- `evaluation_reports.json` - Evaluation reports
- `review_comments.json` - Review comments

## Key Differences from Production Version

1. **No Database**: All data is loaded from JSON files
2. **No Authentication**: All views are accessible without login
3. **No Company Context**: URLs don't require `company_id`
4. **Simplified URLs**: Direct paths like `/dashboard/` instead of `/governance/<company_id>/`
5. **Mock Objects**: Uses simple Python objects instead of Django models

## API Endpoints

Most API endpoints return mock responses. The following endpoints are available:

- `GET /api/ai-systems/models-datasets/` - Get available models and datasets
- `GET /api/use-cases/<id>/evidences/` - Get evidences for a use case
- `GET /api/use-cases/<id>/evaluation-reports/` - Get evaluation reports
- `GET /api/use-cases/<id>/review-comments/` - Get review comments

POST/DELETE endpoints return mock success responses but don't actually modify data.

## Integration Notes

This standalone project is designed for hackathon demo purposes. For integration with the main project:

1. **Frontend Integration**: Jingxiao will provide guidance on how to integrate backend functionalities
2. **Gemini Hackathon Code**: Risk assessment code from Gemini Hackathon team will be integrated later
3. **GitHub Repository**: Code will be merged with the main hackathon repository

## Development

### Running Tests

Since this is a demo project, no tests are included. The focus is on demonstrating functionality.

### Adding New Mock Data

1. Edit the appropriate JSON file in `mock_data/`
2. Restart the development server
3. The new data will be loaded automatically

### Modifying Views

**New Architecture (Recommended)**:
- Views using Clean Architecture are in `governance/presentation/views/`
- They use use cases from `governance/application/use_cases/`
- Business logic is in domain services (`governance/domain/services/`)

**Legacy Views**:
- Old views are still in `governance/views.py` for backward compatibility
- They use mock data loaders from `governance/mock_data.py`

## Troubleshooting

### Static files not loading

Make sure `DEBUG = True` in `settings.py` and that static files are in the `static/governance/` directory.

### Template not found

Templates should be in `templates/governance/pages/`. Make sure the template path in views matches the file structure.

### Import errors

Make sure you're running from the `governance/` directory and that all dependencies are installed.

## License

This is a hackathon demo project. See the main project for licensing information.

## Contact

For questions about integration or functionality, contact the development team.
