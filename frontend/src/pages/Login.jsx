import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Card, message } from 'antd';
import { GithubOutlined, UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../api/client';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const [githubLoading, setGithubLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await login(values);
      message.success('登录成功！');
      navigate('/');
    } catch (err) {
      message.error(err?.msg || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleGithubLogin = async () => {
    setGithubLoading(true);
    try {
      const res = await authAPI.githubLogin();
      window.location.href = res.data.auth_url;
    } catch (err) {
      message.error(err?.msg || 'GitHub 登录失败');
      setGithubLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', padding: '0 16px' }}>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <h1 style={{ fontFamily: "'Noto Serif SC', serif", fontSize: 28, color: '#4A3728', margin: 0 }}>
          欢迎回来
        </h1>
        <p style={{ color: '#A0937D', marginTop: 8 }}>登录你的神秘盒子</p>
      </div>
      <Card style={{ border: 'none', borderRadius: 16, boxShadow: '0 4px 24px rgba(139,94,60,0.1)' }}>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名或邮箱' }]}>
            <Input prefix={<UserOutlined style={{ color: '#A0937D' }} />} placeholder="用户名或邮箱" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined style={{ color: '#A0937D' }} />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}
              style={{ height: 44, borderRadius: 10, fontSize: 16 }}>
              登录
            </Button>
          </Form.Item>
        </Form>
        <div style={{ marginBottom: 12, textAlign: 'center', color: '#A0937D' }}>
          还没有账号？<Link to="/register">立即注册</Link>
        </div>
        <Button icon={<GithubOutlined />} block loading={githubLoading} onClick={handleGithubLogin} style={{ borderRadius: 10 }}>
          GitHub 登录
        </Button>
      </Card>
    </div>
  );
}
