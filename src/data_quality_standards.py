#!/usr/bin/env python3
"""
TIMO Banking Data Quality Standards
Implements data quality checks and validation rules
"""

import os
import logging
import re
from datetime import datetime, date, timedelta
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DataQualityResult:
    """Data quality check result"""
    check_name: str
    status: str  # PASS, FAIL, WARNING
    message: str
    affected_records: int
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DatabaseConfig:
    """Database configuration"""
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'timo_banking')
        self.username = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')

class DataQualityChecker:
    """Main data quality checker class"""
    
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.conn = None
        self.results = []
        
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
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def add_result(self, result: DataQualityResult):
        """Add a data quality check result"""
        self.results.append(result)
        logger.info(f"{result.check_name}: {result.status} - {result.message}")
    
    def check_null_missing_values(self):
        """Check for null/missing values in critical fields"""
        logger.info("Checking for null/missing values...")
        
        cursor = self.conn.cursor()
        
        # Critical fields that should not be null
        checks = [
            {
                'table': 'customers',
                'fields': ['cccd_number', 'full_name', 'phone_number', 'email'],
                'description': 'Customer critical fields'
            },
            {
                'table': 'bank_accounts',
                'fields': ['account_number', 'customer_id', 'account_type'],
                'description': 'Bank account critical fields'
            },
            {
                'table': 'transactions',
                'fields': ['transaction_id', 'amount', 'transaction_type', 'reference_number'],
                'description': 'Transaction critical fields'
            }
        ]
        
        for check in checks:
            for field in check['fields']:
                cursor.execute(f"""
                    SELECT COUNT(*) as null_count
                    FROM {check['table']}
                    WHERE {field} IS NULL
                """)
                
                result = cursor.fetchone()
                null_count = result['null_count']
                
                if null_count > 0:
                    self.add_result(DataQualityResult(
                        check_name=f"null_check_{check['table']}_{field}",
                        status="FAIL",
                        message=f"Found {null_count} null values in {check['table']}.{field}",
                        affected_records=null_count,
                        details={'table': check['table'], 'field': field}
                    ))
                else:
                    self.add_result(DataQualityResult(
                        check_name=f"null_check_{check['table']}_{field}",
                        status="PASS",
                        message=f"No null values found in {check['table']}.{field}",
                        affected_records=0
                    ))
    
    def check_uniqueness_constraints(self):
        """Check uniqueness constraints"""
        logger.info("Checking uniqueness constraints...")
        
        cursor = self.conn.cursor()
        
        # Uniqueness checks
        uniqueness_checks = [
            {
                'table': 'customers',
                'field': 'cccd_number',
                'description': 'CCCD numbers should be unique'
            },
            {
                'table': 'customers',
                'field': 'phone_number',
                'description': 'Phone numbers should be unique'
            },
            {
                'table': 'customers',
                'field': 'email',
                'description': 'Email addresses should be unique'
            },
            {
                'table': 'bank_accounts',
                'field': 'account_number',
                'description': 'Account numbers should be unique'
            },
            {
                'table': 'transactions',
                'field': 'reference_number',
                'description': 'Transaction reference numbers should be unique'
            },
            {
                'table': 'devices',
                'field': 'device_fingerprint',
                'description': 'Device fingerprints should be unique'
            }
        ]
        
        for check in uniqueness_checks:
            cursor.execute(f"""
                SELECT {check['field']}, COUNT(*) as duplicate_count
                FROM {check['table']}
                WHERE {check['field']} IS NOT NULL
                GROUP BY {check['field']}
                HAVING COUNT(*) > 1
            """)
            
            duplicates = cursor.fetchall()
            duplicate_count = len(duplicates)
            
            if duplicate_count > 0:
                total_affected = sum(dup['duplicate_count'] for dup in duplicates)
                self.add_result(DataQualityResult(
                    check_name=f"uniqueness_{check['table']}_{check['field']}",
                    status="FAIL",
                    message=f"Found {duplicate_count} duplicate values in {check['table']}.{check['field']}",
                    affected_records=total_affected,
                    details={'duplicates': [dict(dup) for dup in duplicates[:10]]}  # Show first 10
                ))
            else:
                self.add_result(DataQualityResult(
                    check_name=f"uniqueness_{check['table']}_{check['field']}",
                    status="PASS",
                    message=f"All values unique in {check['table']}.{check['field']}",
                    affected_records=0
                ))
    
    def check_format_validation(self):
        """Check format and length validation"""
        logger.info("Checking format validation...")
        
        cursor = self.conn.cursor()
        
        # CCCD format validation (12 digits)
        cursor.execute("""
            SELECT COUNT(*) as invalid_count
            FROM customers
            WHERE cccd_number !~ '^[0-9]{12}$'
        """)
        
        result = cursor.fetchone()
        invalid_cccd = result['invalid_count']
        
        if invalid_cccd > 0:
            self.add_result(DataQualityResult(
                check_name="format_cccd_validation",
                status="FAIL",
                message=f"Found {invalid_cccd} invalid CCCD formats (should be 12 digits)",
                affected_records=invalid_cccd
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="format_cccd_validation",
                status="PASS",
                message="All CCCD numbers have valid format",
                affected_records=0
            ))
        
        # Phone number format validation (Vietnamese format)
        cursor.execute("""
            SELECT COUNT(*) as invalid_count
            FROM customers
            WHERE phone_number !~ '^(09|08|07|05|03)[0-9]{8}$'
        """)
        
        result = cursor.fetchone()
        invalid_phone = result['invalid_count']
        
        if invalid_phone > 0:
            self.add_result(DataQualityResult(
                check_name="format_phone_validation",
                status="FAIL",
                message=f"Found {invalid_phone} invalid phone number formats",
                affected_records=invalid_phone
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="format_phone_validation",
                status="PASS",
                message="All phone numbers have valid format",
                affected_records=0
            ))
        
        # Email format validation
        cursor.execute("""
            SELECT COUNT(*) as invalid_count
            FROM customers
            WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        """)
        
        result = cursor.fetchone()
        invalid_email = result['invalid_count']
        
        if invalid_email > 0:
            self.add_result(DataQualityResult(
                check_name="format_email_validation",
                status="FAIL",
                message=f"Found {invalid_email} invalid email formats",
                affected_records=invalid_email
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="format_email_validation",
                status="PASS",
                message="All email addresses have valid format",
                affected_records=0
            ))
    
    def check_foreign_key_integrity(self):
        """Check foreign key integrity"""
        logger.info("Checking foreign key integrity...")
        
        cursor = self.conn.cursor()
        
        # Bank accounts should reference existing customers
        cursor.execute("""
            SELECT COUNT(*) as orphaned_count
            FROM bank_accounts ba
            LEFT JOIN customers c ON ba.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """)
        
        result = cursor.fetchone()
        orphaned_accounts = result['orphaned_count']
        
        if orphaned_accounts > 0:
            self.add_result(DataQualityResult(
                check_name="fk_integrity_accounts_customers",
                status="FAIL",
                message=f"Found {orphaned_accounts} bank accounts without valid customer references",
                affected_records=orphaned_accounts
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="fk_integrity_accounts_customers",
                status="PASS",
                message="All bank accounts have valid customer references",
                affected_records=0
            ))
        
        # Transactions should reference existing accounts
        cursor.execute("""
            SELECT COUNT(*) as invalid_count
            FROM transactions t
            LEFT JOIN bank_accounts ba ON t.from_account_id = ba.account_id
            WHERE t.from_account_id IS NOT NULL AND ba.account_id IS NULL
        """)
        
        result = cursor.fetchone()
        invalid_transactions = result['invalid_count']
        
        if invalid_transactions > 0:
            self.add_result(DataQualityResult(
                check_name="fk_integrity_transactions_accounts",
                status="FAIL",
                message=f"Found {invalid_transactions} transactions with invalid account references",
                affected_records=invalid_transactions
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="fk_integrity_transactions_accounts",
                status="PASS",
                message="All transactions have valid account references",
                affected_records=0
            ))
        
        # Devices should reference existing customers
        cursor.execute("""
            SELECT COUNT(*) as orphaned_count
            FROM devices d
            LEFT JOIN customers c ON d.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """)
        
        result = cursor.fetchone()
        orphaned_devices = result['orphaned_count']
        
        if orphaned_devices > 0:
            self.add_result(DataQualityResult(
                check_name="fk_integrity_devices_customers",
                status="FAIL",
                message=f"Found {orphaned_devices} devices without valid customer references",
                affected_records=orphaned_devices
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="fk_integrity_devices_customers",
                status="PASS",
                message="All devices have valid customer references",
                affected_records=0
            ))
    
    def check_business_rules(self):
        """Check business rule compliance"""
        logger.info("Checking business rule compliance...")
        
        cursor = self.conn.cursor()
        
        # Check for negative balances (shouldn't exist for most account types)
        cursor.execute("""
            SELECT COUNT(*) as negative_count
            FROM bank_accounts
            WHERE balance < 0 AND account_type != 'CREDIT'
        """)
        
        result = cursor.fetchone()
        negative_balances = result['negative_count']
        
        if negative_balances > 0:
            self.add_result(DataQualityResult(
                check_name="business_rule_negative_balances",
                status="FAIL",
                message=f"Found {negative_balances} non-credit accounts with negative balances",
                affected_records=negative_balances
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="business_rule_negative_balances",
                status="PASS",
                message="No invalid negative balances found",
                affected_records=0
            ))
        
        # Check for future-dated transactions
        cursor.execute("""
            SELECT COUNT(*) as future_count
            FROM transactions
            WHERE DATE(created_at) > CURRENT_DATE
        """)
        
        result = cursor.fetchone()
        future_transactions = result['future_count']
        
        if future_transactions > 0:
            self.add_result(DataQualityResult(
                check_name="business_rule_future_transactions",
                status="FAIL",
                message=f"Found {future_transactions} transactions with future dates",
                affected_records=future_transactions
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="business_rule_future_transactions",
                status="PASS",
                message="No future-dated transactions found",
                affected_records=0
            ))
        
        # Check for customers with invalid age
        cursor.execute("""
            SELECT COUNT(*) as invalid_age_count
            FROM customers
            WHERE date_of_birth > CURRENT_DATE - INTERVAL '18 years'
            OR date_of_birth < CURRENT_DATE - INTERVAL '120 years'
        """)
        
        result = cursor.fetchone()
        invalid_age = result['invalid_age_count']
        
        if invalid_age > 0:
            self.add_result(DataQualityResult(
                check_name="business_rule_customer_age",
                status="FAIL",
                message=f"Found {invalid_age} customers with invalid age (< 18 or > 120 years)",
                affected_records=invalid_age
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="business_rule_customer_age",
                status="PASS",
                message="All customers have valid age",
                affected_records=0
            ))
    
    def check_compliance_rules(self):
        """Check regulatory compliance rules"""
        logger.info("Checking compliance rules...")
        
        cursor = self.conn.cursor()
        
        # Rule 1: Transactions > 10M VND must use strong authentication
        cursor.execute("""
            SELECT COUNT(*) as non_compliant_count
            FROM transactions
            WHERE amount > 10000000
            AND auth_method NOT IN ('BIOMETRIC', 'OTP_SMS', 'OTP_EMAIL')
            AND status = 'COMPLETED'
            AND created_at >= CURRENT_DATE - INTERVAL '30 days'
        """)
        
        result = cursor.fetchone()
        non_compliant_high_value = result['non_compliant_count']
        
        if non_compliant_high_value > 0:
            self.add_result(DataQualityResult(
                check_name="compliance_high_value_auth",
                status="FAIL",
                message=f"Found {non_compliant_high_value} high-value transactions without strong authentication",
                affected_records=non_compliant_high_value,
                details={'rule': 'Transactions > 10M VND must use strong auth (biometric or OTP)'}
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="compliance_high_value_auth",
                status="PASS",
                message="All high-value transactions use strong authentication",
                affected_records=0
            ))
        
        # Rule 2: New or untrusted devices must be verified
        cursor.execute("""
            SELECT COUNT(*) as unverified_count
            FROM devices d
            JOIN transactions t ON d.device_id = t.device_id
            WHERE d.verification_status = 'UNVERIFIED'
            AND d.is_trusted = FALSE
            AND t.created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY d.device_id
        """)
        
        unverified_devices = len(cursor.fetchall())
        
        if unverified_devices > 0:
            self.add_result(DataQualityResult(
                check_name="compliance_device_verification",
                status="WARNING",
                message=f"Found {unverified_devices} unverified devices used for recent transactions",
                affected_records=unverified_devices,
                details={'rule': 'New/untrusted devices should be verified before use'}
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="compliance_device_verification",
                status="PASS",
                message="All devices used for transactions are verified",
                affected_records=0
            ))
        
        # Rule 3: Customers with > 20M VND daily transactions must have strong auth
        cursor.execute("""
            SELECT ds.customer_id, ds.total_amount, ds.strong_auth_transactions
            FROM daily_summaries ds
            WHERE ds.summary_date >= CURRENT_DATE - INTERVAL '7 days'
            AND ds.total_amount > 20000000
            AND ds.strong_auth_transactions = 0
        """)
        
        non_compliant_daily = cursor.fetchall()
        non_compliant_daily_count = len(non_compliant_daily)
        
        if non_compliant_daily_count > 0:
            self.add_result(DataQualityResult(
                check_name="compliance_daily_limit_auth",
                status="FAIL",
                message=f"Found {non_compliant_daily_count} customers exceeding daily limits without strong auth",
                affected_records=non_compliant_daily_count,
                details={
                    'rule': 'Customers with > 20M VND daily transactions must use strong auth',
                    'violations': [dict(violation) for violation in non_compliant_daily[:5]]
                }
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="compliance_daily_limit_auth",
                status="PASS",
                message="All high-volume customers use strong authentication",
                affected_records=0
            ))
    
    def check_data_consistency(self):
        """Check data consistency across tables"""
        logger.info("Checking data consistency...")
        
        cursor = self.conn.cursor()
        
        # Check if daily summaries match actual transaction data
        cursor.execute("""
            SELECT 
                ds.customer_id,
                ds.summary_date,
                ds.total_amount as summary_amount,
                COALESCE(actual.actual_amount, 0) as actual_amount,
                ABS(ds.total_amount - COALESCE(actual.actual_amount, 0)) as difference
            FROM daily_summaries ds
            LEFT JOIN (
                SELECT 
                    ba.customer_id,
                    DATE(t.created_at) as transaction_date,
                    SUM(t.amount) as actual_amount
                FROM transactions t
                JOIN bank_accounts ba ON t.from_account_id = ba.account_id
                WHERE t.status = 'COMPLETED'
                GROUP BY ba.customer_id, DATE(t.created_at)
            ) actual ON ds.customer_id = actual.customer_id AND ds.summary_date = actual.transaction_date
            WHERE ABS(ds.total_amount - COALESCE(actual.actual_amount, 0)) > 1000
            AND ds.summary_date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        
        inconsistent_summaries = cursor.fetchall()
        inconsistent_count = len(inconsistent_summaries)
        
        if inconsistent_count > 0:
            self.add_result(DataQualityResult(
                check_name="consistency_daily_summaries",
                status="FAIL",
                message=f"Found {inconsistent_count} daily summaries with inconsistent amounts",
                affected_records=inconsistent_count,
                details={'inconsistencies': [dict(inc) for inc in inconsistent_summaries[:5]]}
            ))
        else:
            self.add_result(DataQualityResult(
                check_name="consistency_daily_summaries",
                status="PASS",
                message="Daily summaries are consistent with transaction data",
                affected_records=0
            ))
    
    def run_all_checks(self):
        """Run all data quality checks"""
        logger.info("Starting comprehensive data quality checks...")
        
        try:
            self.connect()
            
            # Run all checks
            self.check_null_missing_values()
            self.check_uniqueness_constraints()
            self.check_format_validation()
            self.check_foreign_key_integrity()
            self.check_business_rules()
            self.check_compliance_rules()
            self.check_data_consistency()
            
            logger.info("Data quality checks completed")
            
        except Exception as e:
            logger.error(f"Error during data quality checks: {e}")
            raise
        finally:
            self.disconnect()
    
    def generate_report(self, output_file: str = None):
        """Generate data quality report"""
        if not self.results:
            logger.warning("No results to report")
            return
        
        # Count results by status
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        warnings = len([r for r in self.results if r.status == "WARNING"])
        
        report = {
            'summary': {
                'total_checks': len(self.results),
                'passed': passed,
                'failed': failed,
                'warnings': warnings,
                'success_rate': round((passed / len(self.results)) * 100, 2),
                'timestamp': datetime.now().isoformat()
            },
            'results': []
        }
        
        # Add detailed results
        for result in self.results:
            report['results'].append({
                'check_name': result.check_name,
                'status': result.status,
                'message': result.message,
                'affected_records': result.affected_records,
                'timestamp': result.timestamp.isoformat(),
                'details': result.details
            })
        
        # Print summary
        print("\n" + "="*50)
        print("DATA QUALITY REPORT")
        print("="*50)
        print(f"Total Checks: {report['summary']['total_checks']}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Warnings: {warnings}")
        print(f"Success Rate: {report['summary']['success_rate']}%")
        print("="*50)
        
        # Print failed checks
        failed_results = [r for r in self.results if r.status == "FAIL"]
        if failed_results:
            print("\nFAILED CHECKS:")
            for result in failed_results:
                print(f"❌ {result.check_name}: {result.message}")
        
        # Print warnings
        warning_results = [r for r in self.results if r.status == "WARNING"]
        if warning_results:
            print("\nWARNINGS:")
            for result in warning_results:
                print(f"⚠️ {result.check_name}: {result.message}")
        
        print("\n")
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved to {output_file}")
        
        return report

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run data quality checks for TIMO Banking Platform')
    parser.add_argument('--output', '-o', help='Output file for detailed report (JSON format)')
    
    args = parser.parse_args()
    
    # Initialize database configuration
    db_config = DatabaseConfig()
    
    # Run data quality checks
    checker = DataQualityChecker(db_config)
    checker.run_all_checks()
    
    # Generate report
    checker.generate_report(args.output)

if __name__ == "__main__":
    main()
