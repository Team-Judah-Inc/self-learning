package ingestion

import (
	"encoding/json"
	"log"
	"os"
	"time"

	"github.com/google/uuid"
	"github.com/self-learning/backend/internal/models"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

// StartNormalizerLoop listens to the queue and processes raw data into the DB.
func StartNormalizerLoop(db *gorm.DB, queue <-chan SyncJob) {
	log.Println("🏭 Ingestion Engine: Normalizer Loop Started")

	for job := range queue {
		processJob(db, job)
	}
}

func processJob(db *gorm.DB, job SyncJob) {
	log.Printf("   📥 Normalizer: Processing Job for Account %s", job.AccountID)

	// 1. Load Raw Data from "S3" (Local file)
	rawBytes, err := os.ReadFile(job.S3Path)
	if err != nil {
		log.Printf("   ❌ Normalizer: Failed to read file %s: %v", job.S3Path, err)
		return // In a real app, send to Dead Letter Queue
	}

	// 2. Parse (Normalize)
	transactions, err := parseTransactions(job.AccountID, rawBytes)
	if err != nil {
		log.Printf("   ❌ Normalizer: Failed to parse JSON: %v", err)
		return
	}

	// 3. Upsert (Idempotent Insert)
	if len(transactions) > 0 {
		err = upsertTransactions(db, transactions)
		if err != nil {
			log.Printf("   ❌ Normalizer: Failed to insert transactions: %v", err)
			return
		}
	}

	// 4. Finalize (Unlock Account)
	err = finalizeAccount(db, job)
	if err != nil {
		log.Printf("   ❌ Normalizer: Failed to update account status: %v", err)
		return
	}

	log.Printf("   ✨ Normalizer: Successfully synced %d transactions for %s", len(transactions), job.AccountID)
}

func parseTransactions(accountID string, data []byte) ([]models.Transaction, error) {
	// Define a struct that matches the *Mock Bank's* JSON format (from fetcher.go)
	type BankTxn struct {
		ID       string  `json:"id"`
		Amount   float64 `json:"amount"`
		Merchant string  `json:"merchant"`
		Date     string  `json:"date"` // RFC3339
		Currency string  `json:"currency"`
		Status   string  `json:"status"`
	}

	var bankTxns []BankTxn
	if err := json.Unmarshal(data, &bankTxns); err != nil {
		return nil, err
	}

	var internalTxns []models.Transaction
	for _, bt := range bankTxns {
		parsedDate, _ := time.Parse(time.RFC3339, bt.Date)

		t := models.Transaction{
			ID:                    uuid.New().String(), // Generate internal UUID
			AccountID:             accountID,
			ProviderTransactionID: bt.ID, // Critical for Deduplication!
			Amount:                bt.Amount,
			MerchantName:          bt.Merchant,
			Currency:              bt.Currency,
			TransactionDate:       parsedDate,
			SystemInsertedAt:      time.Now(),
		}
		internalTxns = append(internalTxns, t)
	}

	return internalTxns, nil
}

func upsertTransactions(db *gorm.DB, txns []models.Transaction) error {
	// GORM Clause: ON CONFLICT DO NOTHING
	// This relies on the unique index we defined in models/transaction.go
	return db.Clauses(clause.OnConflict{
		Columns:   []clause.Column{{Name: "provider_transaction_id"}},
		DoNothing: true, // Ignore duplicates
	}).Create(&txns).Error
}

func finalizeAccount(db *gorm.DB, job SyncJob) error {
	return db.Model(&models.Account{}).
		Where("id = ?", job.AccountID).
		Updates(map[string]interface{}{
			"sync_status":        models.StatusIdle, // Unlock!
			"last_synced_cursor": job.FetchedAt,     // Advance cursor
			"last_updated_at":    time.Now(),
			"priority":           10,
		}).Error
}
