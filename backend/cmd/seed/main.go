package main

import (
	"log"
	"time"

	"github.com/self-learning/backend/internal/config"
	"github.com/self-learning/backend/internal/database"
	"github.com/self-learning/backend/internal/models"
)

func main() {
	// 1. Load config and connect to DB
	cfg := config.Load()
	db := database.Connect(cfg.DatabasePath)

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

	// 4. Seed a dummy transaction
	newTransaction := models.Transaction{
		ID:                    "txn-test-001",
		AccountID:             newAccount.ID,
		ProviderTransactionID: "prov-txn-001",
		Amount:                -150.50,
		Currency:              "ILS",
		Description:           "Supermarket Purchase",
		MerchantName:          "Super Sal",
		Category:              "Groceries",
		TransactionDate:       time.Now().Add(-24 * time.Hour), // Yesterday
	}

	if err := db.Save(&newTransaction).Error; err != nil {
		log.Fatalf("❌ Failed to seed transaction: %v", err)
	}

	log.Printf("🌱 Seeded Transaction: %s for Account: %s", newTransaction.ID, newAccount.ID)
	log.Println("🚀 Run 'go run cmd/server/main.go' to see the Fetcher pick it up!")
}
