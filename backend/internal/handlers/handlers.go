package handlers

import (
	"time"

	"github.com/self-learning/backend/internal/services"
)

type Handler struct {
	authService *services.AuthService
	startTime   time.Time
}

func New(
// authService *services.AuthService,
) *Handler {
	return &Handler{
		//authService: authService,
		startTime: time.Now(),
	}
}
