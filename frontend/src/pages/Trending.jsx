import { useEffect, useState } from 'react';
import { Card, List, Pagination, Tag, Spin, Skeleton, Typography } from 'antd';
import { StarOutlined, GithubOutlined, RobotOutlined, CalendarOutlined } from '@ant-design/icons';
import { automationAPI } from '../api/client';

const { Title, Paragraph } = Typography;

const LANG_COLORS = {
  'Python': '#3572A5', 'JavaScript': '#F7DF1E', 'TypeScript': '#3178C6',
  'Go': '#00ADD8', 'Rust': '#DEA584', 'Java': '#B07219',
  'C++': '#F34B7D', 'C': '#555555', 'Ruby': '#701516',
};

export default function Trending() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setLoading(true);
    automationAPI.listTrending({ page, page_size: 20 })
      .then(r => { setItems(r.data?.items || []); setTotal(r.data?.total || 0); })
      .catch(() => {}).finally(() => setLoading(false));
  }, [page]);

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 16px' }}>
      <Title level={2} style={{ fontFamily: "'Noto Serif SC',serif", color: '#4A3728', marginBottom: 8 }}>
        🔥 GitHub Trending 解读
      </Title>
      <Paragraph style={{ color: '#A0937D', marginBottom: 24 }}>
        每日 GitHub Trending 仓库自动解读（AI 生成中文分析）
      </Paragraph>

      {loading && items.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[1, 2, 3].map(i => <Card key={i} style={{ border: 'none' }}><Skeleton active /></Card>)}
        </div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#A0937D' }}>
          暂无 Trending 数据，请先启用自动化并触发抓取
        </div>
      ) : (
        <List dataSource={items} renderItem={item => (
          <Card hoverable style={{ marginBottom: 16, border: 'none', background: '#FFF' }}
            onClick={() => window.open(item.repo_url, '_blank')} className="fade-in-up">
            <Card.Meta
              title={<div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <GithubOutlined style={{ color: '#24292e' }} />
                <span style={{ fontFamily: "'Noto Serif SC',serif", fontSize: 16 }}>{item.repo_name}</span>
              </div>}
              description={<>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                  {item.language && (
                    <Tag style={{ borderRadius: 6, background: LANG_COLORS[item.language] || '#8B5E3C', color: '#FFF', border: 'none' }}>
                      {item.language}
                    </Tag>
                  )}
                  {item.stars_today > 0 && (
                    <Tag icon={<StarOutlined />} color="#D4A574" style={{ borderRadius: 6 }}>
                      {item.stars_today} stars today
                    </Tag>
                  )}
                  {item.total_stars > 0 && (
                    <span style={{ color: '#C4B5A5', fontSize: 13 }}>
                      ⭐ {item.total_stars.toLocaleString()} total
                    </span>
                  )}
                  <span style={{ color: '#C4B5A5', fontSize: 13 }}>
                    <CalendarOutlined /> {item.fetched_date}
                  </span>
                </div>
                {item.description && (
                  <Paragraph ellipsis={{ rows: 2 }} style={{ color: '#A0937D', marginBottom: 8 }}>
                    {item.description}
                  </Paragraph>
                )}
                {item.ai_interpretation && (
                  <div style={{
                    background: 'linear-gradient(135deg, #FDF8F4, #F5EDE6)',
                    padding: '12px 16px',
                    borderRadius: 10,
                    border: '1px solid #E8D5C4',
                  }}>
                    <Tag icon={<RobotOutlined />} color="#87d068" style={{ borderRadius: 6, marginBottom: 6 }}>
                      AI 解读
                    </Tag>
                    <Paragraph style={{ color: '#4A3728', marginBottom: 0, fontSize: 14 }}>
                      {item.ai_interpretation}
                    </Paragraph>
                  </div>
                )}
              </>}
            />
          </Card>
        )} />
      )}

      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <Pagination current={page} total={total} pageSize={20} onChange={setPage} showSizeChanger={false} />
      </div>
    </div>
  );
}
