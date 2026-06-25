import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal, Input, List, Tag, Empty, Typography } from 'antd';
import { SearchOutlined, FileTextOutlined } from '@ant-design/icons';
import { postsAPI } from '../api/client';

const { Text } = Typography;

export default function SearchModal({ open, onClose }) {
  const [query, setQuery] = useState('');
  const [posts, setPosts] = useState([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) return;
    setQuery(''); setSelected(0); setPosts([]);
  }, [open]);

  // 防抖搜索
  useEffect(() => {
    if (!query.trim()) { setPosts([]); return; }
    const timer = setTimeout(() => {
      setLoading(true);
      postsAPI.search({ q: query })
        .then(r => { setPosts(r.data || []); setSelected(0); })
        .catch(() => {})
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelected(s => Math.min(s + 1, posts.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === 'Enter' && posts[selected]) { navigate(`/posts/${posts[selected].id}?q=${encodeURIComponent(query)}`); onClose(); }
  };

  return (
    <Modal open={open} onCancel={onClose} footer={null} width={560}
      title={null} closable={false} style={{ top: 80 }}>
      <Input prefix={<SearchOutlined style={{ color: '#A0937D' }} />}
        placeholder="搜索文章标题、摘要、标签、正文..."
        size="large" value={query}
        onChange={e => { setQuery(e.target.value); setSelected(0); }}
        onKeyDown={handleKeyDown} autoFocus
        style={{ borderRadius: 10 }} />
      {query.trim() && !loading && posts.length === 0 && (
        <Empty description="没有找到相关文章" style={{ marginTop: 24 }} />
      )}
      {posts.length > 0 && (
        <List style={{ marginTop: 12 }} loading={loading}
          dataSource={posts} renderItem={(post, i) => (
            <List.Item onClick={() => { navigate(`/posts/${post.id}?q=${encodeURIComponent(query)}`); onClose(); }}
              onMouseEnter={() => setSelected(i)}
              style={{ cursor: 'pointer', padding: '12px 8px', borderRadius: 8,
                background: i === selected ? 'var(--warm-bg)' : 'transparent', border: 'none' }}>
              <List.Item.Meta
                avatar={<FileTextOutlined style={{ fontSize: 18, color: '#8B5E3C', marginTop: 4 }} />}
                title={<span style={{ fontFamily: "'Noto Serif SC', serif" }}>{post.title}</span>}
                description={<>
                  {post.highlight === 'title' ? (
                    <Text type="secondary" style={{ fontSize: 13, color: '#D4A574' }}>标题匹配</Text>
                  ) : post.snippet ? (
                    <Text ellipsis style={{ fontSize: 13 }}>
                      <span dangerouslySetInnerHTML={{ __html: post.snippet }} />
                    </Text>
                  ) : (
                    <Text ellipsis type="secondary" style={{ fontSize: 13 }}>{post.summary}</Text>
                  )}
                  {post.tags?.length > 0 && <div style={{ marginTop: 4 }}>
                    {post.tags.map(t => <Tag key={t} style={{ borderRadius: 4, fontSize: 11 }}>{t}</Tag>)}
                  </div>}
                </>} />
            </List.Item>
          )} />
      )}
      <div style={{ marginTop: 8, fontSize: 12, color: '#A0937D', textAlign: 'center' }}>
        <kbd>↑↓</kbd> 导航 <kbd>Enter</kbd> 打开 <kbd>Esc</kbd> 关闭
      </div>
    </Modal>
  );
}
