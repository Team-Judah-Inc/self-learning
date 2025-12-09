# Self-Learning Frontend

A full-stack application for self-learning with a Go backend and modern frontend.

## Project Structure

```
self-learning/
├── backend/          # Go backend service
│   ├── cmd/         # Application entrypoints
│   ├── internal/    # Private application code
│   ├── pkg/         # Public libraries
│   └── api/         # API definitions
├── frontend/        # Frontend client application
│   ├── src/         # Source files
│   ├── public/      # Static assets
│   └── dist/        # Build output
└── docs/            # Documentation
```

## Getting Started

### Backend (Go)

```bash
cd backend
go mod download
go run cmd/server/main.go
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Prerequisites

- Go 1.21 or higher
- Node.js 18 or higher
- npm or yarn

## Development

### Backend Development

The backend is built with Go and follows a clean architecture pattern:
- `cmd/` - Application entry points
- `internal/` - Private application and business logic
- `pkg/` - Public reusable packages
- `api/` - API specifications and handlers

### Frontend Development

The frontend uses modern web technologies for a responsive user experience.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.