package handlers

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/self-learning/backend/internal/models"
)

func (h *Handler) HealthCheck(w http.ResponseWriter, r *http.Request) {
	uptime := time.Since(h.startTime)

	response := models.APIResponse{
		Success: true,
		Data: map[string]interface{}{
			"uptime": uptime.String(),
			"status": "healthy",
		},
		Message: "Server is running",
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
