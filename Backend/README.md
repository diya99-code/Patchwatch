# PatchWatch Backend

A comprehensive dependency monitoring and vulnerability detection system built with FastAPI, PostgreSQL, and Celery.

## Features

- **Multi-ecosystem Support**: JavaScript/npm and Python/PyPI packages
- **Vulnerability Detection**: Real-time security scanning using OSV.dev API
- **User Authentication**: JWT-based authentication with secure password hashing
- **Project Management**: Organize scans by projects with proper access control
- **Background Processing**: Asynchronous scan processing using Celery and Redis
- **Risk Analysis**: Intelligent update recommendations with priority classification
- **RESTful API**: Comprehensive API with OpenAPI documentation
- **Database Persistence**: PostgreSQL with proper migrations and relationships

## Technology Stack

- **Backend Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Authentication**: JWT with bcrypt password hashing
- **Background Jobs**: Celery with Redis
- **HTTP Client**: httpx for external API calls
- **Testing**: pytest with comprehensive test coverage
- **Containerization**: Docker and Docker Compose

## Project Structure

```
Backend/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── deps.py            # Authentication dependencies
│   │   └── v1/                # API version 1
│   │       ├── auth.py        # Authentication endpoints
│   │       ├── projects.py    # Project management
│   │       ├── scans.py       # Scan operations
│   │       └── dependencies.py # Dependency analysis
│   ├── core/                  # Core configuration
│   │   ├── config.py          # Settings management
│   │   ├── security.py        # JWT and password utilities
│   │   └── exceptions.py      # Custom exceptions
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # Business logic
│   │   ├── parser.py          # Dependency file parsing
│   │   └── vuln_checker.py    # Vulnerability detection
│   ├── integrations/          # External API clients
│   │   ├── npm_client.py      # npm registry client
│   │   ├── pypi_client.py     # PyPI API client
│   │   └── osv_client.py      # OSV vulnerability API
│   ├── workers/               # Celery background tasks
│   │   ├── celery_app.py      # Celery configuration
│   │   └── scan_tasks.py      # Scan processing tasks
│   ├── database.py            # Database session management
│   └── main.py                # FastAPI application
├── alembic/                   # Database migrations
├── tests/                     # Test suite
├── docker-compose.yml         # Multi-service setup
├── Dockerfile                 # Application container
├── requirements.txt           # Python dependencies
└── .env.example               # Environment template
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (recommended)

### Option 1: Docker Compose (Recommended)

1. **Clone and navigate to the backend directory**:
   ```bash
   cd Backend
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **The API will be available at**:
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Option 2: Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL database**:
   ```sql
   CREATE DATABASE patchwatch;
   CREATE USER patchwatch WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE patchwatch TO patchwatch;
   ```

3. **Set up Redis** (follow Redis installation guide for your OS)

4. **Create and configure `.env` file**:
   ```bash
   cp .env.example .env
   # Edit database and Redis URLs
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Start Celery worker** (in a separate terminal):
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

## API Usage

### Authentication

1. **Register a new user**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "SecurePass123!",
       "full_name": "John Doe"
     }'
   ```

2. **Login to get access token**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "SecurePass123!"
     }'
   ```

3. **Use the token in subsequent requests**:
   ```bash
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     "http://localhost:8000/api/v1/auth/me"
   ```

### Project Management

1. **Create a project**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/projects/" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "My Web App",
       "description": "A sample web application",
       "repository_url": "https://github.com/user/webapp"
     }'
   ```

2. **List projects**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/v1/projects/"
   ```

### Dependency Scanning

1. **Upload and scan a package.json**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/projects/1/scans" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@package.json"
   ```

2. **Check scan status**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/v1/scans/1"
   ```

3. **Get detailed scan results**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/v1/scans/1/results"
   ```

### Dependency Analysis

1. **Get project dependencies**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/v1/projects/1/dependencies"
   ```

2. **Get vulnerabilities only**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/v1/projects/1/dependencies?vulnerable_only=true"
   ```

3. **Get project summary**:
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/api/v1/projects/1/summary"
   ```

## Supported File Types

### JavaScript/TypeScript
- **package.json**: Dependency declarations
- **package-lock.json**: Resolved versions (planned)

### Python
- **requirements.txt**: Pip dependency format
- **poetry.lock**: Poetry lockfile (planned)
- **Pipfile.lock**: Pipenv lockfile (planned)

## Environment Configuration

Key environment variables (see `.env.example` for complete list):

```env
# Database
DATABASE_URL=postgresql://patchwatch:password@localhost:5432/patchwatch

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# External APIs
OSV_API_URL=https://api.osv.dev/v1/query
NPM_REGISTRY_URL=https://registry.npmjs.org
PYPI_API_URL=https://pypi.org/pypi
```

## Database Schema

### Core Tables

- **users**: User accounts with authentication
- **projects**: User projects for organizing scans
- **scans**: Individual dependency scan records
- **dependencies**: Discovered package dependencies
- **vulnerabilities**: Security advisories from OSV.dev
- **recommendations**: Update suggestions with risk analysis

### Relationships

- Users own multiple Projects
- Projects have multiple Scans
- Scans contain multiple Dependencies
- Dependencies have multiple Vulnerabilities
- Dependencies have multiple Recommendations

## Testing

Run the complete test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py

# Run specific test class
pytest tests/test_api.py::TestAuthenticationEndpoints
```

