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

	return accounts, nil
}

// GetAccountTransactions retrieves transactions for a specific account
// Verifies that the account belongs to the user
func (s *AccountService) GetAccountTransactions(userID, accountID string) ([]models.Transaction, error) {
	// 1. Verify account ownership
	var account models.Account
	if err := s.db.Where("id = ? AND user_id = ?", accountID, userID).First(&account).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrNotFound
		}
		return nil, err
	}

	// 2. Fetch transactions
	var transactions []models.Transaction
	if err := s.db.Where("account_id = ?", accountID).Order("transaction_date desc").Find(&transactions).Error; err != nil {
		return nil, err
	}

	return transactions, nil
}
