import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Alert, Spin, Typography } from 'antd';
import {
  UserOutlined,
  TransactionOutlined,
  AlertOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title } = Typography;

const DashboardOverview = () => {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOverview();
    // Refresh every 30 seconds
    const interval = setInterval(loadOverview, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const response = await apiService.getDashboardOverview();
      setOverview(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard overview');
      console.error('Dashboard overview error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !overview) {
    return (
      <div className="loading-container">
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          action={
            <button onClick={loadOverview} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
              Retry
            </button>
          }
        />
      </div>
    );
  }

  const getStatusColor = (value, thresholds) => {
    if (value >= thresholds.good) return '#52c41a';
    if (value >= thresholds.warning) return '#faad14';
    return '#ff4d4f';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div>
      <Title level={2}>Dashboard Overview</Title>
      
      {loading && (
        <Alert
          message="Refreshing data..."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={[16, 16]}>
        {/* Key Metrics Row */}
        <Col xs={24} sm={12} md={6}>
          <Card className="dashboard-card">
            <Statistic
              title="Total Customers"
              value={overview?.total_customers || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card className="dashboard-card">
            <Statistic
              title="Today's Transactions"
              value={overview?.today_transactions || 0}
              prefix={<TransactionOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card className="dashboard-card">
            <Statistic
              title="Today's Volume"
              value={formatCurrency(overview?.today_volume || 0)}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card className="dashboard-card">
            <Statistic
              title="Active Alerts"
              value={overview?.active_alerts || 0}
              prefix={<AlertOutlined />}
              valueStyle={{ color: overview?.active_alerts > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* Quality & Compliance Row */}
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="Data Quality Score" 
            className="dashboard-card"
            extra={<SafetyOutlined />}
          >
            <div className="metric-card">
              <div 
                className="metric-value"
                style={{ 
                  color: getStatusColor(overview?.data_quality_score || 0, { good: 95, warning: 90 })
                }}
              >
                {(overview?.data_quality_score || 0).toFixed(1)}%
              </div>
              <div className="metric-label">
                {overview?.data_quality_score >= 95 ? (
                  <span className="status-good">
                    <CheckCircleOutlined /> Excellent
                  </span>
                ) : overview?.data_quality_score >= 90 ? (
                  <span className="status-warning">
                    <ExclamationCircleOutlined /> Good
                  </span>
                ) : (
                  <span className="status-critical">
                    <ExclamationCircleOutlined /> Needs Attention
                  </span>
                )}
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="Compliance Rate" 
            className="dashboard-card"
            extra={<CheckCircleOutlined />}
          >
            <div className="metric-card">
              <div 
                className="metric-value"
                style={{ 
                  color: getStatusColor(overview?.compliance_rate || 0, { good: 95, warning: 90 })
                }}
              >
                {(overview?.compliance_rate || 0).toFixed(1)}%
              </div>
              <div className="metric-label">
                High-value Auth Compliance
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="High-Risk Transactions" 
            className="dashboard-card"
            extra={<AlertOutlined />}
          >
            <div className="metric-card">
              <div 
                className="metric-value"
                style={{ 
                  color: overview?.high_risk_transactions > 10 ? '#ff4d4f' : 
                         overview?.high_risk_transactions > 5 ? '#faad14' : '#52c41a'
                }}
              >
                {overview?.high_risk_transactions || 0}
              </div>
              <div className="metric-label">
                Today's Count
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Alerts Section */}
      {overview?.active_alerts > 0 && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Alert
              message="Active Alerts Detected"
              description={`There are ${overview.active_alerts} active alerts that require attention. Please check the Fraud Alerts panel for details.`}
              type="warning"
              showIcon
              closable
            />
          </Col>
        </Row>
      )}

      {/* System Status */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="System Status" size="small">
            <Row gutter={16}>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                  <div>Database</div>
                  <div style={{ color: '#52c41a', fontSize: 12 }}>Connected</div>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                  <div>API</div>
                  <div style={{ color: '#52c41a', fontSize: 12 }}>Healthy</div>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                  <div>Monitoring</div>
                  <div style={{ color: '#52c41a', fontSize: 12 }}>Active</div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <div style={{ textAlign: 'center', marginTop: 16, color: '#666', fontSize: 12 }}>
        Last updated: {overview?.last_updated ? new Date(overview.last_updated).toLocaleString() : 'Unknown'}
      </div>
    </div>
  );
};

export default DashboardOverview;
