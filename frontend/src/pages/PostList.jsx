import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { List, Card, Spin, Pagination, Typography, Skeleton } from 'antd';
import { EyeOutlined, LikeOutlined, MessageOutlined } from '@ant-design/icons';
import { postsAPI } from '../api/client';

const { Paragraph } = Typography;

function timeAgo(d){const n=Date.now(),t=new Date(d).getTime(),s=Math.floor((n-t)/1e3);if(s<60)return'刚刚';if(s<3600)return Math.floor(s/60)+' 分钟前';if(s<86400)return Math.floor(s/3600)+' 小时前';if(s<2592000)return Math.floor(s/86400)+' 天前';return new Date(d).toLocaleDateString('zh-CN')}
export default function PostList() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    postsAPI.list({page,page_size:10})
      .then(r=>{setPosts(r.data?.items||[]);setTotal(r.data?.total||0)})
      .catch(()=>{}).finally(()=>setLoading(false));
  }, [page]);

  return (
    <div style={{maxWidth:800,margin:'0 auto',padding:'32px 16px'}}>
      <h1 style={{fontFamily:"'Noto Serif SC',serif",fontSize:28,color:'#4A3728',marginBottom:24}}>📚 全部文章</h1>

      {loading && posts.length===0 ? (
        <div style={{display:'flex',flexDirection:'column',gap:16}}>
          {[1,2,3].map(i=><Card key={i} style={{border:'none'}}><Skeleton active/></Card>)}
        </div>
      ) : posts.length===0 ? (
        <div style={{textAlign:'center',padding:60,color:'#A0937D'}}>还没有文章</div>
      ) : (
        <List dataSource={posts} renderItem={post=>(
          <Card hoverable style={{marginBottom:16,border:'none',background:'#FFF'}} onClick={()=>navigate(`/posts/${post.id}`)}>
            <Card.Meta
              title={<span style={{fontFamily:"'Noto Serif SC',serif",fontSize:17}}>{post.title}</span>}
              description={<>
                <Paragraph ellipsis={{rows:2}} style={{color:'#A0937D',marginBottom:12}}>{post.summary||'暂无摘要'}</Paragraph>
                <div style={{color:'#C4B5A5',fontSize:13,display:'flex',gap:16,flexWrap:'wrap',justifyContent:'space-between'}}>
                  <span>
                    <EyeOutlined/> {post.view_count} · <LikeOutlined/> {post.like_count} · <MessageOutlined/> {post.comment_count}
                  </span>
                  <span>
                    {post.author_name||''} · {timeAgo(post.created_at)}
                  </span>
                </div>
              </>}
            />
          </Card>
        )}/>
      )}

      <div style={{textAlign:'center',marginTop:24}}>
        <Pagination current={page} total={total} pageSize={10} onChange={setPage} showSizeChanger={false}/>
      </div>
    </div>
  );
}
