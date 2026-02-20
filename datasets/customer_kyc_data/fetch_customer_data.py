import pandas as pd
from faker import Faker
import random

print("Generating Indian KYC data...\n")

fake = Faker('en_IN')
Faker.seed(42)
random.seed(42)

indian_first_names = ['Rahul', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Anjali', 'Rohan', 'Pooja', 'Arjun', 'Neha', 'Rajesh', 'Kavita', 'Sanjay', 'Deepika', 'Anil']
indian_last_names = ['Sharma', 'Patel', 'Kumar', 'Singh', 'Reddy', 'Gupta', 'Verma', 'Iyer', 'Joshi', 'Mehta', 'Nair', 'Rao', 'Desai', 'Agarwal', 'Malhotra']
indian_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Lucknow']
indian_states = ['Maharashtra', 'Delhi', 'Karnataka', 'Telangana', 'Tamil Nadu', 'Gujarat', 'West Bengal', 'Rajasthan', 'Uttar Pradesh']

kyc_data = []

for i in range(5000):
    first = random.choice(indian_first_names)
    last = random.choice(indian_last_names)
    city = random.choice(indian_cities)
    
    kyc_data.append({
        'customer_id': f'IND{i+1:06d}',
        'account_number': f'{random.randint(1000000000, 9999999999)}',
        'first_name': first,
        'last_name': last,
        'email': f'{first.lower()}.{last.lower()}{random.randint(1,999)}@gmail.com',
        'phone': f'+91{random.randint(7000000000, 9999999999)}',
        'aadhaar': f'{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}',
        'pan': f'{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}{random.randint(1000, 9999)}{random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}',
        'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d'),
        'address': fake.street_address(),
        'city': city,
        'state': random.choice(indian_states),
        'pin_code': f'{random.randint(100000, 999999)}',
        'country': 'India',
        'occupation': fake.job(),
        'annual_income': random.randint(300000, 5000000),
        'marital_status': random.choice(['Single', 'Married', 'Divorced', 'Widowed']),
        'education': random.choice(['10th', '12th', 'Graduate', 'Post Graduate', 'Professional']),
        'credit_score': random.randint(550, 900),
        'account_balance': round(random.uniform(-50000, 1000000), 2),
        'credit_default': random.choice(['yes', 'no']),
        'housing_loan': random.choice(['yes', 'no']),
        'personal_loan': random.choice(['yes', 'no']),
        'kyc_status': random.choice(['VERIFIED', 'VERIFIED', 'VERIFIED', 'PENDING']),
        'account_type': random.choice(['SAVINGS', 'CURRENT', 'SALARY']),
        'account_opened_date': fake.date_between(start_date='-10y', end_date='today').strftime('%Y-%m-%d'),
        'last_transaction_date': fake.date_between(start_date='-30d', end_date='today').strftime('%Y-%m-%d')
    })
    
    if (i + 1) % 1000 == 0:
        print(f"  Generated {i + 1} records...")

df = pd.DataFrame(kyc_data)

# Save in multiple formats
df.to_csv('kyc_customers.csv', index=False)
df.to_json('kyc_customers.json', orient='records', indent=2)
df.to_parquet('kyc_customers.parquet', index=False)

print(f"\n✓ {len(df)} Indian KYC records created")
print("✓ Files: kyc_customers.csv, kyc_customers.json, kyc_customers.parquet")
print(f"\nColumns ({len(df.columns)}): {', '.join(df.columns.tolist())}")
print("\nSample:")
print(df.head(3).to_string())
