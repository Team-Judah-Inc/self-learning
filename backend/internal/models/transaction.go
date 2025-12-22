package models

import (
	"time"
)

type Transaction struct {
	ID string `gorm:"primaryKey"`

	AccountID string `gorm:"index"` // Foreign Key to Account

	// Deduplication Key: (AccountID + ProviderTransactionID) must be unique
	ProviderTransactionID string `gorm:"uniqueIndex:idx_provider_txn"`

	Amount       float64
	Currency     string
	Description  string
	MerchantName string
	Category     string

	// --- EXPLICIT TIMESTAMPS ---

	// Business Time: When the transaction actually occurred at the bank
	TransactionDate time.Time `json:"transaction_date"`

	// System Time: When this record was inserted into our database
	// We use "autoCreateTime" so GORM handles this automatically
	SystemInsertedAt time.Time `gorm:"autoCreateTime" json:"system_inserted_at"`
}
