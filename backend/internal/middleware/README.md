# Middleware Package

This package contains all HTTP middleware for the application.

## Structure

```
middleware/
├── auth.go      # Authentication middleware (Basic Auth)
├── context.go   # Context helpers for user data
├── cors.go      # CORS headers middleware
└── recovery.go  # Panic recovery middleware
```

## Usage

### In server.go

```go
import "github.com/self-learning/backend/internal/middleware"

// Global middleware
router.Use(middleware.CORS)
router.Use(middleware.Recovery)

// Protected routes
api := router.PathPrefix("/api/v1").Subrouter()
api.Use(middleware.BasicAuth)
```

### In handlers

```go
import "github.com/self-learning/backend/internal/middleware"

func (h *Handler) SomeHandler(w http.ResponseWriter, r *http.Request) {
    // Get authenticated user from context
    user, ok := middleware.GetUserFromContext(r.Context())
    if !ok {
        http.Error(w, "Unauthorized", http.StatusUnauthorized)
        return
    }
    
    // Or use the helper
    user, ok := middleware.RequireAuth(w, r)
    if !ok {
        return // RequireAuth already sent error response
    }
    
    // Use user...
}
```

## Available Middleware

### CORS
Handles Cross-Origin Resource Sharing headers.

### Recovery
Recovers from panics and returns a 500 Internal Server Error.

### BasicAuth
Validates HTTP Basic Authentication credentials and adds the authenticated user to the request context.

## Context Helpers

- `GetUserFromContext(ctx)` - Extracts user from context
- `RequireAuth(w, r)` - Helper that gets user and sends error if not authenticated