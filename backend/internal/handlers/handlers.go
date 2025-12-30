package handlers

import (
	"time"

	"github.com/self-learning/backend/internal/services"
)

type Handler struct {
	accountService *services.AccountService
	startTime      time.Time
}

func New(
	accountService *services.AccountService,
) *Handler {
	return &Handler{
		accountService: accountService,
		startTime:      time.Now(),
	}
}
