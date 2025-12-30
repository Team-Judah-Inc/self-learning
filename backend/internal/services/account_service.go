package services

import (
	"github.com/self-learning/backend/internal/models"
	"gorm.io/gorm"
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
func (s *AccountService) GetUserAccounts(userID string) ([]models.Account, error) {
	var accounts []models.Account
	
	err := s.db.Where("user_id = ?", userID).Find(&accounts).Error
	if err != nil {
		return nil, err
	}
	
	return accounts, nil
}