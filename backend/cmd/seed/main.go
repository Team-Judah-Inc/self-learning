package main

import (
	"log"
	"time"

	"github.com/self-learning/backend/internal/database"
	"github.com/self-learning/backend/internal/models"
)

func main() {
	// 1. Connect to DB
	db := database.Connect("riseapp.db")

	// 2. Define a dummy account that needs syncing
	newAccount := models.Account{
		ID:                "acc-test-001",
		UserID:            "user-dave",
		Provider:          "bank_leumi",
		ExternalAccountID: "8888-99",

		// THE TRIGGER: This tells the Fetcher to pick it up!
		SyncStatus: models.StatusPendingSync,
		Priority:   100, // High priority

		Currency:  "ILS",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// 3. Upsert (Create if not exists, Update if exists)
	// We reset status to PENDING_SYNC in case it was already there and IDLE
	result := db.Save(&newAccount)
	if result.Error != nil {
		log.Fatalf("❌ Failed to seed account: %v", result.Error)
	}

	log.Printf("🌱 Seeded Account: %s (Status: PENDING_SYNC)", newAccount.ID)
	log.Println("🚀 Run 'go run cmd/server/main.go' to see the Fetcher pick it up!")
}
