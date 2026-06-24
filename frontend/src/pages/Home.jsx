import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Row, Col, Typography, Spin } from 'antd';
import { EyeOutlined, HeartOutlined, MessageOutlined } from '@ant-design/icons';
import { postsAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const { Title, Paragraph } = Typography;

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    postsAPI.list({ page: 1, page_size: 10 })
      .then((res) => setPosts(res.data?.items || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '24px 16px' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <Title level={2}>欢迎来到 MyBlog</Title>
        <Paragraph type="secondary">分享知识、记录生活</Paragraph>
        {user && (
          <Link to="/posts/new" style={{ fontSize: 16 }}>✏️ 写你的第一篇文章</Link>
        )}
      </div>

      <Row gutter={[24, 24]}>
        {posts.map((post) => (
          <Col xs={24} sm={12} key={post.id}>
            <Card
              hoverable
              onClick={() => navigate(`/posts/${post.id}`)}
              actions={[
                <span><EyeOutlined /> {post.view_count}</span>,
                <span><HeartOutlined /> {post.like_count}</span>,
                <span><MessageOutlined /> {post.comment_count}</span>,
              ]}
            >
              <Card.Meta
                title={post.title}
                description={
                  <>
                    <Paragraph ellipsis={{ rows: 2 }} type="secondary">
                      {post.summary || '暂无摘要'}
                    </Paragraph>
                    <small style={{ color: '#999' }}>
                      {new Date(post.created_at).toLocaleDateString('zh-CN')}
                    </small>
                  </>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
