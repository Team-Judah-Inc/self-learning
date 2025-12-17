package models

import "time"

type User struct {
	ID        string `gorm:"primaryKey"`
	Email     string `gorm:"uniqueIndex"`
	Password  string // Hashed
	CreatedAt time.Time
	UpdatedAt time.Time
}
