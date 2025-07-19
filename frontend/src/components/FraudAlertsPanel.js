import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Alert, Spin, Typography, Select, Input, Badge } from 'antd';
import { 
  AlertOutlined, 
  ExclamationCircleOutlined, 
  WarningOutlined,
  BugOutlined,
  SearchOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title } = Typography;
const { Search } = Input;
const { Option } = Select;

const FraudAlertsPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    loadAlerts();
    // Refresh every 30 seconds
    const interval = setInterval(loadAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    filterAlerts();
  }, [alerts, severityFilter, statusFilter, searchText]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await apiService.getFraudAlerts({ limit: 100 });
      setAlerts(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load fraud alerts');
      console.error('Fraud alerts error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterAlerts = () => {
    let filtered = [...alerts];

    if (severityFilter) {
      filtered = filtered.filter(alert => alert.severity === severityFilter);
    }

    if (statusFilter) {
      filtered = filtered.filter(alert => alert.status === statusFilter);
    }

    if (searchText) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(alert => 
        alert.description.toLowerCase().includes(searchLower) ||
        alert.alert_type.toLowerCase().includes(searchLower)
      );
    }

    setFilteredAlerts(filtered);
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return <BugOutlined style={{ color: '#722ed1' }} />;
      case 'HIGH':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'MEDIUM':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'LOW':
        return <AlertOutlined style={{ color: '#52c41a' }} />;
      default:
        return <AlertOutlined />;
    }
  };

  const getSeverityTag = (severity) => {
    const colors = {
      CRITICAL: 'purple',
      HIGH: 'red',
      MEDIUM: 'orange',
      LOW: 'green'
    };
    return (
      <Tag color={colors[severity]} icon={getSeverityIcon(severity)}>
        {severity}
      </Tag>
    );
  };

  const getStatusTag = (status) => {
    const colors = {
      OPEN: 'red',
      INVESTIGATING: 'orange',
      RESOLVED: 'green',
      FALSE_POSITIVE: 'blue'
    };
    return <Tag color={colors[status]}>{status}</Tag>;
  };

  const getAlertTypeTag = (alertType) => {
    const colors = {
      COMPLIANCE_VIOLATION: 'red',
      SUSPICIOUS_PATTERN: 'orange',
      DEVICE_RISK: 'blue',
      AUTH_FAILURE: 'purple',
      LIMIT_WARNING: 'cyan',
      HIGH_RISK_TRANSACTION: 'magenta',
      SYSTEM_HEALTH: 'green'
    };
    return <Tag color={colors[alertType]}>{alertType.replace(/_/g, ' ')}</Tag>;
  };

  const columns = [
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity) => getSeverityTag(severity),
      width: 120,
      sorter: (a, b) => {
        const order = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
        return order[a.severity] - order[b.severity];
      },
    },
    {
      title: 'Type',
      dataIndex: 'alert_type',
      key: 'alert_type',
      render: (type) => getAlertTypeTag(type),
      width: 180,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => (
        <div title={text}>
          {text}
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusTag(status),
      width: 120,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (timestamp) => new Date(timestamp).toLocaleString(),
      width: 180,
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      defaultSortOrder: 'descend',
    },
  ];

  const alertCounts = {
    total: alerts.length,
    critical: alerts.filter(a => a.severity === 'CRITICAL').length,
    high: alerts.filter(a => a.severity === 'HIGH').length,
    open: alerts.filter(a => a.status === 'OPEN').length,
    investigating: alerts.filter(a => a.status === 'INVESTIGATING').length,
  };

  if (loading && alerts.length === 0) {
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
            <button onClick={loadAlerts} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
              Retry
            </button>
          }
        />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>
        <AlertOutlined /> Fraud Alerts
      </Title>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#1890ff' }}>
                <Badge count={alertCounts.total} style={{ backgroundColor: '#1890ff' }} />
              </div>
              <div className="metric-label">Total Alerts</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#722ed1' }}>
                <Badge count={alertCounts.critical} style={{ backgroundColor: '#722ed1' }} />
              </div>
              <div className="metric-label">Critical</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#ff4d4f' }}>
                <Badge count={alertCounts.high} style={{ backgroundColor: '#ff4d4f' }} />
              </div>
              <div className="metric-label">High Priority</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={12} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#faad14' }}>
                <Badge count={alertCounts.open + alertCounts.investigating} style={{ backgroundColor: '#faad14' }} />
              </div>
              <div className="metric-label">Active</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Critical Alerts Warning */}
      {alertCounts.critical > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Alert
              message="Critical Alerts Detected"
              description={`${alertCounts.critical} critical alerts require immediate attention.`}
              type="error"
              showIcon
              closable
            />
          </Col>
        </Row>
      )}

      {/* Filters */}
      <Card title={<><FilterOutlined /> Filters</>} style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="Filter by Severity"
              style={{ width: '100%' }}
              value={severityFilter}
              onChange={setSeverityFilter}
              allowClear
            >
              <Option value="CRITICAL">Critical</Option>
              <Option value="HIGH">High</Option>
              <Option value="MEDIUM">Medium</Option>
              <Option value="LOW">Low</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={8} md={6}>
            <Select
              placeholder="Filter by Status"
              style={{ width: '100%' }}
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
            >
              <Option value="OPEN">Open</Option>
              <Option value="INVESTIGATING">Investigating</Option>
              <Option value="RESOLVED">Resolved</Option>
              <Option value="FALSE_POSITIVE">False Positive</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={8} md={12}>
            <Search
              placeholder="Search alerts..."
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: '100%' }}
              prefix={<SearchOutlined />}
            />
          </Col>
        </Row>
      </Card>

      {/* Alerts Table */}
      <Card title={`Fraud Alerts (${filteredAlerts.length} of ${alerts.length})`}>
        <Table
          columns={columns}
          dataSource={filteredAlerts}
          rowKey="alert_id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} alerts`,
          }}
          loading={loading}
          rowClassName={(record) => {
            if (record.severity === 'CRITICAL') return 'table-row-critical';
            if (record.severity === 'HIGH') return 'table-row-high';
            if (record.severity === 'MEDIUM') return 'table-row-medium';
            return 'table-row-low';
          }}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: 16, backgroundColor: '#f9f9f9' }}>
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <strong>Alert ID:</strong> {record.alert_id}
                  </Col>
                  <Col span={12}>
                    <strong>Customer ID:</strong> {record.customer_id || 'N/A'}
                  </Col>
                  <Col span={12}>
                    <strong>Transaction ID:</strong> {record.transaction_id || 'N/A'}
                  </Col>
                  <Col span={12}>
                    <strong>Created:</strong> {new Date(record.created_at).toLocaleString()}
                  </Col>
                  <Col span={24}>
                    <strong>Full Description:</strong><br />
                    {record.description}
                  </Col>
                </Row>
              </div>
            ),
          }}
        />
      </Card>

      <div style={{ textAlign: 'center', marginTop: 16, color: '#666', fontSize: 12 }}>
        Auto-refresh every 30 seconds | Last updated: {new Date().toLocaleString()}
      </div>
    </div>
  );
};

export default FraudAlertsPanel;