### Test Categories

- **Unit Tests**: Individual function and class testing
- **Integration Tests**: API endpoint testing with database
- **Parser Tests**: Dependency file parsing validation
- **Security Tests**: Authentication and authorization

## Vulnerability Detection

### OSV.dev Integration

PatchWatch uses the Open Source Vulnerabilities (OSV) database:

- **Real-time scanning**: Direct API integration
- **Multi-ecosystem support**: npm, PyPI, and more
- **Comprehensive data**: CVE IDs, severity scores, fix versions
- **Rate limiting**: Respectful concurrent request handling

### Risk Analysis

Each dependency gets analyzed for:

- **Security vulnerabilities**: Critical, High, Medium, Low severity
- **Outdated versions**: Comparison with latest releases
- **Update recommendations**: Prioritized by risk and impact
- **Breaking changes**: Major version update detection

## Security Considerations

### Authentication
- JWT tokens with configurable expiration
- bcrypt password hashing with salt
- Secure password complexity requirements

### Authorization
- User-based resource isolation
- Project ownership verification
- API endpoint protection

### Input Validation
- File size limits (10MB default)
- File type validation
- Safe JSON/text parsing
- SQL injection prevention

### External APIs
- Request timeouts and retries
- Rate limiting respect
- Error handling and fallbacks

## Performance

### Asynchronous Processing
- Background scan processing with Celery
- Non-blocking API responses
- Concurrent external API requests

### Database Optimization
- Proper indexing on lookup columns
- Foreign key constraints
- Connection pooling

### Caching Strategy
- Redis for Celery message broker
- Result caching for expensive operations
- Session management

## Monitoring and Observability

### Health Checks
- `/health`: Application health status
- Database connectivity verification
- Redis connectivity verification

### Logging
- Structured logging with timestamps
- Request/response logging
- Error tracking and reporting

### Metrics
- Scan processing times
- API response times
- Background job success/failure rates

## Deployment

### Production Checklist

1. **Security**:
   - Change default SECRET_KEY
   - Use strong database passwords
   - Configure CORS origins appropriately
   - Set up HTTPS/TLS

2. **Database**:
   - Use managed PostgreSQL service
   - Configure connection pooling
   - Set up automated backups
   - Monitor performance

3. **Caching**:
   - Use managed Redis service
   - Configure persistence
   - Monitor memory usage

4. **Scaling**:
   - Horizontal scaling with multiple workers
   - Load balancer configuration
   - Database read replicas if needed

5. **Monitoring**:
   - Application performance monitoring
   - Error tracking
   - Log aggregation
   - Uptime monitoring

### Docker Production

```bash
# Build production image
docker build -t patchwatch-backend:latest .

# Run with production configuration
docker run -d \
  --name patchwatch-backend \
  -p 8000:8000 \
  --env-file .env.production \
  patchwatch-backend:latest
```

## API Documentation

Complete API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/auth/me` - Current user info
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/projects/{id}/scans` - Start scan
- `GET /api/v1/scans/{id}` - Get scan status
- `GET /api/v1/scans/{id}/results` - Get scan results
- `GET /api/v1/projects/{id}/dependencies` - List dependencies
- `GET /api/v1/projects/{id}/vulnerabilities` - List vulnerabilities
- `GET /api/v1/projects/{id}/summary` - Project summary

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8

# Format code
black app/ tests/

# Check code style
flake8 app/ tests/

# Run tests
pytest
```

## Known Limitations

1. **Lockfile Support**: Currently supports manifest files (package.json, requirements.txt) but not lockfiles for precise version resolution
2. **Transitive Dependencies**: Limited detection of indirect/transitive dependencies
3. **Breaking Change Detection**: Basic heuristic based on semantic versioning
4. **Repository Integration**: No direct GitHub/GitLab repository scanning
5. **Additional Ecosystems**: Maven, Gradle, Go modules not yet supported

## Roadmap

### Short Term
- [ ] Package lockfile support (package-lock.json, poetry.lock)
- [ ] Improved transitive dependency detection  
- [ ] Email notifications for critical vulnerabilities
- [ ] Scan scheduling and automation

### Medium Term
- [ ] Additional package ecosystems (Maven, Go, Rust)
- [ ] GitHub/GitLab repository integration
- [ ] Custom vulnerability database sources
- [ ] Enhanced breaking change analysis

### Long Term
- [ ] Dependency update automation
- [ ] Supply chain risk analysis
- [ ] Compliance reporting
- [ ] Integration with CI/CD pipelines

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For questions, issues, or contributions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs`
- Review the test suite for usage examples