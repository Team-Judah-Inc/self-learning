package handlers

import (
	"errors"
	"net/http"

	"github.com/gorilla/mux"
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
	accounts, err := h.accountService.GetUserAccounts(user.ID)
	if err != nil {
        respondInternalError(w, "Failed to retrieve accounts")
        return
    }

	// Return accounts directly (best practice for simple lists)
	respondOK(w, accounts)
}

// GetAccountTransactions retrieves transactions for a specific account
func (h *Handler) GetAccountTransactions(w http.ResponseWriter, r *http.Request) {
	// Get authenticated user
	user, ok := middleware.RequireAuth(w, r)
	if !ok {
		return
	}

	// Get account ID from URL
	vars := mux.Vars(r)
	accountID := vars["accountID"]
	if accountID == "" {
		respondBadRequest(w, "Account ID is required")
		return
	}

	// Get transactions
	transactions, err := h.accountService.GetAccountTransactions(user.ID, accountID)
	if err != nil {
		if errors.Is(err, services.ErrNotFound) {
			respondNotFound(w, "Account not found")
			return
		}
		respondInternalError(w, "Failed to retrieve transactions")
		return
	}

	respondOK(w, transactions)
}