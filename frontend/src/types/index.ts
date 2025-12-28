export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
  updated_at: string;
}

export interface Account {
  id: string;
  user_id: string;
  provider: string;
  external_account_id: string;
  balance: number;
  currency: string;
  sync_status: 'IDLE' | 'FETCHED' | 'SYNCING' | 'FAILED';
  priority: number;
  last_synced_cursor: string;
  last_updated_at: string;
  last_sync_attempt: string;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  account_id: string;
  provider_transaction_id: string;
  amount: number;
  currency: string;
  description: string;
  merchant_name: string;
  category: string;
  transaction_date: string;
  system_inserted_at: string;
}