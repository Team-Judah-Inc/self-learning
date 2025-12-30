import type { User, Account, Transaction } from '../types';
import mockUsers from '../../mock_data/mock_user.json';
import mockAccounts from '../../mock_data/mock_accounts.json';
import mockTransactions from '../../mock_data/mock_transactions.json';
import mockAuth from '../../mock_data/mock_authenticate.json';

// Simulate network delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Define the authentication user type
interface AuthUser {
  id: string;
  email: string;
  password: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export const mockApi = {
  authenticate: async (email: string, password: string): Promise<{ success: boolean; userId?: string; error?: string }> => {
    await delay(500);
    
    const user = (mockAuth as AuthUser[]).find(
      (u) => u.email === email && u.password === password
    );
    
    if (!user) {
      return { success: false, error: "Invalid email or password" };
    }
    
    if (!user.active) {
      return { success: false, error: "Account is not active" };
    }
    
    return { success: true, userId: user.id };
  },

  getUserProfile: async (userId: string): Promise<User | null> => {
    await delay(500);
    const user = (mockUsers as User[]).find((u) => u.id === userId);
    return user || null;
  },

  getAccounts: async (userId: string): Promise<Account[]> => {
    await delay(500);
    return (mockAccounts as Account[]).filter((acc) => acc.user_id === userId);
  },

  getTransactions: async (userId: string): Promise<Transaction[]> => {
    await delay(500);
    // First get user's accounts
    const userAccountIds = (mockAccounts as Account[])
      .filter((acc) => acc.user_id === userId)
      .map((acc) => acc.id);

    // Then filter transactions for those accounts
    return (mockTransactions as Transaction[]).filter((txn) =>
      userAccountIds.includes(txn.account_id)
    );
  },
};