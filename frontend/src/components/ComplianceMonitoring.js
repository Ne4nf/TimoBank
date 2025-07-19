import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Progress, Alert, Spin, Typography, Tag, Divider } from 'antd';
import { 
  SafetyCertificateOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  CloseCircleOutlined,
  UserOutlined,
  MobileOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title } = Typography;

const ComplianceMonitoring = () => {
  const [complianceMetrics, setComplianceMetrics] = useState([]);
  const [customerProfiles, setCustomerProfiles] = useState([]);
  const [unverifiedDevices, setUnverifiedDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadComplianceData();
    // Refresh every 60 seconds
    const interval = setInterval(loadComplianceData, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadComplianceData = async () => {
    try {
      setLoading(true);
      
      const [metricsResponse, profilesResponse, devicesResponse] = await Promise.all([
        apiService.getComplianceMetrics(),
        apiService.getCustomerRiskProfiles(50),
        apiService.getUnverifiedDevices()
      ]);

      setComplianceMetrics(metricsResponse.data);
      setCustomerProfiles(profilesResponse.data);
      setUnverifiedDevices(devicesResponse.data);
      setError(null);
    } catch (err) {
      setError('Failed to load compliance data');
      console.error('Compliance monitoring error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'GOOD':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'WARNING':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'CRITICAL':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return null;
    }
  };

  const getRiskLevelTag = (riskLevel) => {
    const colors = {
      LOW: 'green',
      MEDIUM: 'orange',
      HIGH: 'red'
    };
    return <Tag color={colors[riskLevel]}>{riskLevel}</Tag>;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  // Customer profiles table columns
  const customerColumns = [
    {
      title: 'Customer',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (name, record) => (
        <div>
          <div><strong>{name}</strong></div>
          <div style={{ fontSize: 12, color: '#666' }}>ID: {record.customer_id.slice(0, 8)}...</div>
        </div>
      ),
    },
    {
      title: 'Risk Level',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level) => getRiskLevelTag(level),
      filters: [
        { text: 'Low', value: 'LOW' },
        { text: 'Medium', value: 'MEDIUM' },
        { text: 'High', value: 'HIGH' },
      ],
      onFilter: (value, record) => record.risk_level === value,
    },
    {
      title: 'Transactions',
      dataIndex: 'total_transactions',
      key: 'total_transactions',
      sorter: (a, b) => a.total_transactions - b.total_transactions,
    },
    {
      title: 'Total Amount',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (amount) => formatCurrency(amount),
      sorter: (a, b) => a.total_amount - b.total_amount,
    },
    {
      title: 'Unverified Devices',
      dataIndex: 'unverified_devices',
      key: 'unverified_devices',
      render: (count) => (
        <span style={{ color: count > 0 ? '#ff4d4f' : '#52c41a' }}>
          {count}
        </span>
      ),
      sorter: (a, b) => a.unverified_devices - b.unverified_devices,
    },
    {
      title: 'Recent Alerts',
      dataIndex: 'recent_alerts',
      key: 'recent_alerts',
      render: (count) => (
        <span style={{ color: count > 0 ? '#ff4d4f' : '#52c41a' }}>
          {count}
        </span>
      ),
      sorter: (a, b) => a.recent_alerts - b.recent_alerts,
    },
  ];

  // Unverified devices table columns
  const deviceColumns = [
    {
      title: 'Customer',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (name, record) => (
        <div>
          <div><strong>{name}</strong></div>
          <div style={{ fontSize: 12, color: '#666' }}>CCCD: {record.cccd_number}</div>
        </div>
      ),
    },
    {
      title: 'Unverified Devices',
      dataIndex: 'unverified_device_count',
      key: 'unverified_device_count',
      render: (count) => (
        <Tag color="red" icon={<MobileOutlined />}>
          {count} devices
        </Tag>
      ),
      sorter: (a, b) => a.unverified_device_count - b.unverified_device_count,
    },
    {
      title: 'Last Usage',
      dataIndex: 'last_unverified_usage',
      key: 'last_unverified_usage',
      render: (timestamp) => timestamp ? new Date(timestamp).toLocaleString() : 'N/A',
      sorter: (a, b) => new Date(a.last_unverified_usage || 0) - new Date(b.last_unverified_usage || 0),
    },
  ];

  if (loading && complianceMetrics.length === 0) {
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
            <button onClick={loadComplianceData} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
              Retry
            </button>
          }
        />
      </div>
    );
  }

  // Calculate overall compliance score
  const overallScore = complianceMetrics.length > 0 
    ? complianceMetrics.reduce((sum, metric) => sum + metric.percentage, 0) / complianceMetrics.length 
    : 0;

  const criticalMetrics = complianceMetrics.filter(m => m.status === 'CRITICAL');
  const warningMetrics = complianceMetrics.filter(m => m.status === 'WARNING');

  return (
    <div>
      <Title level={2}>
        <SafetyCertificateOutlined /> Compliance Monitoring
      </Title>

      {/* Overall Compliance Score */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Overall Compliance Score">
            <Progress
              percent={overallScore}
              status={
                overallScore >= 95 ? 'success' :
                overallScore >= 90 ? 'normal' : 'exception'
              }
              strokeColor={
                overallScore >= 95 ? '#52c41a' :
                overallScore >= 90 ? '#1890ff' : '#ff4d4f'
              }
              format={(percent) => `${percent?.toFixed(1)}%`}
            />
            <div style={{ marginTop: 8, color: '#666' }}>
              {overallScore >= 95 && "Excellent compliance across all metrics"}
              {overallScore >= 90 && overallScore < 95 && "Good compliance with minor issues"}
              {overallScore < 90 && "Compliance issues detected - immediate attention required"}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Compliance Alerts */}
      {criticalMetrics.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Alert
              message="Critical Compliance Issues"
              description={`${criticalMetrics.length} compliance metrics are in critical status and require immediate attention.`}
              type="error"
              showIcon
              closable
            />
          </Col>
        </Row>
      )}

      {warningMetrics.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Alert
              message="Compliance Warnings"
              description={`${warningMetrics.length} compliance metrics have warnings and should be reviewed.`}
              type="warning"
              showIcon
              closable
            />
          </Col>
        </Row>
      )}

      {/* Compliance Metrics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {complianceMetrics.map((metric, index) => (
          <Col xs={24} md={12} lg={8} key={index}>
            <Card 
              title={
                <span>
                  {getStatusIcon(metric.status)} {metric.metric_name}
                </span>
              }
              size="small"
            >
              <div className="metric-card">
                <Progress
                  percent={metric.percentage}
                  status={
                    metric.status === 'GOOD' ? 'success' :
                    metric.status === 'WARNING' ? 'normal' : 'exception'
                  }
                  strokeColor={
                    metric.status === 'GOOD' ? '#52c41a' :
                    metric.status === 'WARNING' ? '#faad14' : '#ff4d4f'
                  }
                  format={() => `${metric.value}/${metric.total}`}
                />
                <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                  {metric.percentage.toFixed(1)}% compliance rate
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Divider orientation="left">Customer Risk Analysis</Divider>

      {/* Customer Risk Profiles */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card 
            title={
              <span>
                <UserOutlined /> High-Risk Customer Profiles
              </span>
            }
          >
            <Table
              columns={customerColumns}
              dataSource={customerProfiles}
              rowKey="customer_id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} customers`,
              }}
              loading={loading}
              rowClassName={(record) => {
                if (record.risk_level === 'HIGH') return 'table-row-high';
                if (record.risk_level === 'MEDIUM') return 'table-row-medium';
                return 'table-row-low';
              }}
            />
          </Card>
        </Col>
      </Row>

      <Divider orientation="left">Device Verification</Divider>

      {/* Unverified Devices */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card 
            title={
              <span>
                <MobileOutlined /> Customers with Unverified Devices
              </span>
            }
            extra={
              <Tag color="orange">
                {unverifiedDevices.length} customers
              </Tag>
            }
          >
            {unverifiedDevices.length > 0 ? (
              <Table
                columns={deviceColumns}
                dataSource={unverifiedDevices}
                rowKey="customer_id"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `${range[0]}-${range[1]} of ${total} customers`,
                }}
                loading={loading}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: 40, color: '#52c41a' }}>
                <CheckCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>All customer devices are verified!</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <div style={{ textAlign: 'center', marginTop: 16, color: '#666', fontSize: 12 }}>
        Compliance data refreshed every 60 seconds | Last updated: {new Date().toLocaleString()}
      </div>
    </div>
  );
};

export default ComplianceMonitoring;
