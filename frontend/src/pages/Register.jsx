import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

export default function Register() {
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await register(values);
      message.success('注册成功！');
      navigate('/');
    } catch (err) {
      message.error(err?.msg || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', padding: '0 16px' }}>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <h1 style={{ fontFamily: "'Noto Serif SC', serif", fontSize: 28, color: '#4A3728', margin: 0 }}>
          加入神秘盒子
        </h1>
        <p style={{ color: '#A0937D', marginTop: 8 }}>注册一个账号，开始互动</p>
      </div>
      <Card style={{ border: 'none', borderRadius: 16, boxShadow: '0 4px 24px rgba(139,94,60,0.1)' }}>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined style={{ color: '#A0937D' }} />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="email" rules={[{ required: true, type: 'email', message: '请输入有效邮箱' }]}>
            <Input prefix={<MailOutlined style={{ color: '#A0937D' }} />} placeholder="邮箱" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, min: 6, message: '密码至少6位' }]}>
            <Input.Password prefix={<LockOutlined style={{ color: '#A0937D' }} />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}
              style={{ height: 44, borderRadius: 10, fontSize: 16 }}>
              注册
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center', color: '#A0937D' }}>
          已有账号？<Link to="/login">去登录</Link>
        </div>
      </Card>
    </div>
  );
}
