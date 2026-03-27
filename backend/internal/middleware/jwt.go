package middleware

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"strings"

	"github.com/MicahParks/keyfunc/v3"
	"github.com/golang-jwt/jwt/v5"
	"github.com/self-learning/backend/internal/models"
	"gorm.io/gorm"
)

// JWTAuth middleware validates the Supabase Bearer token using JWKS (ES256)
func JWTAuth(db *gorm.DB, supabaseURL string) func(http.Handler) http.Handler {

	// 1. Initialize JWKS (Key Fetcher)
	// This automatically downloads the public keys from Supabase
	jwksURL := fmt.Sprintf("%s/auth/v1/.well-known/jwks.json", supabaseURL)
	k, err := keyfunc.NewDefault([]string{jwksURL})
	if err != nil {
		log.Fatalf("Failed to create JWKS from resource at %s.\nError: %s", jwksURL, err)
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {

			// 2. Extract Token
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				respondUnauthorized(w, "Missing Authorization Header")
				return
			}
			parts := strings.Split(authHeader, " ")
			if len(parts) != 2 || parts[0] != "Bearer" {
				respondUnauthorized(w, "Invalid Header Format")
				return
			}
			tokenString := parts[1]

			// 3. Parse & Validate Token using the Public Key
			token, err := jwt.Parse(tokenString, k.Keyfunc)

			if err != nil || !token.Valid {
				log.Printf("Token validation failed: %v", err)
				respondUnauthorized(w, "Invalid Token")
				return
			}

			// 4. Extract Claims
			claims, ok := token.Claims.(jwt.MapClaims)
			if !ok {
				respondUnauthorized(w, "Invalid Token Claims")
				return
			}

			userID, _ := claims["sub"].(string)
			email, _ := claims["email"].(string)

			if userID == "" {
				respondUnauthorized(w, "Token missing User ID")
				return
			}

			// 5. JIT Provisioning (Same as before)
			user := models.User{
				ID:    userID,
				Email: email,
			}
			// Upsert user
			if err := db.Save(&user).Error; err != nil {
				respondError(w, http.StatusInternalServerError, "db_error", "Failed to sync user")
				return
			}

			// 6. Set Context
			ctx := context.WithValue(r.Context(), UserContextKey, &user)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}