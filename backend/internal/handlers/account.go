package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/self-learning/backend/internal/middleware"
	"github.com/self-learning/backend/internal/models"
)

// GetUserAccounts retrieves all connected accounts for the authenticated user
func (h *Handler) GetUserAccounts(w http.ResponseWriter, r *http.Request) {
	// Get authenticated user from context
	user, ok := middleware.RequireAuth(w, r)
	if !ok {
		return
	}

	// Get accounts from service
	accounts, err := h.accountService.GetUserAccounts(user.Username)
	if err != nil {
		http.Error(w, "Failed to retrieve accounts", http.StatusInternalServerError)
		return
	}

	// Return accounts as JSON
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models.APIResponse{
		Success: true,
		Data:    accounts,
	})
}