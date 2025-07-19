-- TIMO Banking Data Platform Schema
-- Compliant with 2345/QĐ-NHNN 2023 regulatory requirements

-- Enable UUID extension for better security
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Customers table - Identity verification and KYC
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cccd_number VARCHAR(12) UNIQUE NOT NULL, -- Vietnam CCCD format
    passport_number VARCHAR(20) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    address TEXT NOT NULL,
    kyc_status VARCHAR(20) DEFAULT 'PENDING' CHECK (kyc_status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    risk_level VARCHAR(10) DEFAULT 'LOW' CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Bank accounts table
CREATE TABLE bank_accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('CHECKING', 'SAVINGS', 'CREDIT')),
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'VND',
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')),
    daily_limit DECIMAL(15,2) DEFAULT 20000000, -- 20M VND default daily limit
    monthly_limit DECIMAL(15,2) DEFAULT 500000000, -- 500M VND default monthly limit
    opened_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Devices table - Track customer devices for security
CREATE TABLE devices (
    device_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    device_fingerprint VARCHAR(255) UNIQUE NOT NULL,
    device_type VARCHAR(50) NOT NULL, -- MOBILE, WEB, ATM
    device_os VARCHAR(50),
    device_model VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    is_trusted BOOLEAN DEFAULT FALSE,
    last_used_at TIMESTAMP,
    verification_status VARCHAR(20) DEFAULT 'UNVERIFIED' CHECK (verification_status IN ('VERIFIED', 'UNVERIFIED', 'SUSPICIOUS')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Authentication logs table - Track OTP and biometric authentication
CREATE TABLE authentication_logs (
    auth_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    device_id UUID REFERENCES devices(device_id),
    auth_method VARCHAR(20) NOT NULL CHECK (auth_method IN ('PASSWORD', 'OTP_SMS', 'OTP_EMAIL', 'BIOMETRIC', 'PIN')),
    auth_status VARCHAR(20) NOT NULL CHECK (auth_status IN ('SUCCESS', 'FAILED', 'EXPIRED')),
    ip_address INET,
    location_data JSONB,
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    failed_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment transactions table
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_account_id UUID REFERENCES bank_accounts(account_id),
    to_account_id UUID REFERENCES bank_accounts(account_id),
    transaction_type VARCHAR(30) NOT NULL CHECK (transaction_type IN ('TRANSFER', 'DEPOSIT', 'WITHDRAWAL', 'PAYMENT', 'REFUND')),
    amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'VND',
    description TEXT,
    reference_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    fee_amount DECIMAL(15,2) DEFAULT 0.00,
    exchange_rate DECIMAL(10,4) DEFAULT 1.0000,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('ATM', 'ONLINE', 'MOBILE', 'BRANCH', 'CARD')),
    device_id UUID REFERENCES devices(device_id),
    auth_method VARCHAR(20) CHECK (auth_method IN ('PASSWORD', 'OTP_SMS', 'OTP_EMAIL', 'BIOMETRIC', 'PIN')),
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    is_high_risk BOOLEAN DEFAULT FALSE,
    requires_strong_auth BOOLEAN DEFAULT FALSE,
    merchant_code VARCHAR(50),
    merchant_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    processed_by VARCHAR(100)
);

-- Risk assessment table
CREATE TABLE risk_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID REFERENCES transactions(transaction_id),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    risk_factors JSONB,
    risk_score INTEGER NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    flags TEXT[],
    recommendations TEXT[],
    auto_decision VARCHAR(20) CHECK (auto_decision IN ('APPROVE', 'REJECT', 'REVIEW')),
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fraud detection alerts
CREATE TABLE fraud_alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID REFERENCES transactions(transaction_id),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE')),
    assigned_to VARCHAR(100),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily transaction summaries for monitoring
CREATE TABLE daily_summaries (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    summary_date DATE NOT NULL,
    total_transactions INTEGER DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0.00,
    high_value_transactions INTEGER DEFAULT 0,
    strong_auth_transactions INTEGER DEFAULT 0,
    failed_transactions INTEGER DEFAULT 0,
    risk_score_avg DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, summary_date)
);

-- Indexes for performance
CREATE INDEX idx_customers_cccd ON customers(cccd_number);
CREATE INDEX idx_customers_phone ON customers(phone_number);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_kyc_status ON customers(kyc_status);

CREATE INDEX idx_accounts_customer ON bank_accounts(customer_id);
CREATE INDEX idx_accounts_number ON bank_accounts(account_number);
CREATE INDEX idx_accounts_status ON bank_accounts(status);

CREATE INDEX idx_devices_customer ON devices(customer_id);
CREATE INDEX idx_devices_fingerprint ON devices(device_fingerprint);
CREATE INDEX idx_devices_trusted ON devices(is_trusted);

CREATE INDEX idx_auth_logs_customer ON authentication_logs(customer_id);
CREATE INDEX idx_auth_logs_device ON authentication_logs(device_id);
CREATE INDEX idx_auth_logs_method ON authentication_logs(auth_method);
CREATE INDEX idx_auth_logs_created ON authentication_logs(created_at);

CREATE INDEX idx_transactions_from_account ON transactions(from_account_id);
CREATE INDEX idx_transactions_to_account ON transactions(to_account_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created ON transactions(created_at);
CREATE INDEX idx_transactions_amount ON transactions(amount);
CREATE INDEX idx_transactions_high_risk ON transactions(is_high_risk);

CREATE INDEX idx_risk_assessments_transaction ON risk_assessments(transaction_id);
CREATE INDEX idx_risk_assessments_customer ON risk_assessments(customer_id);
CREATE INDEX idx_risk_assessments_level ON risk_assessments(risk_level);

CREATE INDEX idx_fraud_alerts_customer ON fraud_alerts(customer_id);
CREATE INDEX idx_fraud_alerts_status ON fraud_alerts(status);
CREATE INDEX idx_fraud_alerts_severity ON fraud_alerts(severity);

CREATE INDEX idx_daily_summaries_customer_date ON daily_summaries(customer_id, summary_date);

-- Triggers for updated_at fields
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON bank_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for reporting
CREATE VIEW high_risk_transactions AS
SELECT 
    t.transaction_id,
    t.amount,
    t.transaction_type,
    t.channel,
    t.auth_method,
    t.risk_score,
    c.full_name,
    c.cccd_number,
    t.created_at
FROM transactions t
JOIN bank_accounts ba ON t.from_account_id = ba.account_id
JOIN customers c ON ba.customer_id = c.customer_id
WHERE t.is_high_risk = TRUE OR t.risk_score > 70;

CREATE VIEW unverified_devices_summary AS
SELECT 
    c.customer_id,
    c.full_name,
    c.cccd_number,
    COUNT(d.device_id) as unverified_device_count,
    MAX(d.last_used_at) as last_unverified_usage
FROM customers c
LEFT JOIN devices d ON c.customer_id = d.customer_id
WHERE d.verification_status = 'UNVERIFIED'
GROUP BY c.customer_id, c.full_name, c.cccd_number
HAVING COUNT(d.device_id) > 0;

CREATE VIEW daily_compliance_summary AS
SELECT 
    ds.summary_date,
    COUNT(*) as total_customers,
    SUM(ds.total_transactions) as total_transactions,
    SUM(ds.total_amount) as total_amount,
    SUM(ds.high_value_transactions) as high_value_transactions,
    SUM(ds.strong_auth_transactions) as strong_auth_transactions,
    AVG(ds.risk_score_avg) as avg_risk_score
FROM daily_summaries ds
GROUP BY ds.summary_date
ORDER BY ds.summary_date DESC;
