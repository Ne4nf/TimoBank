#!/usr/bin/env python3
"""
TIMO Banking Data Quality DAG
Airflow DAG for orchestrating daily data quality checks and monitoring
"""

from datetime import datetime, timedelta
import os
import logging
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago

# Add src directory to path for imports
sys.path.append('/opt/airflow/dags/src')

# Default arguments for the DAG
default_args = {
    'owner': 'timo-data-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email': ['data-team@timo.vn']
}

# DAG definition
dag = DAG(
    'timo_banking_data_quality',
    default_args=default_args,
    description='Daily data quality checks and monitoring for TIMO Banking Platform',
    schedule_interval='0 6 * * *',  # Run daily at 6 AM
    catchup=False,
    max_active_runs=1,
    tags=['timo', 'banking', 'data-quality', 'monitoring']
)

def check_database_connection():
    """Check if database is accessible"""
    logger = logging.getLogger(__name__)
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'timo_banking'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'tuthuc1411'),
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        result = cursor.fetchone()
        
        logger.info(f"Database connection successful. Found {result[0]} customers.")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def run_data_quality_checks():
    """Run comprehensive data quality checks"""
    logger = logging.getLogger(__name__)
    
    try:
        # Alternative implementation using direct SQL checks
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'timo_banking'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'tuthuc1411'),
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        # Run basic data quality checks
        quality_checks = {
            'null_customers': "SELECT COUNT(*) FROM customers WHERE full_name IS NULL OR cccd IS NULL",
            'invalid_accounts': "SELECT COUNT(*) FROM bank_accounts WHERE balance < 0",
            'orphaned_transactions': """
                SELECT COUNT(*) FROM transactions t 
                WHERE NOT EXISTS (SELECT 1 FROM bank_accounts ba WHERE ba.account_id = t.from_account_id)
            """,
            'duplicate_cccd': """
                SELECT COUNT(*) - COUNT(DISTINCT cccd) as duplicates FROM customers
            """
        }
        
        results = {}
        critical_failures = 0
        
        for check_name, query in quality_checks.items():
            cursor.execute(query)
            result = cursor.fetchone()
            count = result[0] if isinstance(result[0], int) else 0
            
            if count > 0:
                critical_failures += 1
                logger.warning(f"Data quality issue: {check_name} = {count}")
            
            results[check_name] = count
        
        cursor.close()
        conn.close()
        
        # Generate report
        output_file = f"/tmp/dq_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'critical_failures': critical_failures
            }, f, indent=2)
        
        if critical_failures > 0:
            logger.error(f"Data quality check failed with {critical_failures} critical issues")
            # Store the report path for the alert task
            with open('/tmp/dq_failure_report.txt', 'w') as f:
                f.write(output_file)
            raise Exception(f"Data quality check failed with {critical_failures} critical issues")
        else:
            logger.info("All data quality checks passed successfully")
            
        return results
        
    except Exception as e:
        logger.error(f"Data quality check failed: {e}")
        raise

def run_monitoring_checks():
    """Run monitoring and fraud detection"""
    logger = logging.getLogger(__name__)
    
    try:
        # Alternative implementation using direct SQL checks
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'timo_banking'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'tuthuc1411'),
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        # Run basic monitoring checks
        monitoring_checks = {
            'high_value_transactions': """
                SELECT COUNT(*) FROM transactions 
                WHERE amount > 1000000 AND created_at >= NOW() - INTERVAL '24 hours'
            """,
            'failed_transactions': """
                SELECT COUNT(*) FROM transactions 
                WHERE status = 'FAILED' AND created_at >= NOW() - INTERVAL '24 hours'
            """,
            'multiple_failures': """
                SELECT COUNT(*) FROM (
                    SELECT customer_id, COUNT(*) as failures
                    FROM transactions t
                    JOIN bank_accounts ba ON t.from_account_id = ba.account_id
                    WHERE t.status = 'FAILED' AND t.created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY customer_id
                    HAVING COUNT(*) > 3
                ) as suspicious_customers
            """,
            'unusual_patterns': """
                SELECT COUNT(*) FROM (
                    SELECT from_account_id, COUNT(*) as tx_count
                    FROM transactions
                    WHERE created_at >= NOW() - INTERVAL '1 hour'
                    GROUP BY from_account_id
                    HAVING COUNT(*) > 10
                ) as unusual_activity
            """
        }
        
        results = {}
        critical_alerts = 0
        
        for check_name, query in monitoring_checks.items():
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                count = result[0] if isinstance(result[0], int) else 0
                
                if count > 0:
                    critical_alerts += 1
                    logger.warning(f"Monitoring alert: {check_name} = {count}")
                
                results[check_name] = count
            except Exception as query_error:
                logger.warning(f"Could not execute {check_name}: {query_error}")
                results[check_name] = 0
        
        cursor.close()
        conn.close()
        
        # Generate report
        output_file = f"/tmp/monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'critical_alerts': critical_alerts
            }, f, indent=2)
        
        if critical_alerts > 0:
            logger.warning(f"Found {critical_alerts} critical/high severity alerts")
            # Store the report path for the alert task
            with open('/tmp/monitoring_alerts.txt', 'w') as f:
                f.write(output_file)
        else:
            logger.info("No critical alerts detected")
            
        return results
        
    except Exception as e:
        logger.error(f"Monitoring check failed: {e}")
        raise

