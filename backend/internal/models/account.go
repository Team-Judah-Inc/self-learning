package models

import (
	"time"

	"gorm.io/gorm"
)

type SyncStatus string

const (
	StatusIdle        SyncStatus = "IDLE"
	StatusPendingSync SyncStatus = "PENDING_SYNC"
	StatusSyncing     SyncStatus = "SYNCING"
	StatusFetched     SyncStatus = "FETCHED"
	StatusFailed      SyncStatus = "FAILED"
)

type Account struct {
	ID       string `gorm:"primaryKey;type:string"` // UUID
	UserID   string `gorm:"index"`
	Provider string // e.g., "leumi", "visa"

	ExternalAccountID string `gorm:"uniqueIndex"`
	Balance           float64
	Currency          string

	// Sync Engine Fields
	SyncStatus SyncStatus `gorm:"default:'IDLE'"`
	Priority   int        `gorm:"default:10"`

	LastSyncedCursor *time.Time

	LastUpdatedAt   time.Time
	LastSyncAttempt time.Time

	CreatedAt time.Time
	UpdatedAt time.Time
	DeletedAt gorm.DeletedAt `gorm:"index"`
}
