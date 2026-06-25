import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Select, message, Space, Upload, Switch } from 'antd';
import { RobotOutlined, UploadOutlined } from '@ant-design/icons';
import MDEditor from '@uiw/react-md-editor';
import { postsAPI } from '../api/client';

export default function CreatePost() {
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const handleUpload = async (options) => {
    setUploading(true);
    try {
      const res = await postsAPI.upload(options.file);
      message.success('文件导入成功！已自动发布');
      navigate(`/posts/${res.data.id}`);
    } catch (err) { message.error(err?.msg || '导入失败'); options.onError?.(); }
    finally { setUploading(false); }
  };

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const res = await postsAPI.create(values);
      message.success('文章发布成功！');
      navigate(`/posts/${res.data.id}`);
    } catch (err) {
      message.error(err?.msg || '发布失败');
    } finally { setLoading(false); }
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

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 16px' }}>
      <Card title="写文章" extra={
        <Upload showUploadList={false} accept=".md,.txt,.pdf" customRequest={handleUpload}>
          <Button icon={<UploadOutlined />} loading={uploading}>导入文件</Button>
        </Upload>
      }>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入文章标题' }]}>
            <Input placeholder="给文章起个标题" size="large" />
          </Form.Item>
          <Form.Item label="摘要">
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name="summary" noStyle>
                <Input.TextArea rows={2} placeholder="文章摘要（选填，或点右边AI生成）" />
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
          <Form.Item name="content" label="内容" rules={[{ required: true, message: '请输入文章内容' }]}>
            <MDEditor preview="edit" height={500} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" size="large" loading={loading}>发布文章</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
