import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import json

print("Generating Account & Ledger Dataset...\n")

fake = Faker('en_IN')
Faker.seed(42)
random.seed(42)

# Generate Accounts
print("Creating accounts...")
accounts = []
for i in range(5000):
    accounts.append({
        'account_id': f'ACC{i+1:08d}',
        'account_number': f'{random.randint(1000000000, 9999999999)}',
        'customer_id': f'CUST{random.randint(1, 10000):06d}',
        'account_type': random.choice(['SAVINGS', 'CURRENT', 'FIXED_DEPOSIT', 'RECURRING_DEPOSIT']),
        'account_status': random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'DORMANT', 'CLOSED']),
        'opening_date': fake.date_between(start_date='-10y', end_date='today').strftime('%Y-%m-%d'),
        'branch_code': f'BR{random.randint(1000, 9999)}',
        'currency': 'INR',
        'current_balance': round(random.uniform(1000, 1000000), 2),
        'available_balance': round(random.uniform(1000, 1000000), 2),
        'overdraft_limit': round(random.uniform(0, 50000), 2) if random.random() > 0.7 else 0,
        'interest_rate': round(random.uniform(3.5, 7.5), 2),
        'last_transaction_date': fake.date_between(start_date='-30d', end_date='today').strftime('%Y-%m-%d')
    })

df_accounts = pd.DataFrame(accounts)

# Generate Ledger Entries
print("Creating ledger entries...")
ledger = []
entry_id = 1

for account in accounts[:1000]:
    num_entries = random.randint(10, 50)
    balance = account['current_balance']
    
    for j in range(num_entries):
        debit = 0
        credit = 0
        entry_type = random.choice(['DEBIT', 'CREDIT'])
        amount = round(random.uniform(100, 50000), 2)
        
        if entry_type == 'DEBIT':
            debit = amount
            balance -= amount
        else:
            credit = amount
            balance += amount
        
        ledger.append({
            'entry_id': f'LED{entry_id:010d}',
            'account_id': account['account_id'],
            'transaction_date': fake.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d'),
            'value_date': fake.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d'),
            'transaction_type': random.choice(['DEPOSIT', 'WITHDRAWAL', 'TRANSFER_IN', 'TRANSFER_OUT', 'INTEREST', 'FEE', 'CHARGE']),
            'debit_amount': debit,
            'credit_amount': credit,
            'balance': round(balance, 2),
            'description': random.choice(['Cash Deposit', 'ATM Withdrawal', 'NEFT Transfer', 'UPI Payment', 'Interest Credit', 'Service Charge']),
            'reference_number': f'REF{random.randint(100000000, 999999999)}',
            'branch_code': account['branch_code'],
            'posted_by': f'USER{random.randint(1000, 9999)}',
            'posted_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        entry_id += 1

df_ledger = pd.DataFrame(ledger)

print(f"\n✓ Generated {len(df_accounts)} accounts")
print(f"✓ Generated {len(df_ledger)} ledger entries")

# Save in Parquet and ORC formats
print("\nSaving in Parquet and ORC formats...")

# Parquet
df_accounts.to_parquet('accounts.parquet', index=False)
df_ledger.to_parquet('ledger.parquet', index=False)
print("✓ Parquet: accounts.parquet, ledger.parquet")

# ORC
import pyarrow.orc as orc
import pyarrow as pa

table_accounts = pa.Table.from_pandas(df_accounts)
table_ledger = pa.Table.from_pandas(df_ledger)

orc.write_table(table_accounts, 'accounts.orc')
orc.write_table(table_ledger, 'ledger.orc')
print("✓ ORC: accounts.orc, ledger.orc")

# Stats
stats = {
    "accounts": {
        "total": len(df_accounts),
        "active": int(df_accounts[df_accounts['account_status'] == 'ACTIVE'].shape[0]),
        "total_balance": float(df_accounts['current_balance'].sum()),
        "avg_balance": float(df_accounts['current_balance'].mean())
    },
    "ledger": {
        "total_entries": len(df_ledger),
        "total_debits": float(df_ledger['debit_amount'].sum()),
        "total_credits": float(df_ledger['credit_amount'].sum())
    }
}

with open('account_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

print("\n✓ Stats saved: account_stats.json")
