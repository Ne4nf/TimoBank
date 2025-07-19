#!/usr/bin/env python3
"""
TIMO Banking Monitoring and Audit System
Implements real-time monitoring, fraud detection, and audit logging
"""

import os
import logging
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AlertEvent:
    """Alert event data structure"""
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    title: str
    description: str
    affected_entities: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class AuditLog:
    """Audit log entry"""
    event_type: str
    entity_type: str
    entity_id: str
    action: str
    details: Dict[str, Any]
    timestamp: datetime = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DatabaseConfig:
    """Database configuration"""
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB', 'timo_banking')
        self.username = os.getenv('POSTGRES_USER', 'postgres')
        self.password = os.getenv('POSTGRES_PASSWORD', 'tuthuc1411')

class MonitoringSystem:
    """Main monitoring and audit system"""
    
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.conn = None
        self.alerts = []
        self.audit_logs = []
        
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
    
    def add_alert(self, alert: AlertEvent):
        """Add an alert to the system"""
        self.alerts.append(alert)
        logger.warning(f"ALERT [{alert.severity}]: {alert.title} - {alert.description}")
        
        # Save alert to database
        self.save_alert_to_db(alert)
    
    def add_audit_log(self, audit_log: AuditLog):
        """Add an audit log entry"""
        self.audit_logs.append(audit_log)
        logger.info(f"AUDIT: {audit_log.event_type} - {audit_log.action} on {audit_log.entity_type} {audit_log.entity_id}")
    
    def save_alert_to_db(self, alert: AlertEvent):
        """Save alert to fraud_alerts table"""
        if not self.conn:
            return
            
        cursor = self.conn.cursor()
        
        try:
            # Extract customer_id and transaction_id from metadata if available
            customer_id = alert.metadata.get('customer_id')
            transaction_id = alert.metadata.get('transaction_id')
            
            cursor.execute("""
                INSERT INTO fraud_alerts (
                    transaction_id, customer_id, alert_type, severity, description,
                    status, created_at
                ) VALUES (%s, %s, %s, %s, %s, 'OPEN', %s)
            """, (
                transaction_id, customer_id, alert.alert_type, alert.severity,
                alert.description, alert.timestamp
            ))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")
            self.conn.rollback()
    
    def monitor_high_value_transactions(self, threshold: Decimal = Decimal('10000000')):
        """Monitor high-value transactions for compliance"""
        logger.info(f"Monitoring high-value transactions (> {threshold:,.0f} VND)...")
        
        cursor = self.conn.cursor()
        
        # Check transactions from the last hour
        cursor.execute("""
            SELECT 
                t.transaction_id,
                t.amount,
                t.auth_method,
                t.from_account_id,
                ba.customer_id,
                c.full_name,
                c.cccd_number,
                t.created_at
            FROM transactions t
            JOIN bank_accounts ba ON t.from_account_id = ba.account_id
            JOIN customers c ON ba.customer_id = c.customer_id
            WHERE t.amount > %s
            AND t.created_at >= %s
            AND t.status = 'COMPLETED'
            AND t.auth_method NOT IN ('BIOMETRIC', 'OTP_SMS', 'OTP_EMAIL')
        """, (threshold, datetime.now() - timedelta(hours=1)))
        
        non_compliant_transactions = cursor.fetchall()
        
        for txn in non_compliant_transactions:
            self.add_alert(AlertEvent(
                alert_type="COMPLIANCE_VIOLATION",
                severity="HIGH",
                title="High-value transaction without strong authentication",
                description=f"Transaction {txn['transaction_id']} of {txn['amount']:,.0f} VND by {txn['full_name']} used weak authentication: {txn['auth_method']}",
                affected_entities=[str(txn['transaction_id']), str(txn['customer_id'])],
                metadata={
                    'transaction_id': str(txn['transaction_id']),
                    'customer_id': str(txn['customer_id']),
                    'amount': float(txn['amount']),
                    'auth_method': txn['auth_method'],
                    'rule': 'High-value transactions must use strong authentication'
                }
            ))
    
    def monitor_suspicious_patterns(self):
        """Monitor for suspicious transaction patterns"""
        logger.info("Monitoring suspicious transaction patterns...")
        
        cursor = self.conn.cursor()
        
        # Pattern 1: Multiple high-value transactions in short time
        cursor.execute("""
            SELECT 
                ba.customer_id,
                c.full_name,
                COUNT(*) as transaction_count,
                SUM(t.amount) as total_amount,
                MIN(t.created_at) as first_txn,
                MAX(t.created_at) as last_txn
            FROM transactions t
            JOIN bank_accounts ba ON t.from_account_id = ba.account_id
            JOIN customers c ON ba.customer_id = c.customer_id
            WHERE t.amount > 5000000
            AND t.created_at >= %s
            AND t.status = 'COMPLETED'
            GROUP BY ba.customer_id, c.full_name
            HAVING COUNT(*) >= 5
            AND MAX(t.created_at) - MIN(t.created_at) <= INTERVAL '1 hour'
        """, (datetime.now() - timedelta(hours=2),))
        
        rapid_transactions = cursor.fetchall()
        
        for pattern in rapid_transactions:
            self.add_alert(AlertEvent(
                alert_type="SUSPICIOUS_PATTERN",
                severity="HIGH",
                title="Rapid high-value transactions detected",
                description=f"Customer {pattern['full_name']} made {pattern['transaction_count']} transactions totaling {pattern['total_amount']:,.0f} VND in {pattern['last_txn'] - pattern['first_txn']}",
                affected_entities=[str(pattern['customer_id'])],
                metadata={
                    'customer_id': str(pattern['customer_id']),
                    'transaction_count': pattern['transaction_count'],
                    'total_amount': float(pattern['total_amount']),
                    'time_span': str(pattern['last_txn'] - pattern['first_txn'])
                }
            ))
        
        # Pattern 2: Transactions from new/unverified devices
        cursor.execute("""
            SELECT 
                t.transaction_id,
                t.amount,
                ba.customer_id,
                c.full_name,
                d.device_fingerprint,
                d.verification_status,
                t.created_at
            FROM transactions t
            JOIN bank_accounts ba ON t.from_account_id = ba.account_id
            JOIN customers c ON ba.customer_id = c.customer_id
            JOIN devices d ON t.device_id = d.device_id
            WHERE d.verification_status = 'UNVERIFIED'
            AND t.amount > 1000000
            AND t.created_at >= %s
            AND t.status = 'COMPLETED'
        """, (datetime.now() - timedelta(hours=1),))
        
        unverified_device_txns = cursor.fetchall()
        
        for txn in unverified_device_txns:
            self.add_alert(AlertEvent(
                alert_type="DEVICE_RISK",
                severity="MEDIUM",
                title="Transaction from unverified device",
                description=f"Transaction {txn['transaction_id']} of {txn['amount']:,.0f} VND from unverified device by {txn['full_name']}",
                affected_entities=[str(txn['transaction_id']), str(txn['customer_id'])],
                metadata={
                    'transaction_id': str(txn['transaction_id']),
                    'customer_id': str(txn['customer_id']),
                    'amount': float(txn['amount']),
                    'device_fingerprint': txn['device_fingerprint']
                }
            ))
    
    def monitor_authentication_failures(self):
        """Monitor authentication failure patterns"""
        logger.info("Monitoring authentication failures...")
        
        cursor = self.conn.cursor()
        
        # Check for excessive failed login attempts
        cursor.execute("""
            SELECT 
                al.customer_id,
                c.full_name,
                COUNT(*) as failed_attempts,
                MAX(al.created_at) as last_attempt
            FROM authentication_logs al
            JOIN customers c ON al.customer_id = c.customer_id
            WHERE al.auth_status = 'FAILED'
            AND al.created_at >= %s
            GROUP BY al.customer_id, c.full_name
            HAVING COUNT(*) >= 5
        """, (datetime.now() - timedelta(hours=1),))
        
        excessive_failures = cursor.fetchall()
        
        for failure in excessive_failures:
            self.add_alert(AlertEvent(
                alert_type="AUTH_FAILURE",
                severity="HIGH",
                title="Excessive authentication failures",
                description=f"Customer {failure['full_name']} had {failure['failed_attempts']} failed authentication attempts in the last hour",
                affected_entities=[str(failure['customer_id'])],
                metadata={
                    'customer_id': str(failure['customer_id']),
                    'failed_attempts': failure['failed_attempts'],
                    'last_attempt': failure['last_attempt'].isoformat()
                }
            ))
    
    def monitor_daily_limits(self):
        """Monitor daily transaction limits"""
        logger.info("Monitoring daily transaction limits...")
        
        cursor = self.conn.cursor()
        
        # Check customers approaching or exceeding daily limits
        cursor.execute("""
            SELECT 
                ds.customer_id,
                c.full_name,
                ds.total_amount,
                ba.daily_limit,
                (ds.total_amount / ba.daily_limit * 100) as usage_percentage,
                ds.strong_auth_transactions
            FROM daily_summaries ds
            JOIN customers c ON ds.customer_id = c.customer_id
            JOIN bank_accounts ba ON c.customer_id = ba.customer_id
            WHERE ds.summary_date = CURRENT_DATE
            AND ds.total_amount > (ba.daily_limit * 0.9)  -- 90% of limit
        """)
        
        limit_warnings = cursor.fetchall()
        
        for warning in limit_warnings:
            severity = "CRITICAL" if warning['total_amount'] > warning['daily_limit'] else "HIGH"
            status = "exceeded" if warning['total_amount'] > warning['daily_limit'] else "approaching"
            
            self.add_alert(AlertEvent(
                alert_type="LIMIT_WARNING",
                severity=severity,
                title=f"Daily limit {status}",
                description=f"Customer {warning['full_name']} has used {warning['usage_percentage']:.1f}% of daily limit ({warning['total_amount']:,.0f} / {warning['daily_limit']:,.0f} VND)",
                affected_entities=[str(warning['customer_id'])],
                metadata={
                    'customer_id': str(warning['customer_id']),
                    'total_amount': float(warning['total_amount']),
                    'daily_limit': float(warning['daily_limit']),
                    'usage_percentage': float(warning['usage_percentage']),
                    'strong_auth_count': warning['strong_auth_transactions']
                }
            ))
    
    def monitor_risk_scores(self):
        """Monitor transaction risk scores"""
        logger.info("Monitoring transaction risk scores...")
        
        cursor = self.conn.cursor()
        
        # Check for high-risk transactions
        cursor.execute("""
            SELECT 
                t.transaction_id,
                t.amount,
                t.risk_score,
                ba.customer_id,
                c.full_name,
                t.created_at
            FROM transactions t
            JOIN bank_accounts ba ON t.from_account_id = ba.account_id
            JOIN customers c ON ba.customer_id = c.customer_id
            WHERE t.risk_score > 80
            AND t.created_at >= %s
            AND t.status = 'COMPLETED'
        """, (datetime.now() - timedelta(hours=1),))
        
        high_risk_transactions = cursor.fetchall()
        
        for txn in high_risk_transactions:
            self.add_alert(AlertEvent(
                alert_type="HIGH_RISK_TRANSACTION",
                severity="HIGH",
                title="High-risk transaction detected",
                description=f"Transaction {txn['transaction_id']} by {txn['full_name']} has risk score {txn['risk_score']} (amount: {txn['amount']:,.0f} VND)",
                affected_entities=[str(txn['transaction_id']), str(txn['customer_id'])],
                metadata={
                    'transaction_id': str(txn['transaction_id']),
                    'customer_id': str(txn['customer_id']),
                    'risk_score': txn['risk_score'],
                    'amount': float(txn['amount'])
                }
            ))
    
    def check_system_health(self):
        """Check overall system health metrics"""
        logger.info("Checking system health...")
        
        cursor = self.conn.cursor()
        
        # Check transaction processing rates
        cursor.execute("""
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending
            FROM transactions
            WHERE created_at >= %s
        """, (datetime.now() - timedelta(hours=1),))
        
        health_stats = cursor.fetchone()
        
        if health_stats['total_transactions'] > 0:
            failure_rate = (health_stats['failed'] / health_stats['total_transactions']) * 100
            pending_rate = (health_stats['pending'] / health_stats['total_transactions']) * 100
            
            if failure_rate > 5:  # More than 5% failure rate
                self.add_alert(AlertEvent(
                    alert_type="SYSTEM_HEALTH",
                    severity="HIGH",
                    title="High transaction failure rate",
                    description=f"Transaction failure rate is {failure_rate:.2f}% in the last hour ({health_stats['failed']}/{health_stats['total_transactions']})",
                    affected_entities=[],
                    metadata={
                        'failure_rate': failure_rate,
                        'failed_count': health_stats['failed'],
                        'total_count': health_stats['total_transactions']
                    }
                ))
            
            if pending_rate > 10:  # More than 10% pending rate
                self.add_alert(AlertEvent(
                    alert_type="SYSTEM_HEALTH",
                    severity="MEDIUM",
                    title="High pending transaction rate",
                    description=f"Pending transaction rate is {pending_rate:.2f}% in the last hour ({health_stats['pending']}/{health_stats['total_transactions']})",
                    affected_entities=[],
                    metadata={
                        'pending_rate': pending_rate,
                        'pending_count': health_stats['pending'],
                        'total_count': health_stats['total_transactions']
                    }
                ))
    
    def generate_audit_trail(self, entity_type: str = None, start_date: date = None, end_date: date = None):
        """Generate audit trail report"""
        logger.info("Generating audit trail...")
        
        cursor = self.conn.cursor()
        
        # Generate audit logs for important events
        if start_date is None:
            start_date = date.today() - timedelta(days=1)
        if end_date is None:
            end_date = date.today()
        
        # Audit high-value transactions
        cursor.execute("""
            SELECT 
                t.transaction_id,
                t.amount,
                t.transaction_type,
                t.status,
                ba.customer_id,
                c.full_name,
                t.created_at,
                t.processed_by
            FROM transactions t
            JOIN bank_accounts ba ON t.from_account_id = ba.account_id
            JOIN customers c ON ba.customer_id = c.customer_id
            WHERE t.amount > 10000000
            AND DATE(t.created_at) BETWEEN %s AND %s
            ORDER BY t.created_at DESC
        """, (start_date, end_date))
        
        high_value_txns = cursor.fetchall()
        
        for txn in high_value_txns:
            self.add_audit_log(AuditLog(
                event_type="HIGH_VALUE_TRANSACTION",
                entity_type="TRANSACTION",
                entity_id=str(txn['transaction_id']),
                action=f"{txn['transaction_type']} - {txn['status']}",
                details={
                    'amount': float(txn['amount']),
                    'customer_id': str(txn['customer_id']),
                    'customer_name': txn['full_name'],
                    'processed_by': txn['processed_by']
                },
                timestamp=txn['created_at']
            ))
        
        # Audit authentication events
        cursor.execute("""
            SELECT 
                al.auth_id,
                al.customer_id,
                c.full_name,
                al.auth_method,
                al.auth_status,
                al.created_at,
                al.risk_score
            FROM authentication_logs al
            JOIN customers c ON al.customer_id = c.customer_id
            WHERE DATE(al.created_at) BETWEEN %s AND %s
            AND (al.auth_status = 'FAILED' OR al.risk_score > 70)
            ORDER BY al.created_at DESC
        """, (start_date, end_date))
        
        auth_events = cursor.fetchall()
        
        for auth in auth_events:
            self.add_audit_log(AuditLog(
                event_type="AUTHENTICATION_EVENT",
                entity_type="AUTHENTICATION",
                entity_id=str(auth['auth_id']),
                action=f"{auth['auth_method']} - {auth['auth_status']}",
                details={
                    'customer_id': str(auth['customer_id']),
                    'customer_name': auth['full_name'],
                    'risk_score': auth['risk_score']
                },
                timestamp=auth['created_at']
            ))
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        logger.info("Starting monitoring cycle...")
        
        try:
            self.connect()
            
            # Run all monitoring checks
            self.monitor_high_value_transactions()
            self.monitor_suspicious_patterns()
            self.monitor_authentication_failures()
            self.monitor_daily_limits()
            self.monitor_risk_scores()
            self.check_system_health()
            
            # Generate audit trail
            self.generate_audit_trail()
            
            logger.info(f"Monitoring cycle completed. Generated {len(self.alerts)} alerts and {len(self.audit_logs)} audit logs")
            
        except Exception as e:
            logger.error(f"Error during monitoring cycle: {e}")
            raise
        finally:
            self.disconnect()
    
    def generate_monitoring_report(self, output_file: str = None):
        """Generate monitoring report"""
        if not self.alerts and not self.audit_logs:
            logger.warning("No alerts or audit logs to report")
            return
        
        # Count alerts by severity
        alert_counts = {}
        for alert in self.alerts:
            alert_counts[alert.severity] = alert_counts.get(alert.severity, 0) + 1
        
        report = {
            'monitoring_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_alerts': len(self.alerts),
                'alert_breakdown': alert_counts,
                'total_audit_logs': len(self.audit_logs)
            },
            'alerts': [],
            'audit_logs': []
        }
        
        # Add alerts
        for alert in self.alerts:
            report['alerts'].append({
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'description': alert.description,
                'affected_entities': alert.affected_entities,
                'metadata': alert.metadata,
                'timestamp': alert.timestamp.isoformat()
            })
        
        # Add audit logs
        for audit_log in self.audit_logs:
            report['audit_logs'].append({
                'event_type': audit_log.event_type,
                'entity_type': audit_log.entity_type,
                'entity_id': audit_log.entity_id,
                'action': audit_log.action,
                'details': audit_log.details,
                'timestamp': audit_log.timestamp.isoformat(),
                'user_id': audit_log.user_id
            })
        
        # Print summary
        print("\n" + "="*50)
        print("MONITORING & AUDIT REPORT")
        print("="*50)
        print(f"Total Alerts: {len(self.alerts)}")
        for severity, count in alert_counts.items():
            print(f"  {severity}: {count}")
        print(f"Total Audit Logs: {len(self.audit_logs)}")
        print("="*50)
        
        # Print critical and high alerts
        critical_high_alerts = [a for a in self.alerts if a.severity in ['CRITICAL', 'HIGH']]
        if critical_high_alerts:
            print("\nCRITICAL & HIGH SEVERITY ALERTS:")
            for alert in critical_high_alerts:
                print(f"🚨 [{alert.severity}] {alert.title}")
                print(f"   {alert.description}")
                print(f"   Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        
        print("\n")
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Monitoring report saved to {output_file}")
        
        return report

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run monitoring and audit for TIMO Banking Platform')
    parser.add_argument('--output', '-o', help='Output file for monitoring report (JSON format)')
    
    args = parser.parse_args()
    
    # Initialize database configuration
    db_config = DatabaseConfig()
    
    # Run monitoring cycle
    monitor = MonitoringSystem(db_config)
    monitor.run_monitoring_cycle()
    
    # Generate report
    monitor.generate_monitoring_report(args.output)

if __name__ == "__main__":
    main()
