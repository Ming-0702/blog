import { useEffect, useState } from 'react';
import { Card, List, Pagination, Tag, Spin, Skeleton, Typography } from 'antd';
import { FileTextOutlined, UserOutlined, CalendarOutlined, LinkOutlined, RobotOutlined } from '@ant-design/icons';
import { automationAPI } from '../api/client';

const { Title, Paragraph } = Typography;

const CATEGORIES = ['cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.IR', 'cs.NE'];

export default function Papers() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState('');

  useEffect(() => {
    setLoading(true);
    automationAPI.listPapers({ page, page_size: 20, category })
      .then(r => { setItems(r.data?.items || []); setTotal(r.data?.total || 0); })
      .catch(() => {}).finally(() => setLoading(false));
  }, [page, category]);

  const handleCategory = (cat) => { setCategory(cat); setPage(1); };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 16px' }}>
      <Title level={2} style={{ fontFamily: "'Noto Serif SC',serif", color: '#4A3728', marginBottom: 8 }}>
        📄 AI 论文速递
      </Title>
      <Paragraph style={{ color: '#A0937D', marginBottom: 24 }}>
        Arxiv 最新 AI 论文自动抓取与中文摘要
      </Paragraph>

      <div style={{ marginBottom: 24, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Tag color={category === '' ? '#D4A574' : '#E8D5C4'}
          style={{ cursor: 'pointer', borderRadius: 8, padding: '2px 12px',
            color: category === '' ? '#FFF' : '#8B5E3C' }}
          onClick={() => handleCategory('')}>全部</Tag>
        {CATEGORIES.map(cat => (
          <Tag key={cat} color={category === cat ? '#D4A574' : '#E8D5C4'}
            style={{ cursor: 'pointer', borderRadius: 8, padding: '2px 12px',
              color: category === cat ? '#FFF' : '#8B5E3C' }}
            onClick={() => handleCategory(cat)}>{cat}</Tag>
        ))}
      </div>

      {loading && items.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[1, 2, 3].map(i => <Card key={i} style={{ border: 'none' }}><Skeleton active /></Card>)}
        </div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#A0937D' }}>
          暂无论文摘要，请先启用自动化并触发抓取
        </div>
      ) : (
        <List dataSource={items} renderItem={item => (
          <Card hoverable style={{ marginBottom: 16, border: 'none', background: '#FFF' }} className="fade-in-up"
            onClick={() => window.open(item.paper_url, '_blank')}>
            <Card.Meta
              title={<div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <FileTextOutlined style={{ color: '#8B5E3C' }} />
                <span style={{ fontFamily: "'Noto Serif SC',serif", fontSize: 16 }}>{item.title}</span>
              </div>}
              description={<>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8, alignItems: 'center' }}>
                  {item.authors && (
                    <span style={{ color: '#C4B5A5', fontSize: 13 }}>
                      <UserOutlined /> {item.authors.slice(0, 3).join(', ')}
                      {item.authors.length > 3 && ` 等${item.authors.length}人`}
                    </span>
                  )}
                  {item.published_date && (
                    <span style={{ color: '#C4B5A5', fontSize: 13 }}>
                      <CalendarOutlined /> {new Date(item.published_date).toLocaleDateString('zh-CN')}
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
                  {item.categories?.map(c => (
                    <Tag key={c} color="#D4A574" style={{ borderRadius: 6, fontSize: 11 }}>{c}</Tag>
                  ))}
                  <Tag color="#8B5E3C" style={{ borderRadius: 6, fontSize: 11 }}>
                    <LinkOutlined /> {item.arxiv_id}
                  </Tag>
                </div>
                {item.ai_summary_zh && (
                  <div style={{
                    background: 'linear-gradient(135deg, #FDF8F4, #F5EDE6)',
                    padding: '12px 16px',
                    borderRadius: 10,
                    border: '1px solid #E8D5C4',
                    marginBottom: 8,
                  }}>
                    <Tag icon={<RobotOutlined />} color="#87d068" style={{ borderRadius: 6, marginBottom: 6 }}>
                      AI 中文摘要
                    </Tag>
                    <Paragraph style={{ color: '#4A3728', marginBottom: 0, fontSize: 14 }}>
                      {item.ai_summary_zh}
                    </Paragraph>
                  </div>
                )}
                {!item.ai_summary_zh && item.abstract && (
                  <Paragraph ellipsis={{ rows: 2 }} style={{ color: '#A0937D', marginBottom: 0, fontSize: 13 }}>
                    📝 {item.abstract}
                  </Paragraph>
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
