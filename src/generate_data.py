#!/usr/bin/env python3
"""
TIMO Banking Data Generator
Generates realistic sample data for the banking data platform
"""

import os
import random
import string
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from faker import Faker
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

fake = Faker('vi_VN')  # Vietnamese locale

class DatabaseConfig:
    """Database configuration"""
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'timo_banking')
        self.username = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
    
    def get_connection_string(self):
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

class BankingDataGenerator:
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self.customers = []
        self.accounts = []
        self.devices = []
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.username,
                password=self.db_config.password,
                cursor_factory=RealDictCursor
            )
            self.conn.autocommit = True
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def generate_cccd(self):
        """Generate Vietnamese CCCD number (12 digits)"""
        return ''.join([str(random.randint(0, 9)) for _ in range(12)])
    
    def generate_account_number(self):
        """Generate unique account number"""
        return ''.join([str(random.randint(0, 9)) for _ in range(16)])
    
    def generate_phone_number(self):
        """Generate Vietnamese phone number"""
        prefixes = ['09', '08', '07', '05', '03']
        prefix = random.choice(prefixes)
        number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return f"{prefix}{number}"
    
    def generate_device_fingerprint(self):
        """Generate unique device fingerprint"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    def generate_customers(self, count=1000):
        """Generate customer data"""
        logger.info(f"Generating {count} customers...")
        
        cursor = self.conn.cursor()
        
        for i in range(count):
            customer_data = {
                'customer_id': str(uuid.uuid4()),
                'cccd_number': self.generate_cccd(),
                'passport_number': fake.bothify(text='?#######') if random.random() > 0.3 else None,
                'full_name': fake.name(),
                'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80),
                'phone_number': self.generate_phone_number(),
                'email': fake.email(),
                'address': fake.address(),
                'kyc_status': random.choices(['VERIFIED', 'PENDING', 'REJECTED'], weights=[85, 10, 5])[0],
                'risk_level': random.choices(['LOW', 'MEDIUM', 'HIGH'], weights=[80, 15, 5])[0],
                'is_active': random.choices([True, False], weights=[95, 5])[0],
                'created_at': fake.date_time_between(start_date='-2y', end_date='now'),
                'created_by': 'SYSTEM'
            }
            
            try:
                cursor.execute("""
                    INSERT INTO customers (
                        customer_id, cccd_number, passport_number, full_name, date_of_birth,
                        phone_number, email, address, kyc_status, risk_level, is_active,
                        created_at, created_by
                    ) VALUES (
                        %(customer_id)s, %(cccd_number)s, %(passport_number)s, %(full_name)s, %(date_of_birth)s,
                        %(phone_number)s, %(email)s, %(address)s, %(kyc_status)s, %(risk_level)s, %(is_active)s,
                        %(created_at)s, %(created_by)s
                    )
                """, customer_data)
                
                self.customers.append(customer_data)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Generated {i + 1} customers")
                    
            except psycopg2.IntegrityError:
                # Handle duplicate CCCD/phone/email
                continue
        
        logger.info(f"Successfully generated {len(self.customers)} customers")
    
    def generate_bank_accounts(self):
        """Generate bank accounts for customers"""
        logger.info("Generating bank accounts...")
        
        cursor = self.conn.cursor()
        
        for customer in self.customers:
            # Each customer gets 1-3 accounts
            num_accounts = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            
            for _ in range(num_accounts):
                account_data = {
                    'account_id': str(uuid.uuid4()),
                    'customer_id': customer['customer_id'],
                    'account_number': self.generate_account_number(),
                    'account_type': random.choices(['CHECKING', 'SAVINGS', 'CREDIT'], weights=[60, 30, 10])[0],
                    'balance': Decimal(str(random.uniform(0, 1000000000))),  # Up to 1B VND
                    'currency': 'VND',
                    'status': random.choices(['ACTIVE', 'SUSPENDED', 'CLOSED'], weights=[90, 5, 5])[0],
                    'daily_limit': Decimal(str(random.choice([20000000, 50000000, 100000000]))),
                    'monthly_limit': Decimal(str(random.choice([500000000, 1000000000, 2000000000]))),
                    'opened_date': fake.date_between(start_date=customer['created_at'].date(), end_date='today'),
                    'created_at': customer['created_at']
                }
                
                try:
                    cursor.execute("""
                        INSERT INTO bank_accounts (
                            account_id, customer_id, account_number, account_type, balance,
                            currency, status, daily_limit, monthly_limit, opened_date, created_at
                        ) VALUES (
                            %(account_id)s, %(customer_id)s, %(account_number)s, %(account_type)s, %(balance)s,
                            %(currency)s, %(status)s, %(daily_limit)s, %(monthly_limit)s, %(opened_date)s, %(created_at)s
                        )
                    """, account_data)
                    
                    self.accounts.append(account_data)
                    
                except psycopg2.IntegrityError:
                    continue
        
        logger.info(f"Successfully generated {len(self.accounts)} bank accounts")
    
    def generate_devices(self):
        """Generate devices for customers"""
        logger.info("Generating devices...")
        
        cursor = self.conn.cursor()
        
        device_types = ['MOBILE', 'WEB', 'ATM']
        device_os = ['Android', 'iOS', 'Windows', 'MacOS', 'Linux']
        
        for customer in self.customers:
            # Each customer has 1-4 devices
            num_devices = random.choices([1, 2, 3, 4], weights=[40, 35, 20, 5])[0]
            
            for _ in range(num_devices):
                device_data = {
                    'device_id': str(uuid.uuid4()),
                    'customer_id': customer['customer_id'],
                    'device_fingerprint': self.generate_device_fingerprint(),
                    'device_type': random.choice(device_types),
                    'device_os': random.choice(device_os),
                    'device_model': fake.bothify(text='Model-###'),
                    'ip_address': fake.ipv4(),
                    'user_agent': fake.user_agent(),
                    'is_trusted': random.choices([True, False], weights=[70, 30])[0],
                    'last_used_at': fake.date_time_between(start_date='-30d', end_date='now'),
                    'verification_status': random.choices(['VERIFIED', 'UNVERIFIED', 'SUSPICIOUS'], weights=[70, 25, 5])[0],
                    'created_at': fake.date_time_between(start_date=customer['created_at'], end_date='now')
                }
                
                try:
                    cursor.execute("""
                        INSERT INTO devices (
                            device_id, customer_id, device_fingerprint, device_type, device_os,
                            device_model, ip_address, user_agent, is_trusted, last_used_at,
                            verification_status, created_at
                        ) VALUES (
                            %(device_id)s, %(customer_id)s, %(device_fingerprint)s, %(device_type)s, %(device_os)s,
                            %(device_model)s, %(ip_address)s, %(user_agent)s, %(is_trusted)s, %(last_used_at)s,
                            %(verification_status)s, %(created_at)s
                        )
                    """, device_data)
                    
                    self.devices.append(device_data)
                    
                except psycopg2.IntegrityError:
                    continue
        
        logger.info(f"Successfully generated {len(self.devices)} devices")
    
    def generate_authentication_logs(self, count=10000):
        """Generate authentication logs"""
        logger.info(f"Generating {count} authentication logs...")
        
        cursor = self.conn.cursor()
        auth_methods = ['PASSWORD', 'OTP_SMS', 'OTP_EMAIL', 'BIOMETRIC', 'PIN']
        auth_statuses = ['SUCCESS', 'FAILED', 'EXPIRED']
        
        for i in range(count):
            customer = random.choice(self.customers)
            device = random.choice([d for d in self.devices if d['customer_id'] == customer['customer_id']])
            
            auth_data = {
                'auth_id': str(uuid.uuid4()),
                'customer_id': customer['customer_id'],
                'device_id': device['device_id'],
                'auth_method': random.choice(auth_methods),
                'auth_status': random.choices(auth_statuses, weights=[85, 12, 3])[0],
                'ip_address': fake.ipv4(),
                'location_data': json.dumps({
                    'country': 'Vietnam',
                    'city': fake.city(),
                    'latitude': float(fake.latitude()),
                    'longitude': float(fake.longitude())
                }),
                'risk_score': random.randint(0, 100),
                'failed_attempts': random.randint(0, 3) if random.random() > 0.8 else 0,
                'created_at': fake.date_time_between(start_date='-90d', end_date='now')
            }
            
            cursor.execute("""
                INSERT INTO authentication_logs (
                    auth_id, customer_id, device_id, auth_method, auth_status,
                    ip_address, location_data, risk_score, failed_attempts, created_at
                ) VALUES (
                    %(auth_id)s, %(customer_id)s, %(device_id)s, %(auth_method)s, %(auth_status)s,
                    %(ip_address)s, %(location_data)s, %(risk_score)s, %(failed_attempts)s, %(created_at)s
                )
            """, auth_data)
            
            if (i + 1) % 1000 == 0:
                logger.info(f"Generated {i + 1} authentication logs")
        
        logger.info(f"Successfully generated {count} authentication logs")
    
    def generate_transactions(self, count=50000):
        """Generate transactions with compliance edge cases"""
        logger.info(f"Generating {count} transactions...")
        
        cursor = self.conn.cursor()
        transaction_types = ['TRANSFER', 'DEPOSIT', 'WITHDRAWAL', 'PAYMENT', 'REFUND']
        channels = ['ATM', 'ONLINE', 'MOBILE', 'BRANCH', 'CARD']
        auth_methods = ['PASSWORD', 'OTP_SMS', 'OTP_EMAIL', 'BIOMETRIC', 'PIN']
        
        active_accounts = [acc for acc in self.accounts if acc['status'] == 'ACTIVE']
        
        for i in range(count):
            from_account = random.choice(active_accounts)
            to_account = random.choice(active_accounts) if random.random() > 0.3 else None
            
            # Generate amount with edge cases
            if random.random() < 0.1:  # 10% high-value transactions (>10M VND)
                amount = Decimal(str(random.uniform(10000000, 100000000)))
                requires_strong_auth = True
                is_high_risk = True
                risk_score = random.randint(70, 100)
            elif random.random() < 0.05:  # 5% very high-value transactions (>50M VND)
                amount = Decimal(str(random.uniform(50000000, 500000000)))
                requires_strong_auth = True
                is_high_risk = True
                risk_score = random.randint(80, 100)
            else:  # Normal transactions
                amount = Decimal(str(random.uniform(10000, 10000000)))
                requires_strong_auth = amount > 10000000
                is_high_risk = random.random() < 0.05
                risk_score = random.randint(0, 70)
            
            # Ensure compliance for high-value transactions
            auth_method = random.choice(auth_methods)
            if requires_strong_auth and random.random() < 0.9:  # 90% compliance
                auth_method = random.choice(['BIOMETRIC', 'OTP_SMS', 'OTP_EMAIL'])
            elif requires_strong_auth:  # 10% non-compliance for testing
                auth_method = random.choice(['PASSWORD', 'PIN'])
            
            transaction_data = {
                'transaction_id': str(uuid.uuid4()),
                'from_account_id': from_account['account_id'],
                'to_account_id': to_account['account_id'] if to_account else None,
                'transaction_type': random.choice(transaction_types),
                'amount': amount,
                'currency': 'VND',
                'description': fake.sentence(nb_words=6),
                'reference_number': f"TXN{random.randint(100000000, 999999999)}",
                'status': random.choices(['COMPLETED', 'PENDING', 'FAILED', 'CANCELLED'], weights=[85, 8, 5, 2])[0],
                'fee_amount': amount * Decimal('0.001') if amount > 1000000 else Decimal('0'),
                'exchange_rate': Decimal('1.0000'),
                'channel': random.choice(channels),
                'device_id': random.choice([d['device_id'] for d in self.devices if d['customer_id'] == from_account['customer_id']]),
                'auth_method': auth_method,
                'risk_score': risk_score,
                'is_high_risk': is_high_risk,
                'requires_strong_auth': requires_strong_auth,
                'merchant_code': f"MCH{random.randint(1000, 9999)}" if random.random() > 0.5 else None,
                'merchant_name': fake.company() if random.random() > 0.5 else None,
                'created_at': datetime.now(),

                'completed_at': fake.date_time_between(start_date='-90d', end_date='now') if random.random() > 0.1 else None,
                'processed_by': 'SYSTEM'
            }
            
            try:
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, from_account_id, to_account_id, transaction_type, amount,
                        currency, description, reference_number, status, fee_amount, exchange_rate,
                        channel, device_id, auth_method, risk_score, is_high_risk, requires_strong_auth,
                        merchant_code, merchant_name, created_at, completed_at, processed_by
                    ) VALUES (
                        %(transaction_id)s, %(from_account_id)s, %(to_account_id)s, %(transaction_type)s, %(amount)s,
                        %(currency)s, %(description)s, %(reference_number)s, %(status)s, %(fee_amount)s, %(exchange_rate)s,
                        %(channel)s, %(device_id)s, %(auth_method)s, %(risk_score)s, %(is_high_risk)s, %(requires_strong_auth)s,
                        %(merchant_code)s, %(merchant_name)s, %(created_at)s, %(completed_at)s, %(processed_by)s
                    )
                """, transaction_data)
                
                if (i + 1) % 5000 == 0:
                    logger.info(f"Generated {i + 1} transactions")
                    
            except psycopg2.IntegrityError:
                continue
        
        logger.info(f"Successfully generated {count} transactions")
    
    def generate_daily_summaries(self):
        """Generate daily summaries for monitoring"""
        logger.info("Generating daily summaries...")
        
        cursor = self.conn.cursor()
        
        # Generate summaries for the last 90 days
        for days_back in range(90):
            summary_date = date.today() - timedelta(days=days_back)
            
            cursor.execute("""
                INSERT INTO daily_summaries (
                    customer_id, summary_date, total_transactions, total_amount,
                    high_value_transactions, strong_auth_transactions, failed_transactions, risk_score_avg
                )
                SELECT 
                    ba.customer_id,
                    %s as summary_date,
                    COUNT(t.transaction_id) as total_transactions,
                    COALESCE(SUM(t.amount), 0) as total_amount,
                    COUNT(CASE WHEN t.amount > 10000000 THEN 1 END) as high_value_transactions,
                    COUNT(CASE WHEN t.auth_method IN ('BIOMETRIC', 'OTP_SMS', 'OTP_EMAIL') THEN 1 END) as strong_auth_transactions,
                    COUNT(CASE WHEN t.status = 'FAILED' THEN 1 END) as failed_transactions,
                    COALESCE(AVG(t.risk_score), 0) as risk_score_avg
                FROM bank_accounts ba
                LEFT JOIN transactions t ON ba.account_id = t.from_account_id 
                    AND DATE(t.created_at) = %s
                GROUP BY ba.customer_id
                ON CONFLICT (customer_id, summary_date) DO UPDATE SET
                    total_transactions = EXCLUDED.total_transactions,
                    total_amount = EXCLUDED.total_amount,
                    high_value_transactions = EXCLUDED.high_value_transactions,
                    strong_auth_transactions = EXCLUDED.strong_auth_transactions,
                    failed_transactions = EXCLUDED.failed_transactions,
                    risk_score_avg = EXCLUDED.risk_score_avg
            """, (summary_date, summary_date))
        
        logger.info("Successfully generated daily summaries")
    
    def generate_all_data(self, customers=1000, transactions=50000, auth_logs=10000):
        """Generate all sample data"""
        logger.info("Starting data generation process...")
        
        try:
            self.connect()
            
            # Generate data in dependency order
            self.generate_customers(customers)
            self.generate_bank_accounts()
            self.generate_devices()
            self.generate_authentication_logs(auth_logs)
            self.generate_transactions(transactions)
            self.generate_daily_summaries()
            
            logger.info("Data generation completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during data generation: {e}")
            raise
        finally:
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(description='Generate sample data for TIMO Banking Platform')
    parser.add_argument('--customers', type=int, default=1000, help='Number of customers to generate')
    parser.add_argument('--transactions', type=int, default=50000, help='Number of transactions to generate')
    parser.add_argument('--auth-logs', type=int, default=10000, help='Number of authentication logs to generate')
    
    args = parser.parse_args()
    
    # Initialize database configuration
    db_config = DatabaseConfig()
    
    # Generate data
    generator = BankingDataGenerator(db_config)
    generator.generate_all_data(
        customers=args.customers,
        transactions=args.transactions,
        auth_logs=args.auth_logs
    )

if __name__ == "__main__":
    main()
