package ingestion

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/self-learning/backend/internal/models"
	"gorm.io/gorm"
)

// StartFetcherLoop is the main entry point for the extraction process.
// It continuously looks for accounts that need syncing.
func StartFetcherLoop(db *gorm.DB, queue chan<- SyncJob) {
	log.Println("🚜 Ingestion Engine: Fetcher Loop Started")

	ticker := time.NewTicker(5 * time.Second)

	for range ticker.C {
		// 1. Find and Lock work (The "Steal")
		accounts, err := stealWork(db)
		if err != nil {
			log.Printf("❌ Fetcher: Error stealing work: %v", err)
			continue
		}

		if len(accounts) == 0 {
			// No work found, sleep until next tick
			continue
		}

		log.Printf("🚜 Fetcher: Picked up %d accounts", len(accounts))

		// 2. Process each account
		for _, acc := range accounts {
			processAccount(db, acc, queue)
		}
	}
}

// stealWork atomically finds eligible accounts and marks them as SYNCING.
func stealWork(db *gorm.DB) ([]models.Account, error) {
	var accounts []models.Account

	// Transaction ensures we don't pick up the same row twice in race conditions
	err := db.Transaction(func(tx *gorm.DB) error {

		// A. Define the eligibility criteria
		// 1. User requested (PENDING_SYNC)
		// 2. Scheduled (IDLE + >6 hours old)
		// 3. Zombie Recovery (SYNCING + >1 hour old)

		now := time.Now()
		sixHoursAgo := now.Add(-6 * time.Hour)
		oneHourAgo := now.Add(-1 * time.Hour)

		var eligibleIDs []string

		// Use a subquery logic to find IDs first.
		// (This is safer in GORM/SQLite than complex UPDATE...FROM syntax)
		err := tx.Model(&models.Account{}).
			Select("id").
			Where("sync_status = ?", models.StatusPendingSync).                                // Priority 1
			Or("sync_status = ? AND last_updated_at < ?", models.StatusIdle, sixHoursAgo).     // Priority 2
			Or("sync_status = ? AND last_sync_attempt < ?", models.StatusSyncing, oneHourAgo). // Priority 3
			Order("priority DESC").                                                            // High priority first
			Limit(10).                                                                         // Batch size
			Find(&eligibleIDs).Error

		if err != nil {
			return err
		}

		if len(eligibleIDs) == 0 {
			return nil // Nothing to do
		}

		// B. Atomic Update ("Lock")
		err = tx.Model(&models.Account{}).
			Where("id IN ?", eligibleIDs).
			Updates(map[string]interface{}{
				"sync_status":       models.StatusSyncing,
				"last_sync_attempt": now,
			}).Error

		if err != nil {
			return err
		}

		// C. Return the full objects for processing
		return tx.Where("id IN ?", eligibleIDs).Find(&accounts).Error
	})

	return accounts, err
}

func processAccount(db *gorm.DB, acc models.Account, queue chan<- SyncJob) {
	// 1. Determine "From Date" (Cursor)
	// Default to 90 days ago if this is the first sync
	cursor := time.Now().Add(-90 * 24 * time.Hour)
	if acc.LastSyncedCursor != nil {
		cursor = *acc.LastSyncedCursor
	}

	// 2. Call the Mock Bank Provider
	// In a real app, this would use the `acc.ExternalAccountID`
	log.Printf("   -> Fetching Account %s (Provider: %s) Cursor: %s",
		acc.ID, acc.Provider, cursor.Format("2006-01-02"))

	rawData, err := fetchFromBankMock(acc.Provider, cursor)
	if err != nil {
		log.Printf("   ❌ Failed to fetch %s: %v", acc.ID, err)
		// Mark failed so it doesn't get stuck in SYNCING forever (until zombie killer)
		db.Model(&acc).Updates(map[string]interface{}{
			"sync_status": models.StatusFailed,
			"last_error":  err.Error(),
		})
		return
	}

	// 3. Save to "S3" (Local File System for MVP)
	s3Path, err := saveToLocalStorage(acc.ID, rawData)
	if err != nil {
		log.Printf("   ❌ Failed to save raw data: %v", err)
		return
	}

	// 4. Handoff to Normalizer (Queue)
	log.Printf("   🔔 Auto-Triggering Queue for Account %s...", acc.ID)
	job := SyncJob{
		AccountID: acc.ID,
		Cursor:    cursor, // Pass the time we used to fetch
		S3Path:    s3Path,
		FetchedAt: time.Now(),
	}
	queue <- job

	// 5. Update Status (Checkpoint)
	// We mark it as FETCHED. The Normalizer will later move it to IDLE.
	// We reset priority to 10 so it doesn't block other users next time.
	db.Model(&acc).Updates(map[string]interface{}{
		"sync_status": models.StatusFetched,
		"priority":    10,
	})

	log.Printf("   ✅ Fetched & Queued: %s", acc.ID)
}

// --- Mocks (Placeholders for real services) ---

func fetchFromBankMock(provider string, from time.Time) ([]byte, error) {
	// Simulate network latency
	time.Sleep(200 * time.Millisecond)

	// Return dummy JSON
	mockData := []map[string]interface{}{
		{
			"id":       fmt.Sprintf("tx-%d", time.Now().UnixNano()),
			"amount":   -150.00,
			"merchant": "Mock Purchase " + provider,
			"date":     time.Now().Format(time.RFC3339),
			"currency": "ILS",
			"status":   "SETTLED",
		},
		{
			"id":       fmt.Sprintf("tx-%d-2", time.Now().UnixNano()),
			"amount":   -45.00,
			"merchant": "Coffee Shop",
			"date":     time.Now().Format(time.RFC3339),
			"currency": "ILS",
			"status":   "PENDING",
		},
	}
	return json.Marshal(mockData)
}

func saveToLocalStorage(accountID string, data []byte) (string, error) {
	// Ensure directory exists: storage/raw/{accountID}/
	dir := filepath.Join("storage", "raw", accountID)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", err
	}

	// File: timestamp.json
	filename := fmt.Sprintf("%d.json", time.Now().Unix())
	fullPath := filepath.Join(dir, filename)

	err := os.WriteFile(fullPath, data, 0644)
	return fullPath, err
}
