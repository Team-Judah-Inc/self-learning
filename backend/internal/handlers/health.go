package handlers

import (
	"net/http"
	"time"
)

func (h *Handler) HealthCheck(w http.ResponseWriter, r *http.Request) {
	uptime := time.Since(h.startTime)

	// Return direct object (best practice for health checks)
	respondOK(w, map[string]interface{}{
		"status": "healthy",
		"uptime": uptime.String(),
	})
}
