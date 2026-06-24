import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, message } from 'antd';
import { postsAPI } from '../api/client';

const { TextArea } = Input;

export default function CreatePost() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const res = await postsAPI.create(values);
      message.success('文章发布成功！');
      navigate(`/posts/${res.data.id}`);
    } catch (err) {
      message.error(err?.msg || '发布失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 16px' }}>
      <Card title="写文章">
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入文章标题' }]}>
            <Input placeholder="给文章起个标题" size="large" />
          </Form.Item>
          <Form.Item name="summary" label="摘要">
            <Input.TextArea rows={2} placeholder="文章摘要（选填）" />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true, message: '请输入文章内容' }]}>
            <TextArea rows={15} placeholder="开始写作..." />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" size="large" loading={loading}>
              发布文章
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
