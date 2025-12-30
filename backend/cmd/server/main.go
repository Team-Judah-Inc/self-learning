package main

import (
	"log"

	"github.com/self-learning/backend/internal/config"
	"github.com/self-learning/backend/internal/database"
	"github.com/self-learning/backend/internal/ingestion"
	"github.com/self-learning/backend/internal/server"
)

func main() {
	cfg := config.Load()

	srv := server.New(cfg)

	// 1. Initialize Database
	db := database.Connect("riseapp.db")

	// 2. Create the internal Queue (Buffered Channel)
	// This acts as the "Queue" between Fetcher and Normalizer
	queue := make(chan ingestion.SyncJob, 100)

	// 3. Start the Background Fetcher (The Engine)
	go ingestion.StartFetcherLoop(db, queue)

	// 4. Start the Real Normalizer (The Chef - Loop B)
	go ingestion.StartNormalizerLoop(db, queue)

	log.Printf("Server starting on port %s", cfg.Port)
	if err := srv.Start(); err != nil {
		log.Fatal(err)
	}
}
