import { useEffect, useState } from 'react';
import { Card, List, Pagination, Tag, Spin, Skeleton, Typography } from 'antd';
import { CalendarOutlined, LinkOutlined, RobotOutlined } from '@ant-design/icons';
import { automationAPI } from '../api/client';

const { Title, Paragraph } = Typography;

export default function Digests() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    setLoading(true);
    automationAPI.listDigests({ page, page_size: 20, source_type: filter })
      .then(r => { setItems(r.data?.items || []); setTotal(r.data?.total || 0); })
      .catch(() => {}).finally(() => setLoading(false));
  }, [page, filter]);

  const handleFilter = (type) => { setFilter(type); setPage(1); };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 16px' }}>
      <Title level={2} style={{ fontFamily: "'Noto Serif SC',serif", color: '#4A3728', marginBottom: 8 }}>
        📰 AI 资讯摘要
      </Title>
      <Paragraph style={{ color: '#A0937D', marginBottom: 24 }}>
        自动抓取科技资讯并生成 AI 中文摘要
      </Paragraph>

      <div style={{ marginBottom: 24, display: 'flex', gap: 8 }}>
        {['', 'news', 'conference'].map(t => (
          <Tag key={t} color={filter === t ? '#D4A574' : '#E8D5C4'}
            style={{ cursor: 'pointer', borderRadius: 8, padding: '2px 12px', color: filter === t ? '#FFF' : '#8B5E3C' }}
            onClick={() => handleFilter(t)}>
            {t === '' ? '全部' : t === 'news' ? '📰 新闻' : '🎤 大会'}
          </Tag>
        ))}
      </div>

      {loading && items.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[1, 2, 3].map(i => <Card key={i} style={{ border: 'none' }}><Skeleton active /></Card>)}
        </div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#A0937D' }}>
          暂无资讯摘要，请先启用自动化并触发抓取
        </div>
      ) : (
        <List dataSource={items} renderItem={item => (
          <Card hoverable style={{ marginBottom: 16, border: 'none', background: '#FFF' }}
            onClick={() => window.open(item.source_url, '_blank')}>
            <Card.Meta
              title={<span style={{ fontFamily: "'Noto Serif SC',serif", fontSize: 16 }}>{item.title}</span>}
              description={<>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
                  <Tag color="#D4A574" style={{ borderRadius: 6 }}>{item.source_name}</Tag>
                  {item.is_processed
                    ? <Tag icon={<RobotOutlined />} color="#87d068" style={{ borderRadius: 6 }}>AI 摘要</Tag>
                    : <Tag color="#E8D5C4" style={{ borderRadius: 6 }}>原始</Tag>}
                  {item.published_date && (
                    <span style={{ color: '#C4B5A5', fontSize: 13 }}>
                      <CalendarOutlined /> {new Date(item.published_date).toLocaleDateString('zh-CN')}
                    </span>
                  )}
                </div>
                <Paragraph ellipsis={{ rows: 3 }} style={{ color: '#A0937D', marginBottom: 8 }}>
                  {item.content || (item.raw_data?.summary || '暂无摘要')}
                </Paragraph>
                {item.source_url && (
                  <span style={{ color: '#8B5E3C', fontSize: 13 }}>
                    <LinkOutlined /> {item.source_url}
                  </span>
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
