import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Alert, Spin, Typography, Progress, Badge } from 'antd';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  CloseCircleOutlined,
  SafetyOutlined 
} from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title } = Typography;

const DataQualityPanel = () => {
  const [qualityData, setQualityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDataQuality();
    // Refresh every 60 seconds
    const interval = setInterval(loadDataQuality, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadDataQuality = async () => {
    try {
      setLoading(true);
      const response = await apiService.getDataQualitySummary();
      setQualityData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load data quality information');
      console.error('Data quality error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'PASS':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'WARNING':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'FAIL':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return null;
    }
  };

  const getStatusTag = (status) => {
    const colors = {
      PASS: 'success',
      WARNING: 'warning',
      FAIL: 'error'
    };
    return <Tag color={colors[status]}>{status}</Tag>;
  };

  const columns = [
    {
      title: 'Check Name',
      dataIndex: 'check_name',
      key: 'check_name',
      render: (text) => <strong>{text.replace(/_/g, ' ').toUpperCase()}</strong>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <span>
          {getStatusIcon(status)} {getStatusTag(status)}
        </span>
      ),
      filters: [
        { text: 'Pass', value: 'PASS' },
        { text: 'Warning', value: 'WARNING' },
        { text: 'Fail', value: 'FAIL' },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: 'Affected Records',
      dataIndex: 'affected_records',
      key: 'affected_records',
      render: (count) => (
        <Badge 
          count={count} 
          style={{ backgroundColor: count > 0 ? '#ff4d4f' : '#52c41a' }}
        />
      ),
      sorter: (a, b) => a.affected_records - b.affected_records,
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => new Date(timestamp).toLocaleString(),
      sorter: (a, b) => new Date(a.timestamp) - new Date(b.timestamp),
    },
  ];

  if (loading && !qualityData) {
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
            <button onClick={loadDataQuality} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
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
        <SafetyOutlined /> Data Quality Monitoring
      </Title>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#1890ff' }}>
                {qualityData?.total_checks || 0}
              </div>
              <div className="metric-label">Total Checks</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#52c41a' }}>
                {qualityData?.passed || 0}
              </div>
              <div className="metric-label">Passed</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#ff4d4f' }}>
                {qualityData?.failed || 0}
              </div>
              <div className="metric-label">Failed</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#faad14' }}>
                {qualityData?.warnings || 0}
              </div>
              <div className="metric-label">Warnings</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Success Rate Progress */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Data Quality Score">
            <Progress
              percent={qualityData?.success_rate || 0}
              status={
                (qualityData?.success_rate || 0) >= 95 ? 'success' :
                (qualityData?.success_rate || 0) >= 90 ? 'normal' : 'exception'
              }
              strokeColor={
                (qualityData?.success_rate || 0) >= 95 ? '#52c41a' :
                (qualityData?.success_rate || 0) >= 90 ? '#1890ff' : '#ff4d4f'
              }
              format={(percent) => `${percent?.toFixed(1)}%`}
            />
            <div style={{ marginTop: 8, color: '#666' }}>
              {(qualityData?.success_rate || 0) >= 95 && "Excellent data quality"}
              {(qualityData?.success_rate || 0) >= 90 && (qualityData?.success_rate || 0) < 95 && "Good data quality"}
              {(qualityData?.success_rate || 0) < 90 && "Data quality needs attention"}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Alerts for Failed Checks */}
      {qualityData?.failed > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Alert
              message="Data Quality Issues Detected"
              description={`${qualityData.failed} data quality checks have failed. Please review and address these issues.`}
              type="error"
              showIcon
              closable
            />
          </Col>
        </Row>
      )}

      {qualityData?.warnings > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Alert
              message="Data Quality Warnings"
              description={`${qualityData.warnings} data quality checks have warnings. Consider reviewing these items.`}
              type="warning"
              showIcon
              closable
            />
          </Col>
        </Row>
      )}

      {/* Detailed Results Table */}
      <Card title="Detailed Quality Check Results">
        <Table
          columns={columns}
          dataSource={qualityData?.checks || []}
          rowKey="check_name"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} checks`,
          }}
          loading={loading}
          rowClassName={(record) => {
            if (record.status === 'FAIL') return 'table-row-fail';
            if (record.status === 'WARNING') return 'table-row-warning';
            return 'table-row-pass';
          }}
        />
      </Card>

      <div style={{ textAlign: 'center', marginTop: 16, color: '#666', fontSize: 12 }}>
        Last updated: {qualityData?.last_updated ? new Date(qualityData.last_updated).toLocaleString() : 'Unknown'}
      </div>
    </div>
  );
};

export default DataQualityPanel;
