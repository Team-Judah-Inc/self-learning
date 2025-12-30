package middleware

import (
	"context"
	"fmt"
	"net/http"

	"github.com/self-learning/backend/internal/auth"
)

// BasicAuth validates HTTP Basic Authentication credentials
func BasicAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		username, password, ok := r.BasicAuth()
		fmt.Println("MiddleBasicAuth")

		if ok {
			// Use the auth package to validate credentials
			user, valid := auth.ValidateCredentials(username, password)
			if valid {
				fmt.Printf("User successfully authenticated: %s\n", user.Username)

				// Add user to context for use in handlers
				ctx := context.WithValue(r.Context(), UserContextKey, user)
				next.ServeHTTP(w, r.WithContext(ctx))
			} else {
				fmt.Printf("User authentication failed for: %s\n", username)
				w.Header().Set("WWW-Authenticate", `Basic realm="Restricted"`)
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
			}
		} else {
			fmt.Println("No basic auth credentials provided")
			w.Header().Set("WWW-Authenticate", `Basic realm="Restricted"`)
			http.Error(w, "Authorization required", http.StatusUnauthorized)
		}
	})
}
