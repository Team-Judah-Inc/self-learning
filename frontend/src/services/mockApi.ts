import type { User, Account, Transaction } from '../types';
import mockUsers from '../../mock_data/mock_user.json';
import mockAccounts from '../../mock_data/mock_accounts.json';
import mockTransactions from '../../mock_data/mock_transactions.json';

// Simulate network delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockApi = {
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