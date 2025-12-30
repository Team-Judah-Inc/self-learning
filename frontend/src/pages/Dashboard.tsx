import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { mockApi } from '../services/mockApi';
import type { User, Account, Transaction } from '../types';
import AccountCard from '../components/AccountCard';
import TransactionList from '../components/TransactionList';
import './Dashboard.css';

export default function Dashboard() {
  const { userId, logout } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (!userId) return;

      try {
        const [userData, accountsData, transactionsData] = await Promise.all([
          mockApi.getUserProfile(userId),
          mockApi.getAccounts(userId),
          mockApi.getTransactions(userId),
        ]);

        setUser(userData);
        setAccounts(accountsData);
        setTransactions(transactionsData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [userId]);

  if (loading) {
    return (
      <div className="dashboard-page flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-header-content">
          <h1 className="dashboard-title">Finance Dashboard</h1>
          <div className="user-info">
            <span className="welcome-text">
              Welcome, {user?.first_name} {user?.last_name}
            </span>
            <button
              onClick={logout}
              className="logout-button"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Accounts Grid */}
        <section className="mb-8">
          <h2 className="section-title">Your Accounts</h2>
          <div className="accounts-grid">
            {accounts.map((account) => (
              <div key={account.id} className="account-card">
                <div className="account-header">
                  <div>
                    <h3 className="account-provider">{account.provider}</h3>
                    <p className="account-id">{account.external_account_id}</p>
                  </div>
                  <span
                    className={`sync-status ${
                      account.sync_status === 'FETCHED'
                        ? 'sync-status-fetched'
                        : account.sync_status === 'FAILED'
                        ? 'sync-status-failed'
                        : 'sync-status-pending'
                    }`}
                  >
                    {account.sync_status}
                  </span>
                </div>
                <div>
                  <p className="account-balance">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: account.currency,
                    }).format(account.balance)}
                  </p>
                  <p className="last-updated">
                    Last updated: {new Date(account.last_updated_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Transactions List */}
        <section className="transactions-container">
          <div className="transactions-header">
            <h3 className="transactions-title">Recent Transactions</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="transactions-table">
              <thead className="table-header">
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Category</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((txn) => (
                  <tr key={txn.id} className="transaction-row">
                    <td className="transaction-date">
                      {new Date(txn.transaction_date).toLocaleDateString()}
                    </td>
                    <td>
                      <div className="merchant-name">{txn.merchant_name}</div>
                      <div className="transaction-description">{txn.description}</div>
                    </td>
                    <td>
                      <span className="transaction-category">{txn.category}</span>
                    </td>
                    <td className={`transaction-amount ${txn.amount < 0 ? 'amount-negative' : 'amount-positive'}`}>
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: txn.currency,
                      }).format(txn.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}