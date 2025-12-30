package handlers

import (
	"errors"
	"net/http"

	"github.com/self-learning/backend/internal/middleware"
	"github.com/self-learning/backend/internal/services"
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
		// Handle specific error types
		if errors.Is(err, services.ErrNotFound) {
			respondNotFound(w, "No accounts found for user")
			return
		}
		respondInternalError(w, "Failed to retrieve accounts")
		return
	}

	// Return accounts directly (best practice for simple lists)
	respondOK(w, accounts)
}