import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Row, Col, Typography, Spin, List, Tag, Skeleton, Space } from 'antd';
import { EyeOutlined, LikeOutlined, MessageOutlined, CrownOutlined } from '@ant-design/icons';
import { postsAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const { Title, Paragraph } = Typography;

function timeAgo(d) { const n=Date.now(),t=new Date(d).getTime(),s=Math.floor((n-t)/1e3); if(s<60)return'刚刚'; if(s<3600)return Math.floor(s/60)+' 分钟前'; if(s<86400)return Math.floor(s/3600)+' 小时前'; if(s<2592000)return Math.floor(s/86400)+' 天前'; return new Date(d).toLocaleDateString('zh-CN') }
function PostCard({ post }) {
  const navigate = useNavigate();
  return (
    <Card hoverable className="fade-in-up"
      onClick={() => navigate(`/posts/${post.id}`)}
      style={{ height:'100%', border:'none', background:'#FFF' }}
      actions={[
        <span key="v" style={{color:'#A0937D'}}><EyeOutlined/> {post.view_count}</span>,
        <span key="l" style={{color:'#A0937D'}}><LikeOutlined/> {post.like_count}</span>,
        <span key="c" style={{color:'#A0937D'}}><MessageOutlined/> {post.comment_count}</span>,
      ]}
    >
      <Card.Meta
        title={<span style={{fontFamily:"'Noto Serif SC',serif",fontSize:16}}>
          {post.is_pinned && <Tag color="#D4A574" style={{marginRight:6,borderRadius:4,fontSize:11}}>📌 置顶</Tag>}
          {post.title}
        </span>}
        description={<>
          <Paragraph ellipsis={{rows:2}} style={{color:'#A0937D',marginBottom:8}}>{post.summary||'暂无摘要'}</Paragraph>
          {post.tags?.length > 0 && (
            <Space size={4} wrap style={{marginBottom:8}}>
              {post.tags.map(t=><Tag key={t} color="#D4A574" style={{borderRadius:6}}>{t}</Tag>)}
            </Space>
          )}
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <small style={{color:'#C4B5A5'}}>
              {post.author_name||''} · {timeAgo(post.created_at)}
            </small>
          </div>
        </>}
      />
    </Card>
  );
}

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hotPosts, setHotPosts] = useState([]);
  const { user, isAuthor } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    postsAPI.list({page:1,page_size:10})
      .then(r=>setPosts(r.data?.items||[])).catch(()=>{}).finally(()=>setLoading(false));
    postsAPI.hot({limit:5}).then(r=>setHotPosts(r.data||[])).catch(()=>{});
  }, []);

  return (
    <div>
      <div style={{background:'linear-gradient(135deg,#FDF8F4 0%,#F5EDE6 50%,#E8D5C4 100%)',padding:'80px 16px 60px',textAlign:'center',position:'relative',overflow:'hidden'}}>
        <div style={{position:'absolute',top:-60,right:-40,fontSize:120,opacity:.06,userSelect:'none'}}>📦</div>
        <Title level={1} style={{fontFamily:"'Noto Serif SC',serif",fontSize:42,color:'#4A3728',marginBottom:12,position:'relative',zIndex:1}}>时不时丢点东西的神秘盒子</Title>
        <Paragraph style={{fontSize:17,color:'#8B5E3C',marginBottom:24,fontFamily:"'Noto Serif SC',serif",position:'relative',zIndex:1}}>偶尔更新，随心记录 ✨</Paragraph>
        {isAuthor && <Link to="/posts/new" style={{fontSize:16,color:'#8B5E3C',border:'1px solid #8B5E3C',borderRadius:20,padding:'8px 28px',textDecoration:'none',transition:'all .3s',position:'relative',zIndex:1}}>✏️ 写点什么</Link>}
      </div>

      <div style={{maxWidth:960,margin:'0 auto',padding:'24px 16px'}}>
        {hotPosts.length>0&&(
          <div style={{marginBottom:40}}>
            <Title level={3} style={{fontFamily:"'Noto Serif SC',serif",display:'flex',alignItems:'center',gap:8,marginBottom:16}}><CrownOutlined style={{color:'#D4A574'}}/> 热门文章</Title>
            <List dataSource={hotPosts} renderItem={(post,i)=>(
              <List.Item onClick={()=>navigate(`/posts/${post.id}`)} className="fade-in-up"
                style={{cursor:'pointer',padding:'12px 16px',borderRadius:10,marginBottom:4,
                  background:i<3?'#FFF':'transparent',boxShadow:i<3?'0 1px 6px rgba(139,94,60,0.06)':'none'}}>
                <List.Item.Meta
                  avatar={<Tag color={i<3?'#D4A574':'#D7CCC8'} style={{borderRadius:6}}>#{i+1}</Tag>}
                  title={<span style={{fontFamily:"'Noto Serif SC',serif"}}>{post.title}</span>}
                  description={<>{post.author_name||''} · {post.like_count} 赞 · {post.comment_count} 评论</>}
                />
              </List.Item>
            )}/>
          </div>
        )}

        <Title level={3} style={{fontFamily:"'Noto Serif SC',serif",marginBottom:20,display:'flex',alignItems:'center',gap:8}}>📝 最新文章</Title>

        {loading ? (
          <Row gutter={[24,24]}>
            {[1,2,3,4].map(i=><Col xs={24} sm={12} key={i}><Card style={{border:'none'}}><Skeleton active/></Card></Col>)}
          </Row>
        ) : (
          <Row gutter={[24,24]} className="card-stagger">
            {posts.map(p=><Col xs={24} sm={12} key={p.id}><PostCard post={p}/></Col>)}
          </Row>
        )}

        {!loading&&posts.length===0&&<div style={{textAlign:'center',padding:40,color:'#A0937D'}}>还没有文章，敬请期待 🌿</div>}
      </div>
    </div>
  );
}
