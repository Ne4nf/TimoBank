import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography, theme } from 'antd';
import {
  DashboardOutlined,
  SafetyOutlined,
  AlertOutlined,
  BarChartOutlined,
  UserOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import DashboardOverview from './components/DashboardOverview';
import DataQualityPanel from './components/DataQualityPanel';
import FraudAlertsPanel from './components/FraudAlertsPanel';
import TransactionAnalytics from './components/TransactionAnalytics';
import ComplianceMonitoring from './components/ComplianceMonitoring';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const menuItems = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
  },
  {
    key: 'data-quality',
    icon: <SafetyOutlined />,
    label: 'Data Quality',
  },
  {
    key: 'fraud-alerts',
    icon: <AlertOutlined />,
    label: 'Fraud Alerts',
  },
  {
    key: 'analytics',
    icon: <BarChartOutlined />,
    label: 'Analytics',
  },
  {
    key: 'compliance',
    icon: <UserOutlined />,
    label: 'Compliance',
  },
];

function App() {
  const [selectedKey, setSelectedKey] = useState('dashboard');
  const [collapsed, setCollapsed] = useState(false);
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const renderContent = () => {
    switch (selectedKey) {
      case 'dashboard':
        return <DashboardOverview />;
      case 'data-quality':
        return <DataQualityPanel />;
      case 'fraud-alerts':
        return <FraudAlertsPanel />;
      case 'analytics':
        return <TransactionAnalytics />;
      case 'compliance':
        return <ComplianceMonitoring />;
      default:
        return <DashboardOverview />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        style={{ background: colorBgContainer }}
      >
        <div className="logo" style={{ padding: '16px', textAlign: 'center' }}>
          <Title level={4} style={{ color: '#1890ff', margin: 0 }}>
            {collapsed ? 'T' : 'TIMO'}
          </Title>
        </div>
        <Menu
          theme="light"
          selectedKeys={[selectedKey]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => setSelectedKey(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Title level={3} style={{ margin: 0 }}>
            Banking Data Platform
          </Title>
          <div style={{ color: '#666' }}>
            Last updated: {new Date().toLocaleString()}
          </div>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
          }}
        >
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
