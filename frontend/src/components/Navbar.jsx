import { useNavigate, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Layout, Menu, Button, Dropdown, Space, Badge, Popover, List, message } from 'antd';
import { UserOutlined, LogoutOutlined, EditOutlined, HomeOutlined, BellOutlined, SettingOutlined, ReadOutlined, ExperimentOutlined, SunOutlined, MoonOutlined, SearchOutlined, RocketOutlined, FireOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { postsAPI } from '../api/client';
import SearchModal from './SearchModal';
import useWebSocket from '../hooks/useWebSocket';

const { Header } = Layout;

export default function Navbar() {
  const [searchOpen, setSearchOpen] = useState(false);
  const { user, isAuthor, logout } = useAuth();

  // Ctrl+K 打开搜索
  useEffect(() => {
    const handler = (e) => { if ((e.ctrlKey||e.metaKey) && e.key==='k') { e.preventDefault(); setSearchOpen(true); } };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
  const { theme, toggleTheme } = useTheme();
  const { notifications, unreadCount, clearUnread } = useWebSocket();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleRandom = async () => {
    try {
      const res = await postsAPI.random();
      navigate(`/posts/${res.data.id}`);
    } catch { message.error('还没有文章哦'); }
  };

  const menuItems = [
    { key: '/', label: <Link to="/">首页</Link>, icon: <HomeOutlined /> },
    { key: '/posts', label: <Link to="/posts">文章</Link>, icon: <ReadOutlined /> },
    { key: '/digests', label: <Link to="/digests">资讯摘要</Link>, icon: <RocketOutlined /> },
    { key: '/trending', label: <Link to="/trending">AI趋势</Link>, icon: <FireOutlined /> },
    { key: '/papers', label: <Link to="/papers">论文速递</Link>, icon: <ExperimentOutlined /> },
    { key: 'random', label: '随机一篇', icon: <ExperimentOutlined />, onClick: handleRandom },
  ];

  const userMenuItems = user
    ? [
        { key: 'profile', label: `👋 ${user.nickname || user.username}`, disabled: true },
        { key: 'username', label: `@${user.username}`, disabled: true },
        { type: 'divider' },
        ...(isAuthor ? [
          { key: 'new-post', label: '写文章', icon: <EditOutlined />, onClick: () => navigate('/posts/new') },
        ] : []),
        { key: 'settings', label: '个人设置', icon: <SettingOutlined />, onClick: () => navigate('/settings') },
        { type: 'divider' },
        { key: 'logout', label: '退出登录', icon: <LogoutOutlined />, onClick: handleLogout },
      ]
    : [];

  return (
    <>
    <Header className="navbar-glass" style={{
      display: 'flex', alignItems: 'center', padding: '0 24px',
    }}>
      <Link to="/" style={{
        fontSize: 20, fontWeight: 700, marginRight: 40,
        fontFamily: "'Noto Serif SC', serif",
        color: '#8B5E3C', textDecoration: 'none',
        letterSpacing: 1,
      }}>
        📦 神秘盒子
      </Link>
      <Menu
        mode="horizontal"
        items={menuItems}
        style={{ flex: 1, border: 'none', background: 'transparent' }}
      />
      <Space>
        <Button type="text" icon={<SearchOutlined style={{color:'#8B5E3C'}}/>}
          onClick={() => setSearchOpen(true)} title="搜索 (Ctrl+K)"/>
      </Space>
      <Space>
        <Button type="text"
          icon={theme === 'light' ? <MoonOutlined style={{color:'#8B5E3C'}} /> : <SunOutlined style={{color:'#D4A574'}} />}
          onClick={toggleTheme}
        />
        {user ? (
          <>
            <Popover
              title="通知"
              content={
                notifications.length === 0 ? (
                  <span style={{ color: '#999' }}>暂无通知</span>
                ) : (
                  <List
                    size="small"
                    style={{ width: 280 }}
                    dataSource={notifications.slice(0, 10)}
                    renderItem={(item) => (
                      <List.Item>
                        <div>
                          <strong>{item.data?.from_user}</strong>{' '}
                          {item.type === 'new_comment' ? '评论了你的文章' : '回复了你的评论'}
                          <br />
                          <small style={{ color: '#999' }}>{item.data?.content_preview}</small>
                        </div>
                      </List.Item>
                    )}
                  />
                )
              }
              trigger="click"
              onOpenChange={(visible) => { if (visible) clearUnread(); }}
            >
              <Badge count={unreadCount} size="small" offset={[-2, 2]}>
                <Button type="text" icon={<BellOutlined style={{ color: '#8B5E3C' }} />} />
              </Badge>
            </Popover>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button
                type="text"
                icon={<UserOutlined style={{ color: '#8B5E3C' }} />}
                style={{ color: '#4A3728' }}
              >
                {user.nickname || user.username}
              </Button>
            </Dropdown>
          </>
        ) : (
          <>
            <Button type="text" onClick={() => navigate('/login')} style={{ color: '#4A3728' }}>登录</Button>
            <Button
              onClick={() => navigate('/register')}
              style={{ background: '#8B5E3C', color: '#fff', borderRadius: 8 }}
            >
              注册
            </Button>
          </>
        )}
      </Space>
    </Header>
    {searchOpen && <SearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />}
  </>
  );
}
