package middleware

import (
	"context"
	"log"
	"net/http"

	"github.com/self-learning/backend/internal/auth"
)

// BasicAuth validates HTTP Basic Authentication credentials
func BasicAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		username, password, ok := r.BasicAuth()

		if !ok {
			log.Println("BasicAuth: No credentials provided")
			respondUnauthorized(w, "Authorization required")
			return
		}

		// Validate credentials
		user, valid := auth.ValidateCredentials(username, password)
		if !valid {
			log.Printf("BasicAuth: Authentication failed for user: %s\n", username)
			respondUnauthorized(w, "Invalid credentials")
			return
		}

		log.Printf("BasicAuth: User authenticated: %s\n", user.Username)

		// Add user to context for use in handlers
		ctx := context.WithValue(r.Context(), UserContextKey, user)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}