def generate_daily_summaries():
    """Generate daily summaries for customers"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from datetime import date
    
    logger = logging.getLogger(__name__)
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'timo_banking'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'tuthuc1411'),
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        # Update daily summaries for yesterday
        yesterday = date.today() - timedelta(days=1)
        
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
                risk_score_avg = EXCLUDED.risk_score_avg,
                created_at = CURRENT_TIMESTAMP
        """, (yesterday, yesterday))
        
        conn.commit()
        
        # Get summary statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as customers_updated,
                SUM(total_transactions) as total_transactions,
                SUM(total_amount) as total_amount
            FROM daily_summaries
            WHERE summary_date = %s
        """, (yesterday,))
        
        stats = cursor.fetchone()
        
        logger.info(f"Updated daily summaries for {stats['customers_updated']} customers. "
                   f"Total transactions: {stats['total_transactions']}, "
                   f"Total amount: {stats['total_amount']:,.0f} VND")
        
        cursor.close()
        conn.close()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to generate daily summaries: {e}")
        raise

def cleanup_old_data():
    """Clean up old temporary data and logs"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import os
    import glob
    
    logger = logging.getLogger(__name__)
    
    try:
        # Clean up authentication logs older than 90 days
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'timo_banking'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'tuthuc1411'),
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        # Clean old authentication logs
        cursor.execute("""
            DELETE FROM authentication_logs
            WHERE created_at < CURRENT_DATE - INTERVAL '90 days'
        """)
        
        deleted_auth_logs = cursor.rowcount
        
        # Clean old resolved fraud alerts
        cursor.execute("""
            DELETE FROM fraud_alerts
            WHERE status = 'RESOLVED'
            AND resolved_at < CURRENT_DATE - INTERVAL '30 days'
        """)
        
        deleted_alerts = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Clean temporary files
        temp_files = glob.glob('/tmp/dq_report_*.json') + glob.glob('/tmp/monitoring_report_*.json')
        old_files = [f for f in temp_files if os.path.getmtime(f) < (datetime.now() - timedelta(days=7)).timestamp()]
        
        for file in old_files:
            os.remove(file)
        
        logger.info(f"Cleanup completed. Deleted {deleted_auth_logs} auth logs, "
                   f"{deleted_alerts} old alerts, and {len(old_files)} temp files")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        # Don't raise exception for cleanup failures

def send_failure_alert():
    """Send alert for data quality failures"""
    logger = logging.getLogger(__name__)
    
    try:
        # Check if there's a failure report
        if os.path.exists('/tmp/dq_failure_report.txt'):
            with open('/tmp/dq_failure_report.txt', 'r') as f:
                report_file = f.read().strip()
            
            with open(report_file, 'r') as f:
                import json
                report = json.load(f)
            
            failed_checks = [r for r in report['results'] if r['status'] == 'FAIL']
            
            subject = f"URGENT: Data Quality Failures Detected - {len(failed_checks)} issues"
            
            message = f"""
Data Quality Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CRITICAL DATA QUALITY ISSUES DETECTED:

Total Failed Checks: {len(failed_checks)}
Success Rate: {report['summary']['success_rate']}%

Failed Checks:
"""
            
            for check in failed_checks:
                message += f"\n❌ {check['check_name']}"
                message += f"\n   {check['message']}"
                message += f"\n   Affected Records: {check['affected_records']}\n"
            
            message += f"\nFull report available at: {report_file}"
            message += "\n\nPlease investigate and resolve these issues immediately."
            
            logger.error(subject)
            logger.error(message)
            
            # In a real environment, you would send an email or Slack notification here
            print(f"ALERT: {subject}")
            print(message)
            
    except Exception as e:
        logger.error(f"Failed to send failure alert: {e}")

# Task definitions
check_db_task = PythonOperator(
    task_id='check_database_connection',
    python_callable=check_database_connection,
    dag=dag
)

generate_summaries_task = PythonOperator(
    task_id='generate_daily_summaries',
    python_callable=generate_daily_summaries,
    dag=dag
)

data_quality_task = PythonOperator(
    task_id='run_data_quality_checks',
    python_callable=run_data_quality_checks,
    dag=dag
)

monitoring_task = PythonOperator(
    task_id='run_monitoring_checks',
    python_callable=run_monitoring_checks,
    dag=dag
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    dag=dag
)

failure_alert_task = PythonOperator(
    task_id='send_failure_alert',
    python_callable=send_failure_alert,
    dag=dag,
    trigger_rule='one_failed'  # Only run if a previous task failed
)

# Optional: Generate sample data (disabled by default)
generate_data_task = BashOperator(
    task_id='generate_sample_data',
    bash_command='cd /opt/airflow/dags/src && python generate_data.py --customers 100 --transactions 1000 --auth-logs 500',
    dag=dag
)

# Task dependencies
check_db_task >> generate_summaries_task
generate_summaries_task >> [data_quality_task, monitoring_task]
[data_quality_task, monitoring_task] >> cleanup_task
[data_quality_task, monitoring_task] >> failure_alert_task

# Optional: Uncomment to enable daily data generation
# check_db_task >> generate_data_task
# generate_data_task >> generate_summaries_task

if __name__ == "__main__":
    dag.cli()
