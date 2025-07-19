import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Select, Spin, Typography, Alert } from 'antd';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { BarChartOutlined, RiseOutlined } from '@ant-design/icons';
import { apiService } from '../services/api';

const { Title } = Typography;
const { Option } = Select;

const TransactionAnalytics = () => {
  const [transactionData, setTransactionData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    loadTransactionData();
  }, [timeRange]);

  const loadTransactionData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getTransactionSummary(timeRange);
      setTransactionData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load transaction analytics');
      console.error('Transaction analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('vi-VN', {
      month: 'short',
      day: 'numeric'
    });
  };

  // Prepare chart data
  const chartData = transactionData.map(item => ({
    ...item,
    date_formatted: formatDate(item.date),
    total_amount_millions: item.total_amount / 1000000, // Convert to millions for readability
  }));

  // Risk distribution data for pie chart
  const totalTransactions = transactionData.reduce((sum, item) => sum + item.total_transactions, 0);
  const totalHighRisk = transactionData.reduce((sum, item) => sum + item.high_risk_count, 0);
  const totalHighValue = transactionData.reduce((sum, item) => sum + item.high_value_count, 0);

  const riskData = [
    { name: 'Normal Risk', value: totalTransactions - totalHighRisk, color: '#52c41a' },
    { name: 'High Risk', value: totalHighRisk, color: '#ff4d4f' },
  ];

  const valueData = [
    { name: 'Regular Value', value: totalTransactions - totalHighValue, color: '#1890ff' },
    { name: 'High Value (>10M)', value: totalHighValue, color: '#722ed1' },
  ];

  const COLORS = ['#52c41a', '#ff4d4f', '#1890ff', '#722ed1', '#faad14'];

  if (loading && transactionData.length === 0) {
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
            <button onClick={loadTransactionData} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
              Retry
            </button>
          }
        />
      </div>
    );
  }

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <BarChartOutlined /> Transaction Analytics
          </Title>
        </Col>
        <Col>
          <Select
            value={timeRange}
            onChange={setTimeRange}
            style={{ width: 200 }}
            loading={loading}
          >
            <Option value={7}>Last 7 days</Option>
            <Option value={14}>Last 14 days</Option>
            <Option value={30}>Last 30 days</Option>
            <Option value={60}>Last 60 days</Option>
            <Option value={90}>Last 90 days</Option>
          </Select>
        </Col>
      </Row>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#1890ff' }}>
                {totalTransactions.toLocaleString()}
              </div>
              <div className="metric-label">Total Transactions</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#52c41a' }}>
                {formatCurrency(transactionData.reduce((sum, item) => sum + item.total_amount, 0))}
              </div>
              <div className="metric-label">Total Volume</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#722ed1' }}>
                {totalHighValue.toLocaleString()}
              </div>
              <div className="metric-label">High-Value Transactions</div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={6}>
          <Card>
            <div className="metric-card">
              <div className="metric-value" style={{ color: '#ff4d4f' }}>
                {totalHighRisk.toLocaleString()}
              </div>
              <div className="metric-label">High-Risk Transactions</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Charts Row 1 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Transaction Volume Trend" extra={<RiseOutlined />}>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date_formatted" 
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `${value}M`}
                  />
                  <Tooltip 
                    formatter={(value) => [formatCurrency(value * 1000000), 'Volume']}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="total_amount_millions" 
                    stroke="#1890ff" 
                    fill="#1890ff" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Daily Transaction Count">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date_formatted" 
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value) => [value.toLocaleString(), 'Transactions']}
                  />
                  <Bar dataKey="total_transactions" fill="#52c41a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Charts Row 2 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Risk Score Trend">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date_formatted" 
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis 
                    domain={[0, 100]}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip 
                    formatter={(value) => [value?.toFixed(1), 'Avg Risk Score']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="avg_risk_score" 
                    stroke="#faad14" 
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="High-Value vs High-Risk Transactions">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date_formatted" 
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="high_value_count" fill="#722ed1" name="High Value" />
                  <Bar dataKey="high_risk_count" fill="#ff4d4f" name="High Risk" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Pie Charts Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Risk Distribution">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                  >
                    {riskData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [value.toLocaleString(), 'Transactions']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Value Distribution">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={valueData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                  >
                    {valueData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [value.toLocaleString(), 'Transactions']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      <div style={{ textAlign: 'center', marginTop: 16, color: '#666', fontSize: 12 }}>
        Data for the last {timeRange} days | Last updated: {new Date().toLocaleString()}
      </div>
    </div>
  );
};

export default TransactionAnalytics;
