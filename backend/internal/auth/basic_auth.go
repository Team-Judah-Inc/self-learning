package auth

// AuthUser represents a user for authentication (lightweight)
type AuthUser struct {
	Username string
	Password string
}

// Simple user store with plain text passwords (fine for demo)
var validUsers = map[string]string{
	"admin":     "password123",
	"noy":       "theQueen",
	"demo":      "demo123",
	"user-dave": "password123",
}

// ValidateCredentials validates username and password and returns user info
func ValidateCredentials(username, password string) (*AuthUser, bool) {
	storedPassword, exists := validUsers[username]
	if !exists {
		return nil, false
	}

	if storedPassword == password {
		return &AuthUser{Username: username}, true
	}

	return nil, false
}
