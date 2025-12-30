// auth/jwt.go
package auth

import (
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var jwtKey = []byte("TempTestForLearningKey") // CHANGE THIS!

type CustomClaims struct {
	UserID   string `json:"user_id"`
	Username string `json:"username"`
	jwt.RegisteredClaims
}

// GenerateToken creates a new JWT string for a given user.
func GenerateToken(userID, username string) (string, error) {
	// 1. Define the Claims (Payload)
	//expirationTime := time.Now().Add(5 * time.Minute) // Access token should be short-lived (e.g., 5 min)

	claims := &CustomClaims{
		UserID:   userID,
		Username: username,
		RegisteredClaims: jwt.RegisteredClaims{
			IssuedAt: jwt.NewNumericDate(time.Now()),
			Subject:  userID, // The principal of the token (the user)
		},
	}

	// 2. Create the Token object
	// Use jwt.SigningMethodHS256 for HMAC-SHA256
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)

	// 3. Sign the token to get the complete encoded string
	tokenString, err := token.SignedString(jwtKey)

	if err != nil {
		return "", fmt.Errorf("could not sign token: %w", err)
	}

	return tokenString, nil
}
