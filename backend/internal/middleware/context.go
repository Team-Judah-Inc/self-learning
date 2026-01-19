package middleware

import (
	"context"
	"net/http"

	"github.com/self-learning/backend/internal/models"
)

type contextKey string

const UserContextKey contextKey = "user"

// GetUserFromContext extracts authenticated user from request context
func GetUserFromContext(ctx context.Context) (*models.User, bool) {
	// CHANGE: Cast to *models.User instead of *auth.AuthUser
	user, ok := ctx.Value(UserContextKey).(*models.User)
	return user, ok
}

// RequireAuth helper function for handlers to get authenticated user
func RequireAuth(w http.ResponseWriter, r *http.Request) (*models.User, bool) {
	user, ok := GetUserFromContext(r.Context())
	if !ok {
		respondUnauthorized(w, "Authentication required")
		return nil, false
	}
	return user, true
}