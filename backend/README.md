# Self-Learning Backend

Go backend service for the self-learning application.

## Project Structure

```
self-learning/backend/
├── cmd/
│   └── server/
│       └── main.go              # Application entry point
├── internal/                    # Private application code
│   ├── config/
│   │   └── config.go           # Configuration management
│   ├── server/
│   │   ├── server.go           # Server setup and routing
│   │   └── middleware.go       # Middleware functions
│   ├── handlers/               # HTTP handlers (controllers)
│   │   ├── health.go
│   │   ├── auth.go
│   │   └── user.go
│   ├── services/               # Business logic layer
│   │   ├── auth_service.go
│   │   └── user_service.go
│   ├── repository/             # Data access layer
│   │   ├── interfaces.go
│   │   ├── user_repo.go
│   │   └── memory/
│   │       └── user_memory.go
│   ├── models/                 # Domain models/entities
│   │   ├── user.go
│   │   ├── auth.go
│   │   └── response.go
│   └── auth/                   # Authentication logic
│       ├── auth.go
│       └── middleware.go
├── pkg/                        # Public libraries
│   ├── logger/
│   │   └── logger.go
│   ├── validator/
│   │   └── validator.go
│   └── errors/
│       └── errors.go
├── api/                        # API documentation
│   └── openapi.yaml
├── migrations/                 # Database migrations
├── scripts/                    # Build and deployment scripts
├── docker/                     # Docker files
│   └── Dockerfile
├── go.mod
├── go.sum
└── README.md

```

## Getting Started

### Prerequisites

- Go 1.21 or higher

### Installation

1. Clone the repository and navigate to the backend directory:
```bash
cd backend
```

2. Copy the example environment file:
```bash
cp .env.example .env
```

3. Install dependencies:
```bash
go mod download
```

### Running the Server

Development mode:
```bash
go run cmd/server/main.go
```

Build and run:
```bash
go build -o bin/server cmd/server/main.go
./bin/server
```

### Environment Variables

See `.env.example` for all available configuration options:

- `PORT` - Server port (default: 8080)
- `ENVIRONMENT` - Environment mode (development/production)
- `ALLOWED_ORIGINS` - CORS allowed origins
- `DATABASE_URL` - Database connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `LOG_LEVEL` - Logging level (debug/info/error)

## API Endpoints

### Health Check
```
GET /health
```

### API Root
```
GET /api/v1/
```

## Development

### Code Organization

- `cmd/` - Application entry points
- `internal/` - Private application code (not importable by other projects)
- `pkg/` - Public libraries (can be imported by other projects)
- `api/` - API specifications and documentation

### Adding New Features

1. Create handlers in `internal/handlers/`
2. Add routes in `cmd/server/main.go`
3. Update API documentation in `api/`

## Testing

Run tests:
```bash
go test ./...
```

Run tests with coverage:
```bash
go test -cover ./...
```

## Building for Production

```bash
CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o bin/server cmd/server/main.go
```

## License

MIT