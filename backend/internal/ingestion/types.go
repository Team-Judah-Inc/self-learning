package ingestion

import "time"

// SyncJob represents a payload handed off from the Fetcher to the Normalizer.
// It tells the Normalizer where the raw data is and what time it represents.
type SyncJob struct {
	AccountID string
	Cursor    time.Time // The "From" date used for this fetch
	S3Path    string    // Where the raw JSON is stored (e.g., storage/raw/...)
	FetchedAt time.Time // When we physically pulled the data
}
