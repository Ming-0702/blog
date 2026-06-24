import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, message, Spin } from 'antd';
import { postsAPI } from '../api/client';

const { TextArea } = Input;

export default function EditPost() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    postsAPI.get(id)
      .then((res) => {
        form.setFieldsValue({
          title: res.data.title,
          summary: res.data.summary,
          content: res.data.content,
        });
      })
      .catch(() => message.error('加载文章失败'))
      .finally(() => setLoading(false));
  }, [id, form]);

  const onFinish = async (values) => {
    setSubmitting(true);
    try {
      await postsAPI.update(id, values);
      message.success('文章已更新！');
      navigate(`/posts/${id}`);
    } catch (err) {
      message.error(err?.msg || '更新失败');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 16px' }}>
      <Card title="编辑文章">
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input size="large" />
          </Form.Item>
          <Form.Item name="summary" label="摘要">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <TextArea rows={15} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={submitting}>保存</Button>
            <Button style={{ marginLeft: 8 }} onClick={() => navigate(-1)}>取消</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
