-- Reporting queries for TIMO Banking Data Platform

-- 1. Daily transaction volume and risk analysis
SELECT 
    DATE(created_at) as transaction_date,
    COUNT(*) as total_transactions,
    SUM(amount) as total_volume,
    COUNT(CASE WHEN amount > 10000000 THEN 1 END) as high_value_count,
    COUNT(CASE WHEN is_high_risk = TRUE THEN 1 END) as high_risk_count,
    AVG(risk_score) as avg_risk_score
FROM transactions 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY transaction_date DESC;

-- 2. Customer risk profile analysis
SELECT 
    c.risk_level,
    COUNT(*) as customer_count,
    AVG(CASE WHEN ds.total_amount IS NOT NULL THEN ds.total_amount ELSE 0 END) as avg_daily_volume,
    COUNT(fa.alert_id) as total_alerts
FROM customers c
LEFT JOIN daily_summaries ds ON c.customer_id = ds.customer_id AND ds.summary_date = CURRENT_DATE
LEFT JOIN fraud_alerts fa ON c.customer_id = fa.customer_id AND fa.status IN ('OPEN', 'INVESTIGATING')
GROUP BY c.risk_level;

-- 3. Authentication method compliance check
SELECT 
    t.transaction_type,
    t.amount,
    t.auth_method,
    CASE 
        WHEN t.amount > 10000000 AND t.auth_method NOT IN ('BIOMETRIC', 'OTP_SMS', 'OTP_EMAIL') 
        THEN 'NON_COMPLIANT'
        ELSE 'COMPLIANT'
    END as compliance_status
FROM transactions t
WHERE t.amount > 10000000
ORDER BY t.created_at DESC;

-- 4. Device verification status by customer
SELECT 
    c.full_name,
    c.cccd_number,
    COUNT(d.device_id) as total_devices,
    COUNT(CASE WHEN d.verification_status = 'VERIFIED' THEN 1 END) as verified_devices,
    COUNT(CASE WHEN d.verification_status = 'UNVERIFIED' THEN 1 END) as unverified_devices,
    COUNT(CASE WHEN d.verification_status = 'SUSPICIOUS' THEN 1 END) as suspicious_devices
FROM customers c
LEFT JOIN devices d ON c.customer_id = d.customer_id
GROUP BY c.customer_id, c.full_name, c.cccd_number
ORDER BY unverified_devices DESC, suspicious_devices DESC;

-- 5. Monthly fraud detection summary
SELECT 
    DATE_TRUNC('month', fa.created_at) as month,
    fa.severity,
    COUNT(*) as alert_count,
    COUNT(CASE WHEN fa.status = 'RESOLVED' THEN 1 END) as resolved_count,
    COUNT(CASE WHEN fa.status = 'FALSE_POSITIVE' THEN 1 END) as false_positive_count
FROM fraud_alerts fa
WHERE fa.created_at >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', fa.created_at), fa.severity
ORDER BY month DESC, fa.severity;

-- 6. Daily transaction limit compliance
SELECT 
    c.customer_id,
    c.full_name,
    ds.summary_date,
    ds.total_amount,
    ba.daily_limit,
    CASE 
        WHEN ds.total_amount > ba.daily_limit THEN 'EXCEEDED'
        WHEN ds.total_amount > (ba.daily_limit * 0.8) THEN 'WARNING'
        ELSE 'NORMAL'
    END as limit_status,
    ds.strong_auth_transactions
FROM daily_summaries ds
JOIN customers c ON ds.customer_id = c.customer_id
JOIN bank_accounts ba ON c.customer_id = ba.customer_id
WHERE ds.summary_date >= CURRENT_DATE - INTERVAL '7 days'
AND (ds.total_amount > ba.daily_limit OR ds.total_amount > 20000000)
ORDER BY ds.summary_date DESC, ds.total_amount DESC;

-- 7. Top risky transactions requiring investigation
SELECT 
    t.transaction_id,
    t.reference_number,
    c.full_name,
    c.cccd_number,
    t.amount,
    t.transaction_type,
    t.channel,
    t.auth_method,
    t.risk_score,
    ra.risk_level,
    ra.flags,
    t.created_at
FROM transactions t
JOIN bank_accounts ba ON t.from_account_id = ba.account_id
JOIN customers c ON ba.customer_id = c.customer_id
LEFT JOIN risk_assessments ra ON t.transaction_id = ra.transaction_id
WHERE t.risk_score > 80 OR ra.risk_level IN ('HIGH', 'CRITICAL')
ORDER BY t.risk_score DESC, t.amount DESC
LIMIT 50;

-- 8. Authentication failure analysis
SELECT 
    DATE(al.created_at) as auth_date,
    al.auth_method,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN al.auth_status = 'SUCCESS' THEN 1 END) as successful_attempts,
    COUNT(CASE WHEN al.auth_status = 'FAILED' THEN 1 END) as failed_attempts,
    ROUND(
        (COUNT(CASE WHEN al.auth_status = 'FAILED' THEN 1 END) * 100.0 / COUNT(*)), 2
    ) as failure_rate_percent
FROM authentication_logs al
WHERE al.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(al.created_at), al.auth_method
ORDER BY auth_date DESC, failure_rate_percent DESC;
