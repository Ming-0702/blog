import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Typography, Spin, Card, Button, Input, message, Avatar, List, Space } from 'antd';
import { HeartOutlined, HeartFilled, MessageOutlined, DeleteOutlined, UserOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { postsAPI, commentsAPI, likesAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

export default function PostDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [commentText, setCommentText] = useState('');
  const [replyTo, setReplyTo] = useState(null);
  const [submitting, setSubmitting] = useState(false);

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
      setComments(res.data || []);
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
      loadPost(); // 刷新评论计数
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

  if (loading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
  if (!post) return <div style={{ textAlign: 'center', padding: 80 }}>文章不存在</div>;

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 16px' }}>
      <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} style={{ marginBottom: 16, padding: 0 }}>
        返回
      </Button>

      {/* 文章内容 */}
      <Card>
        <Title>{post.title}</Title>
        <Paragraph type="secondary">
          <UserOutlined style={{ marginRight: 4 }} />
          {post.author_id} · {new Date(post.created_at).toLocaleDateString('zh-CN')}
        </Paragraph>
        <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 16 }}>
          {post.content}
        </div>
        <div style={{ marginTop: 24, borderTop: '1px solid #f0f0f0', paddingTop: 16 }}>
          <Space size="large">
            <Button
              type="text"
              size="large"
              icon={liked ? <HeartFilled style={{ color: 'red' }} /> : <HeartOutlined />}
              onClick={handleLike}
            >
              {likeCount}
            </Button>
            <span><MessageOutlined /> {post.comment_count}</span>
          </Space>
        </div>
      </Card>

      {/* 评论区域 */}
      <Card title={`评论 (${comments.length})`} style={{ marginTop: 24 }}>
        {user && (
          <div style={{ marginBottom: 16 }}>
            {replyTo && (
              <Paragraph type="secondary">
                回复 @{replyTo.author_id}：
                <Button type="link" size="small" onClick={() => setReplyTo(null)}>取消</Button>
              </Paragraph>
            )}
            <TextArea
              rows={3}
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder={replyTo ? `回复 #${replyTo.id}` : "写下你的评论..."}
            />
            <Button type="primary" style={{ marginTop: 8 }} loading={submitting} onClick={handleComment}>
              发表评论
            </Button>
          </div>
        )}

        {comments.length === 0 ? (
          <Paragraph type="secondary">暂无评论</Paragraph>
        ) : (
          <List
            dataSource={comments}
            renderItem={(comment) => (
              <List.Item style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                  <div>
                    <strong>用户 #{comment.author_id}</strong>
                    <small style={{ marginLeft: 12, color: '#999' }}>
                      {new Date(comment.created_at).toLocaleString('zh-CN')}
                    </small>
                  </div>
                  <Space>
                    {user && (
                      <Button type="link" size="small" onClick={() => setReplyTo(comment)}>
                        回复
                      </Button>
                    )}
                    {user?.id === comment.author_id && (
                      <Button type="link" size="small" danger icon={<DeleteOutlined />}
                        onClick={() => handleDeleteComment(comment.id)} />
                    )}
                  </Space>
                </div>
                <Paragraph style={{ margin: '8px 0 0 0' }}>{comment.content}</Paragraph>

                {/* 楼中楼回复 */}
                {comment.replies?.length > 0 && (
                  <div style={{ marginLeft: 24, marginTop: 8, paddingLeft: 12, borderLeft: '2px solid #e8e8e8' }}>
                    {comment.replies.map((reply) => (
                      <div key={reply.id} style={{ marginBottom: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <strong>用户 #{reply.author_id}</strong>
                          <small style={{ color: '#999' }}>
                            {new Date(reply.created_at).toLocaleString('zh-CN')}
                            {user?.id === reply.author_id && (
                              <Button type="link" size="small" danger icon={<DeleteOutlined />}
                                onClick={() => handleDeleteComment(reply.id)} />
                            )}
                          </small>
                        </div>
                        <Paragraph style={{ margin: 0 }}>{reply.content}</Paragraph>
                      </div>
                    ))}
                  </div>
                )}
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  );
}
