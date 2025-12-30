package middleware

import (
	"context"
	"net/http"

	"github.com/self-learning/backend/internal/auth"
)

type contextKey string

const UserContextKey contextKey = "user"

// GetUserFromContext extracts authenticated user from request context
func GetUserFromContext(ctx context.Context) (*auth.User, bool) {
	user, ok := ctx.Value(UserContextKey).(*auth.User)
	return user, ok
}

// RequireAuth helper function for handlers to get authenticated user
func RequireAuth(w http.ResponseWriter, r *http.Request) (*auth.User, bool) {
	user, ok := GetUserFromContext(r.Context())
	if !ok {
		http.Error(w, "Authentication required", http.StatusUnauthorized)
		return nil, false
	}
	return user, true
}