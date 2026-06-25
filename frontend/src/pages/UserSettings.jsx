import { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Upload, message, Avatar } from 'antd';
import { UserOutlined, UploadOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { usersAPI } from '../api/client';

export default function UserSettings() {
  const { user, setAuth } = useAuth();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      form.setFieldsValue({ nickname: user.nickname, bio: user.bio });
    }
  }, [user, form]);

  const handleSaveProfile = async (values) => {
    setLoading(true);
    try {
      const res = await usersAPI.update(values);
      const token = localStorage.getItem('token');
      setAuth(token, res.data);
      message.success('个人资料已更新');
    } catch (err) {
      message.error(err?.msg || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (options) => {
    try {
      const res = await usersAPI.uploadAvatar(options.file);
      const token = localStorage.getItem('token');
      setAuth(token, res.data.user);
      message.success('头像已更新');
      options.onSuccess?.();
    } catch (err) {
      message.error(err?.msg || '上传失败');
      options.onError?.();
    }
  };

  if (!user) return null;

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '24px 16px' }}>
      <Card title="个人设置">
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Avatar
            size={80}
            src={user.avatar_url}
            icon={!user.avatar_url && <UserOutlined />}
          />
          <div style={{ marginTop: 8, color: '#A0937D', fontSize: 14 }}>
            @{user.username}
          </div>
          <div style={{ marginTop: 8 }}>
            <Upload
              showUploadList={false}
              accept="image/*"
              customRequest={handleAvatarUpload}
            >
              <Button icon={<UploadOutlined />} size="small">更换头像</Button>
            </Upload>
          </div>
        </div>

        <Form form={form} layout="vertical" onFinish={handleSaveProfile}>
          <Form.Item name="nickname" label="昵称">
            <Input />
          </Form.Item>
          <Form.Item name="bio" label="个人简介">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>保存</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
