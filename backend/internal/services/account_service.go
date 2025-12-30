package services

import (
	"errors"

	"github.com/self-learning/backend/internal/models"
	"gorm.io/gorm"
)

var (
	ErrNotFound = errors.New("no accounts found")
)

type AccountService struct {
	db *gorm.DB
}

func NewAccountService(db *gorm.DB) *AccountService {
	return &AccountService{
		db: db,
	}
}

// GetUserAccounts retrieves all accounts for a given user
// Returns ErrNotFound if user has no accounts
// Returns other error for database errors
func (s *AccountService) GetUserAccounts(userID string) ([]models.Account, error) {
	var accounts []models.Account
	
	err := s.db.Where("user_id = ?", userID).Find(&accounts).Error
	if err != nil {
		// Actual database error (connection issues, etc.)
		return nil, err
	}
	
	// Check if result is empty
	if len(accounts) == 0 {
		return nil, ErrNotFound
	}
	
	return accounts, nil
}