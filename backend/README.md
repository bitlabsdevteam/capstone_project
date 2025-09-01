# FastAPI Application

A robust FastAPI application built with best practices, featuring modular architecture, comprehensive error handling, and production-ready configurations.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Modular Architecture**: Clean separation of concerns with organized code structure
- **Database Integration**: SQLAlchemy ORM with PostgreSQL and SQLite support
- **Authentication & Security**: JWT tokens, password hashing, CORS, and rate limiting
- **Comprehensive Error Handling**: Custom exceptions with proper HTTP status codes
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Structured Logging**: JSON and text logging with configurable levels
- **Data Validation**: Pydantic models for request/response validation
- **Health Checks**: Basic and detailed health monitoring endpoints
- **Rate Limiting**: Built-in request rate limiting middleware
- **Development Tools**: Hot reload, debugging support, and testing utilities

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py              # Main API router
│   │       └── endpoints/
│   │           ├── health.py       # Health check endpoints
│   │           ├── users.py        # User CRUD endpoints
│   │           └── items.py        # Item CRUD endpoints
│   ├── core/
│   │   ├── config.py              # Application configuration
│   │   ├── exceptions.py          # Custom exception classes
│   │   └── logging.py             # Logging configuration
│   ├── db/
│   │   └── session.py             # Database session management
│   ├── middleware/
│   │   └── rate_limit.py          # Rate limiting middleware
│   ├── models/
│   │   ├── user.py                # User database model
│   │   └── item.py                # Item database model
│   ├── schemas/
│   │   ├── health.py              # Health check schemas
│   │   ├── user.py                # User Pydantic schemas
│   │   └── item.py                # Item Pydantic schemas
│   └── services/
│       ├── user_service.py        # User business logic
│       └── item_service.py        # Item business logic
├── main.py                        # FastAPI application entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- pip or poetry for dependency management
- PostgreSQL (optional, SQLite used as fallback)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Run the application**
   ```bash
   python main.py
   # Or using uvicorn directly:
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Using Docker

```bash
# Build the image
docker build -t fastapi-app .

# Run the container
docker run -p 8000:8000 fastapi-app
```

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Available Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /api/v1/health/` - Basic API health check
- `GET /api/v1/health/detailed` - Detailed health check with system info

### Users
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/` - List users (with pagination and search)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `GET /api/v1/users/{user_id}/profile` - Get user profile

### Items
- `POST /api/v1/items/` - Create item
- `GET /api/v1/items/` - List items (with pagination and filtering)
- `GET /api/v1/items/{item_id}` - Get item by ID
- `PUT /api/v1/items/{item_id}` - Update item
- `DELETE /api/v1/items/{item_id}` - Delete item
- `GET /api/v1/items/categories/` - Get available categories
- `PATCH /api/v1/items/{item_id}/toggle-active` - Toggle item status

## Configuration

The application uses environment variables for configuration. Key settings include:

- **Database**: Configure PostgreSQL or use SQLite fallback
- **Security**: Set SECRET_KEY and token expiration times
- **CORS**: Configure allowed origins for cross-origin requests
- **Rate Limiting**: Set request limits and time windows
- **Logging**: Choose log level and format (JSON/text)

See `.env.example` for all available configuration options.

## Database

### PostgreSQL Setup

1. Install PostgreSQL
2. Create a database
3. Set database connection in `.env`:
   ```
   POSTGRES_SERVER=localhost
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=your_database
   ```

### SQLite (Default)

If PostgreSQL is not configured, the application will use SQLite:
```
SQLITE_URL=sqlite:///./app.db
```

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# With debug logging
LOG_LEVEL=DEBUG uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Code Quality

The project includes development dependencies for code quality:

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app
```

## Security Features

- **CORS**: Configurable cross-origin resource sharing
- **Rate Limiting**: Request rate limiting with customizable limits
- **Input Validation**: Pydantic models for request validation
- **Password Hashing**: Bcrypt for secure password storage
- **JWT Tokens**: JSON Web Tokens for authentication
- **Trusted Hosts**: Host header validation

## Monitoring

- **Health Checks**: Multiple health check endpoints
- **Structured Logging**: JSON logging for better log analysis
- **Request Timing**: Process time headers on responses
- **Rate Limit Headers**: Rate limiting information in response headers

## Production Deployment

### Environment Variables

Ensure these are set in production:
- `SECRET_KEY`: Strong secret key for JWT tokens
- `DEBUG=false`: Disable debug mode
- `DATABASE_URL`: Production database connection
- `BACKEND_CORS_ORIGINS`: Allowed origins for your frontend

### Recommended Setup

1. Use a reverse proxy (nginx)
2. Set up SSL/TLS certificates
3. Configure database connection pooling
4. Set up log aggregation
5. Monitor health check endpoints
6. Configure rate limiting based on your needs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run code quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License.