import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { List, Card, Spin, Pagination, Typography } from 'antd';
import { EyeOutlined, HeartOutlined, MessageOutlined } from '@ant-design/icons';
import { postsAPI } from '../api/client';

const { Paragraph } = Typography;

export default function PostList() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    postsAPI.list({ page, page_size: 10 })
      .then((res) => {
        setPosts(res.data?.items || []);
        setTotal(res.data?.total || 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page]);

  if (loading && posts.length === 0) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 16px' }}>
      <h1 style={{ marginBottom: 24 }}>全部文章</h1>
      <List
        dataSource={posts}
        loading={loading}
        renderItem={(post) => (
          <Card
            hoverable
            style={{ marginBottom: 16 }}
            onClick={() => navigate(`/posts/${post.id}`)}
          >
            <Card.Meta
              title={post.title}
              description={
                <>
                  <Paragraph ellipsis={{ rows: 2 }} type="secondary">
                    {post.summary || '暂无摘要'}
                  </Paragraph>
                  <div style={{ color: '#999', fontSize: 13 }}>
                    <span style={{ marginRight: 16 }}><EyeOutlined /> {post.view_count}</span>
                    <span style={{ marginRight: 16 }}><HeartOutlined /> {post.like_count}</span>
                    <span><MessageOutlined /> {post.comment_count}</span>
                    <span style={{ float: 'right' }}>
                      {new Date(post.created_at).toLocaleDateString('zh-CN')}
                    </span>
                  </div>
                </>
              }
            />
          </Card>
        )}
      />
      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <Pagination current={page} total={total} pageSize={10} onChange={setPage} showSizeChanger={false} />
      </div>
    </div>
  );
}
