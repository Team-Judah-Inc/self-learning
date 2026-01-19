package database

import (
	"log"
	"os"
	"path/filepath"

	"github.com/self-learning/backend/internal/models"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

func Connect(dbName string) *gorm.DB {
	if dbName == "" {
		dbName = "riseapp.db"
	}

	// 1. Ensure directory exists
	dbDir := filepath.Dir(dbName)
	if dbDir != "." && dbDir != "" {
		if err := os.MkdirAll(dbDir, 0755); err != nil {
			log.Fatalf("Failed to create database directory %s: %v", dbDir, err)
		}
	}

	// 2. Open Connection
	db, err := gorm.Open(sqlite.Open(dbName), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	// 3. Enable WAL Mode for concurrency
	db.Exec("PRAGMA journal_mode=WAL;")

	// 4. Auto Migrate
	log.Println("Running Database Migrations...")
	err = db.AutoMigrate(
		&models.User{},
		&models.Account{},
		&models.Transaction{},
	)
	if err != nil {
		log.Fatal("Migration failed:", err)
	}
	log.Println("Database Migration Complete!")

	return db
}
