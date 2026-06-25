import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Select, message, Spin, Space, Switch } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import MDEditor from '@uiw/react-md-editor';
import { postsAPI } from '../api/client';

export default function EditPost() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    postsAPI.get(id)
      .then((res) => {
        form.setFieldsValue({
          title: res.data.title,
          summary: res.data.summary,
          content: res.data.content,
          tags: res.data.tags || [],
          is_pinned: res.data.is_pinned || false,
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
    } catch (err) { message.error(err?.msg || '更新失败'); }
    finally { setSubmitting(false); }
  };

  const handleAISummary = async () => {
    const content = form.getFieldValue('content');
    if (!content) { message.warning('请先写点内容'); return; }
    setAiLoading(true);
    try {
      const res = await postsAPI.generateSummary({ content, title: form.getFieldValue('title') || '' });
      form.setFieldsValue({ summary: res.data.summary });
      message.success('摘要已生成');
    } catch (err) { message.error(err?.msg || 'AI 摘要失败'); }
    finally { setAiLoading(false); }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 16px' }}>
      <Card title="编辑文章">
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input size="large" />
          </Form.Item>
          <Form.Item label="摘要">
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name="summary" noStyle>
                <Input.TextArea rows={2} />
              </Form.Item>
              <Button icon={<RobotOutlined />} loading={aiLoading} onClick={handleAISummary}
                style={{ height: 'auto' }}>AI 生成</Button>
            </Space.Compact>
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="添加标签（回车确认）" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_pinned" label="置顶" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}>
            <MDEditor preview="edit" height={500} />
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
