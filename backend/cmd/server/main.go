package main

import (
	"log"

	"github.com/self-learning/backend/internal/config"
	"github.com/self-learning/backend/internal/server"
)

func main() {
	// Load configuration
	cfg := config.Load()

	// Initialize and start server (handles all dependencies internally)
	srv := server.New(cfg)

	log.Printf("Server starting on port %s", cfg.Port)
	if err := srv.Start(); err != nil {
		log.Fatal(err)
	}
}
