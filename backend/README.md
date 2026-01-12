# Self-Learning Backend

Go backend service for the Self-Learning application.

A clean, modular HTTP server with authentication, middleware, and structured logging.

## Project Structure

```text
backend/
├── cmd/
│   └── server/
│       └── main.go          # Application entrypoint
├── internal/
│   ├── auth/                # Authentication logic
│   │   ├── basic_auth.go    # Basic auth validation
│   │   └── jwt.go           # JWT token handling
│   │
│   ├── config/              # Configuration management
│   │   └── config.go        # Environment-based config
│   │
│   ├── handlers/            # HTTP request handlers
│   │   ├── handlers.go      # Main handlers
│   │   ├── auth.go          # Auth endpoints
│   │   └── health.go        # Health check endpoint
│   │
│   ├── middleware/          # HTTP middleware
│   │   ├── auth.go          # Authentication middleware
│   │   ├── context.go       # Context utilities
│   │   ├── cors.go          # CORS configuration
│   │   └── recovery.go      # Panic recovery
│   │
│   ├── models/              # Data models
│   │   ├── auth.go          # Auth-related models
│   │   ├── response.go      # API response structures
│   │   └── user.go          # User models
│   │
│   ├── server/              # HTTP server setup
│   │   └── server.go        # Server initialization & routing
│   │
│   └── services/            # Business logic layer
│       ├── services.go      # Service interfaces
│       └── auth_service.go  # Authentication service
│
├── pkg/
│   └── logger/              # Structured logging utilities
│       └── logger.go
├── go.mod                   # Go module dependencies
├── go.sum                   # Dependency checksums
└── .env.example             # Environment variables template
```

## Getting Started

### Prerequisites

* **Go 1.24** or higher

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
   go mod tidy
   ```

### Running the Server

Start the HTTP server on port `8080`:

```bash
go run cmd/server/main.go
```

The server will start with:
- Health check endpoint at `/health`
- CORS middleware configured
- Panic recovery middleware
- Request logging
- Basic authentication for protected routes

## Environment Variables

See `.env.example` for all available configuration options:

* `PORT` – Server port (default: `8080`)
* `ENVIRONMENT` – Environment mode (`development` / `production`)
* `ALLOWED_ORIGINS` – CORS allowed origins (comma-separated)
* `JWT_SECRET` – Secret key for JWT token signing
* `LOG_LEVEL` – Logging level (`debug` / `info` / `warn` / `error`)

## Features

* **Clean Architecture** – Separation of concerns with handlers, services, and middleware
* **Authentication** – Basic auth and JWT token support
* **Middleware Stack** – CORS, recovery, logging, and authentication
* **Structured Logging** – JSON-formatted logs with configurable levels
* **Health Checks** – Built-in health endpoint for monitoring
* **Environment-based Config** – Flexible configuration via environment variables

## API Endpoints

* `GET /health` – Health check endpoint (public)
* Protected routes require Basic Authentication with credentials from `internal/auth/basic_auth.go`

## Development

The project follows Go best practices:
- Clean separation between handlers, services, and middleware
- Dependency injection for testability
- Structured error handling
- Context-based request scoping

## License

MIT
