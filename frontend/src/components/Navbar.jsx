import { useNavigate, Link } from 'react-router-dom';
import { Layout, Menu, Button, Dropdown, Space } from 'antd';
import { UserOutlined, LogoutOutlined, EditOutlined, HomeOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Header } = Layout;

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    { key: '/', label: <Link to="/">首页</Link>, icon: <HomeOutlined /> },
    { key: '/posts', label: <Link to="/posts">文章</Link> },
  ];

  const userMenuItems = user
    ? [
        { key: 'profile', label: `${user.nickname || user.username}`, disabled: true },
        { type: 'divider' },
        { key: 'new-post', label: '写文章', icon: <EditOutlined />, onClick: () => navigate('/posts/new') },
        { type: 'divider' },
        { key: 'logout', label: '退出登录', icon: <LogoutOutlined />, onClick: handleLogout },
      ]
    : [];

  return (
    <Header style={{ display: 'flex', alignItems: 'center', background: '#fff', borderBottom: '1px solid #f0f0f0', padding: '0 24px' }}>
      <div style={{ fontSize: 20, fontWeight: 'bold', marginRight: 40, color: '#1677ff' }}>
        <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>MyBlog</Link>
      </div>
      <Menu mode="horizontal" items={menuItems} style={{ flex: 1, border: 'none' }} />
      <Space>
        {user ? (
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button type="text" icon={<UserOutlined />}>{user.nickname || user.username}</Button>
          </Dropdown>
        ) : (
          <>
            <Button type="text" onClick={() => navigate('/login')}>登录</Button>
            <Button type="primary" onClick={() => navigate('/register')}>注册</Button>
          </>
        )}
      </Space>
    </Header>
  );
}
