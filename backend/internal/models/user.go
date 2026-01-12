package models

import (
	"time"
)

type User struct {
	// The ID will be the UUID from Supabase (e.g. "a0eebc99-9c0b...")
	ID        string    `gorm:"primaryKey" json:"id"` 
	Email     string    `gorm:"uniqueIndex;not null" json:"email"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}