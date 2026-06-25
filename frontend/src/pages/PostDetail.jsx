import { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Typography, Spin, Card, Button, Input, message, List, Space, Avatar, Modal, Row, Col, Affix } from 'antd';
import { LikeOutlined, LikeFilled, MessageOutlined, DeleteOutlined, EditOutlined, UserOutlined, ArrowLeftOutlined, ArrowUpOutlined, TagOutlined, MenuOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeSlug from 'rehype-slug';
import 'katex/dist/katex.min.css';
import { postsAPI, commentsAPI, likesAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const { Title, Paragraph } = Typography;

// 代码块 + 复制按钮
function CodeBlock({ className, children, ...props }) {
  const [copied, setCopied] = useState(false);
  const code = typeof children === 'string' ? children : '';
  const match = /language-(\w+)/.exec(className || '');
  const lang = match ? match[1] : '';

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <pre className={className} style={{ position: 'relative' }}>
      {lang && <span style={{ position: 'absolute', top: 8, left: 16, fontSize: 11, color: '#A0937D', opacity: 0.6 }}>{lang}</span>}
      <Button size="small" type="text"
        onClick={handleCopy}
        style={{ position: 'absolute', top: 6, right: 8, color: '#A0937D', fontSize: 12 }}>
        {copied ? '✓ 已复制' : '📋 复制'}
      </Button>
      <code {...props}>{children}</code>
    </pre>
  );
}

const TextArea = Input.TextArea;

export default function PostDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const searchQuery = searchParams.get('q') || '';
  const navigate = useNavigate();
  const { user, isAuthor } = useAuth();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [commentText, setCommentText] = useState('');
  const [replyTo, setReplyTo] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editingText, setEditingText] = useState('');
  const [commentLiked, setCommentLiked] = useState({});
  const [commentLikeCounts, setCommentLikeCounts] = useState({});
  const [progress, setProgress] = useState(0);
  const [showBackTop, setShowBackTop] = useState(false);
  const [activeId, setActiveId] = useState('');
  const contentRef = useRef(null);

  // 提取标题生成目录
  const headings = useMemo(() => {
    if (!post?.content) return [];
    const h = [];
    const regex = /^(#{1,3})\s+(.+)$/gm;
    let m;
    while ((m = regex.exec(post.content)) !== null) {
      const level = m[1].length;
      const text = m[2].replace(/[`*_{}[\]()#+\-.!]/g, '');
      const id = text.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9一-鿿-]/g, '');
      h.push({ level, text, id });
    }
    return h;
  }, [post?.content]);

  // 跟踪当前阅读位置
  useEffect(() => {
    if (headings.length === 0) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) { setActiveId(e.target.id); break; }
        }
      },
      { rootMargin: '-80px 0px -70% 0px' }
    );
    headings.forEach(h => {
      const el = document.getElementById(h.id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [headings, post]);

  // 搜索高亮 + 滚动到匹配处
  useEffect(() => {
    if (!searchQuery || !post || loading) return;
    let retries = 5;
    let tid;
    const doHighlight = () => {
      const body = document.querySelector('.markdown-body');
      if (!body && retries-- > 0) { tid = setTimeout(doHighlight, 200); return; }
      if (!body) return;
      body.querySelectorAll('mark.search-hl').forEach(m => m.replaceWith(m.textContent || ''));
      const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      let first = null;
      nodes.forEach(node => {
        const idx = node.textContent.toLowerCase().indexOf(searchQuery.toLowerCase());
        if (idx !== -1) {
          const mark = document.createElement('mark');
          mark.className = 'search-hl';
          const pre = node.textContent.slice(0, idx);
          const hit = node.textContent.slice(idx, idx + searchQuery.length);
          const post = node.textContent.slice(idx + searchQuery.length);
          const frag = document.createDocumentFragment();
          if (pre) frag.appendChild(document.createTextNode(pre));
          mark.textContent = hit;
          frag.appendChild(mark);
          if (post) frag.appendChild(document.createTextNode(post));
          node.parentNode?.replaceChild(frag, node);
          if (!first) first = mark;
        }
      });
      if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };
    tid = setTimeout(doHighlight, 500);
    return () => clearTimeout(tid);
  }, [post?.id, searchQuery, loading]);

  // 阅读进度
  useEffect(() => {
    const onScroll = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(docHeight > 0 ? Math.min(100, (scrollTop / docHeight) * 100) : 0);
      setShowBackTop(scrollTop > 400);
    };
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    loadPost();
    loadComments();
  }, [id]);

  const loadPost = async () => {
    try {
      const res = await postsAPI.get(id);
      setPost(res.data);
      setLikeCount(res.data.like_count);
      if (user) {
        const statusRes = await likesAPI.status('post', id);
        setLiked(statusRes.data?.liked || false);
      }
    } catch { message.error('加载文章失败') }
    finally { setLoading(false) }
  };

  const loadComments = async () => {
    try {
      const res = await commentsAPI.list(id);
      const commentList = res.data || [];
      setComments(commentList);
      const counts = {};
      const allIds = [];
      const flatten = (list) => {
        list.forEach((c) => {
          counts[c.id] = c.like_count;
          allIds.push(c.id);
          if (c.replies) flatten(c.replies);
        });
      };
      flatten(commentList);
      setCommentLikeCounts(counts);
      if (user && allIds.length > 0) {
        const statuses = await Promise.all(
          allIds.map((cid) =>
            likesAPI.status('comment', cid)
              .then((r) => ({ id: cid, liked: r.data?.liked || false }))
              .catch(() => ({ id: cid, liked: false }))
          )
        );
        const likedMap = {};
        statuses.forEach((s) => { if (s.liked) likedMap[s.id] = true; });
        setCommentLiked(likedMap);
      }
    } catch {}
  };

  const handleLike = async () => {
    if (!user) { message.warning('请先登录'); return; }
    try {
      const res = await likesAPI.toggle({ target_type: 'post', target_id: Number(id) });
      setLiked(res.data.liked);
      setLikeCount(res.data.like_count);
    } catch { message.error('操作失败') }
  };

  const handleComment = async () => {
    if (!user) { message.warning('请先登录'); return; }
    if (!commentText.trim()) { message.warning('请输入评论内容'); return; }
    setSubmitting(true);
    try {
      await commentsAPI.create(id, { content: commentText, parent_id: replyTo?.id || null });
      message.success('评论成功');
      setCommentText('');
      setReplyTo(null);
      loadComments();
      loadPost();
    } catch { message.error('评论失败') }
    finally { setSubmitting(false) }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await commentsAPI.delete(commentId);
      message.success('评论已删除');
      loadComments();
      loadPost();
    } catch { message.error('删除失败') }
  };

  const handleEditComment = (comment) => {
    setEditingId(comment.id);
    setEditingText(comment.content);
  };

  const handleSaveComment = async (commentId) => {
    if (!editingText.trim()) { message.warning('评论内容不能为空'); return; }
    try {
      await commentsAPI.update(commentId, { content: editingText });
      message.success('评论已更新');
      setEditingId(null);
      setEditingText('');
      loadComments();
    } catch { message.error('编辑失败') }
  };

  const handleCommentLike = async (commentId) => {
    if (!user) { message.warning('请先登录'); return; }
    try {
      const res = await likesAPI.toggle({ target_type: 'comment', target_id: commentId });
      setCommentLiked((prev) => ({ ...prev, [commentId]: res.data.liked }));
      setCommentLikeCounts((prev) => ({ ...prev, [commentId]: res.data.like_count }));
    } catch { message.error('操作失败') }
  };

  const renderCommentActions = (comment) => {
    if (!user) return null;
    return (
      <Space>
        <Button type="link" size="small"
          icon={commentLiked[comment.id] ? <LikeFilled style={{ color: '#8B5E3C' }} /> : <LikeOutlined />}
          onClick={() => handleCommentLike(comment.id)}
        >
          {commentLikeCounts[comment.id] ?? comment.like_count}
        </Button>
        <Button type="link" size="small" onClick={() => setReplyTo(comment)}>回复</Button>
        {user.id === comment.author_id && (
          <>
            <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditComment(comment)} />
            <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteComment(comment.id)} />
          </>
        )}
      </Space>
    );
  };

  const renderCommentContent = (comment) => {
    if (editingId === comment.id) {
      return (
        <div style={{ marginTop: 8 }}>
          <TextArea rows={2} value={editingText} onChange={(e) => setEditingText(e.target.value)} />
          <Space style={{ marginTop: 8 }}>
            <Button size="small" type="primary" onClick={() => handleSaveComment(comment.id)}>保存</Button>
            <Button size="small" onClick={() => { setEditingId(null); setEditingText(''); }}>取消</Button>
          </Space>
        </div>
      );
    }
    return <Paragraph style={{ margin: '8px 0 0 0' }}>{comment.content}</Paragraph>;
  };

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
  if (!post) return <div style={{ textAlign: 'center', padding: 80 }}>文章不存在</div>;

  return (
    <>
      {/* 阅读进度条 */}
      <div className="reading-progress" style={{ width: `${progress}%` }} />

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 16px' }}>
        <Row gutter={32}>
          {/* 正文 */}
          <Col xs={24} lg={headings.length > 0 ? 18 : 24}>
        <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}
          style={{ marginBottom: 20, padding: 0, color: '#8B5E3C' }}>
          返回
        </Button>

        <Card style={{ border: 'none', padding: 24 }}>
          {/* 文章头 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
            <Title style={{ flex: 1, fontFamily: "'Noto Serif SC', serif", fontSize: 28, border: 'none', marginBottom: 0 }}>
              {post.is_pinned && <Tag color="#D4A574" style={{ marginRight: 8, borderRadius: 4 }}>📌 置顶</Tag>}
              {post.title}
            </Title>
            {isAuthor && (
              <Space>
                <Button icon={<EditOutlined />}
                  style={{ borderColor: '#8B5E3C', color: '#8B5E3C', borderRadius: 8 }}
                  onClick={() => navigate(`/posts/${post.id}/edit`)}>编辑</Button>
                <Button icon={<DeleteOutlined />} danger
                  style={{ borderRadius: 8 }}
                  onClick={() => {
                    Modal.confirm({
                      title: '确认删除',
                      content: '删除后无法恢复，确定要删除这篇文章吗？',
                      okText: '删除',
                      okType: 'danger',
                      cancelText: '取消',
                      onOk: async () => {
                        try {
                          await postsAPI.delete(post.id);
                          message.success('文章已删除');
                          navigate('/');
                        } catch { message.error('删除失败'); }
                      },
                    });
                  }}>删除</Button>
              </Space>
            )}
          </div>

          {/* 元信息 */}
          <div style={{
            display: 'flex', gap: 16, marginBottom: 24, paddingBottom: 20,
            borderBottom: '1px solid #E8D5C4', color: '#A0937D', fontSize: 14,
            flexWrap: 'wrap',
          }}>
            <span><UserOutlined style={{ marginRight: 4 }} /> {post.author_name || `用户#${post.author_id}`}</span>
            <span>📅 {new Date(post.created_at).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
            <span>👁 {post.view_count} 阅读</span>
            <span>⏱ {Math.max(1, Math.ceil((post.content?.length||0) / 400))} 分钟</span>
          </div>

          {post.tags?.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              {post.tags.map(t => <Tag key={t} color="#D4A574" style={{ borderRadius: 6, marginBottom: 4 }}>{t}</Tag>)}
            </div>
          )}

          {/* Markdown 正文 */}
          <div className="markdown-body" style={{ fontSize: 16 }}>
            <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex, rehypeSlug]}
              components={{ pre: CodeBlock }}>
              {post.content}
            </ReactMarkdown>
          </div>

          {/* 操作栏 */}
          <div style={{ marginTop: 32, borderTop: '1px solid #E8D5C4', paddingTop: 16, display: 'flex', gap: 24 }}>
            <Button type="text" size="large"
              icon={liked ? <LikeFilled style={{ color: '#8B5E3C' }} /> : <LikeOutlined />}
              onClick={handleLike}
              style={{ fontSize: 16, color: '#4A3728' }}
            >
              {likeCount}
            </Button>
            <span style={{ fontSize: 16, color: '#A0937D', display: 'flex', alignItems: 'center', gap: 4 }}>
              <MessageOutlined /> {post.comment_count} 条评论
            </span>
          </div>
        </Card>

        {/* 评论区 */}
        <Card id="comments"
          title={<span style={{ fontFamily: "'Noto Serif SC', serif" }}>💬 评论 ({comments.length})</span>}
          style={{ marginTop: 24, border: 'none' }}
        >
          {user ? (
            <div style={{ marginBottom: 20 }}>
              {replyTo && (
                <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                  回复 @{replyTo.author_name || replyTo.author_id}：
                  <Button type="link" size="small" onClick={() => setReplyTo(null)}>取消</Button>
                </Paragraph>
              )}
              <TextArea rows={3} value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder={replyTo ? `回复 #${replyTo.id}` : "写下你的评论..."} />
              <Button type="primary" style={{ marginTop: 8, borderRadius: 8 }} loading={submitting} onClick={handleComment}>
                发表评论
              </Button>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 16, color: '#A0937D', marginBottom: 16 }}>
              请<Button type="link" onClick={() => navigate('/login')} style={{ padding: 0 }}>登录</Button>后发表评论
            </div>
          )}

          {comments.length === 0 ? (
            <Paragraph style={{ textAlign: 'center', color: '#A0937D' }}>暂无评论，来说点什么吧</Paragraph>
          ) : (
            <List dataSource={comments}
              renderItem={(comment) => (
                <List.Item style={{ flexDirection: 'column', alignItems: 'stretch', borderBottom: '1px solid #F5EDE6', padding: '16px 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <div>
                      <Space><Avatar size={24} src={comment.author_avatar} icon={<UserOutlined />} /><strong style={{ color: '#4A3728' }}>{comment.author_name || `用户#${comment.author_id}`}</strong></Space>
                      <small style={{ marginLeft: 12, color: '#C4B5A5' }}>
                        {new Date(comment.created_at).toLocaleString('zh-CN')}
                      </small>
                    </div>
                    {renderCommentActions(comment)}
                  </div>
                  {renderCommentContent(comment)}

                  {/* 楼中楼 */}
                  {comment.replies?.length > 0 && (
                    <div style={{ marginLeft: 24, marginTop: 12, paddingLeft: 16, borderLeft: '2px solid #E8D5C4' }}>
                      {comment.replies.map((reply) => (
                        <div key={reply.id} style={{ marginBottom: 12 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Space><Avatar size={20} src={reply.author_avatar} icon={<UserOutlined />} /><strong style={{ color: '#4A3728' }}>{reply.author_name || `用户#${reply.author_id}`}</strong></Space>
                            <small style={{ color: '#C4B5A5' }}>
                              {new Date(reply.created_at).toLocaleString('zh-CN')}
                              {user?.id === reply.author_id && (
                                <Space size="small" style={{ marginLeft: 8 }}>
                                  <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditComment(reply)} />
                                  <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteComment(reply.id)} />
                                </Space>
                              )}
                            </small>
                          </div>
                          {renderCommentContent(reply)}
                        </div>
                      ))}
                    </div>
                  )}
                </List.Item>
              )}
            />
          )}
        </Card>
        <div style={{ height: 60 }} />
        </Col>

        {/* TOC 侧边栏 */}
        {headings.length > 0 && (
          <Col xs={0} lg={6}>
            <Affix offsetTop={80}>
              <div style={{
                padding: '16px 0',
                position: 'sticky', top: 80,
              }}>
                <div style={{
                  fontFamily: "'Noto Serif SC', serif",
                  fontSize: 14, fontWeight: 600,
                  color: 'var(--warm-brown)', marginBottom: 12,
                  display: 'flex', alignItems: 'center', gap: 6,
                }}>
                  <MenuOutlined /> 目录
                </div>
                <nav style={{ borderLeft: '2px solid var(--warm-border)', paddingLeft: 12 }}>
                  {headings.map(h => (
                    <a
                      key={h.id}
                      href={`#${h.id}`}
                      onClick={e => {
                        e.preventDefault();
                        document.getElementById(h.id)?.scrollIntoView({ behavior: 'smooth' });
                      }}
                      style={{
                        display: 'block',
                        padding: '4px 0',
                        paddingLeft: (h.level - 1) * 12,
                        fontSize: 13,
                        color: activeId === h.id ? 'var(--warm-brown)' : 'var(--warm-muted)',
                        fontWeight: activeId === h.id ? 600 : 400,
                        textDecoration: 'none',
                        transition: 'color 0.2s',
                        lineHeight: 1.5,
                      }}
                    >
                      {h.text}
                    </a>
                  ))}
                </nav>
              </div>
            </Affix>
          </Col>
        )}
        </Row>
      </div>

      {/* 底部浮动操作栏 */}
      {post && (
        <div style={{
          position: 'fixed', bottom: 0, left: 0, right: 0,
          background: 'var(--warm-card)', borderTop: '1px solid var(--warm-border)',
          padding: '12px 24px', display: 'flex', justifyContent: 'center', gap: 24,
          zIndex: 100, backdropFilter: 'blur(8px)',
        }}>
          <Button type="text" size="large"
            icon={liked ? <LikeFilled style={{ color: '#8B5E3C' }} /> : <LikeOutlined />}
            onClick={handleLike}>
            {likeCount}
          </Button>
          <Button type="text" size="large" icon={<MessageOutlined />}
            onClick={() => {
              document.getElementById('comments')?.scrollIntoView({ behavior: 'smooth' });
            }}>
            {post.comment_count} 评论
          </Button>
        </div>
      )}

      {/* 回到顶部 */}
      {showBackTop && (
        <button className="back-to-top" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <ArrowUpOutlined />
        </button>
      )}
    </>
  );
}
