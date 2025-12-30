package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/self-learning/backend/internal/models"
)

// respondJSON sends a JSON response with the given status code
func respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// respondOK sends a 200 OK JSON response (most common success case)
func respondOK(w http.ResponseWriter, data interface{}) {
	respondJSON(w, http.StatusOK, data)
}

// respondError sends a standardized error response
func respondError(w http.ResponseWriter, status int, errorCode, message string) {
	respondJSON(w, status, models.ErrorResponse{
		Error:   errorCode,
		Message: message,
		Code:    status,
	})
}

// Common error responses
func respondBadRequest(w http.ResponseWriter, message string) {
	respondError(w, http.StatusBadRequest, "bad_request", message)
}

func respondUnauthorized(w http.ResponseWriter, message string) {
	respondError(w, http.StatusUnauthorized, "unauthorized", message)
}

func respondNotFound(w http.ResponseWriter, message string) {
	respondError(w, http.StatusNotFound, "not_found", message)
}

func respondInternalError(w http.ResponseWriter, message string) {
	respondError(w, http.StatusInternalServerError, "internal_error", message)
}
