package middleware

import (
	"encoding/json"
	"net/http"

	"github.com/self-learning/backend/internal/models"
)

// respondError sends a standardized error response from middleware
func respondError(w http.ResponseWriter, status int, errorCode, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(models.ErrorResponse{
		Error:   errorCode,
		Message: message,
		Code:    status,
	})
}

// respondUnauthorized sends a 401 error response
func respondUnauthorized(w http.ResponseWriter, message string) {
	w.Header().Set("WWW-Authenticate", `Basic realm="Restricted"`)
	respondError(w, http.StatusUnauthorized, "unauthorized", message)
}