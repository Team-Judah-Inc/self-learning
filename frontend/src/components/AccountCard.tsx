import type { Account } from '../types';

interface AccountCardProps {
  account: Account;
}

export default function AccountCard({ account }: AccountCardProps) {
  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 capitalize">
            {account.provider}
          </h3>
          <p className="text-sm text-gray-500">
            {account.external_account_id}
          </p>
        </div>
        <span
          className={`px-2 py-1 text-xs font-medium rounded-full ${
            account.sync_status === 'FETCHED'
              ? 'bg-green-100 text-green-800'
              : account.sync_status === 'FAILED'
              ? 'bg-red-100 text-red-800'
              : 'bg-yellow-100 text-yellow-800'
          }`}
        >
          {account.sync_status}
        </span>
      </div>
      <div className="mt-2">
        <p className="text-2xl font-bold text-gray-900">
          {formatCurrency(account.balance, account.currency)}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Last updated: {new Date(account.last_updated_at).toLocaleDateString()}
        </p>
      </div>
    </div>
  );
}