import { useEffect, useState, useCallback } from 'react';
import { Card, List, Pagination, Tag, Spin, Skeleton, Typography, Button, message, DatePicker, Space } from 'antd';
import { FileTextOutlined, UserOutlined, CalendarOutlined, LinkOutlined, RobotOutlined, SyncOutlined } from '@ant-design/icons';
import { automationAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';

const { Title, Paragraph } = Typography;

const CATEGORIES = ['cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.IR', 'cs.NE'];

export default function Papers() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [availableDates, setAvailableDates] = useState([]);
  const { isAuthor } = useAuth();

  const fetchData = useCallback(() => {
    setLoading(true);
    automationAPI.listPapers({ page, page_size: 20, category, date: selectedDate })
      .then(r => {
        setItems(r.data?.items || []);
        setTotal(r.data?.total || 0);
        setAvailableDates(r.data?.available_dates || []);
      })
      .catch(() => {}).finally(() => setLoading(false));
  }, [page, category, selectedDate]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCategory = (cat) => { setCategory(cat); setPage(1); };

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const res = await automationAPI.triggerPapers();
      message.success(res.msg || '抓取完成');
      fetchData();
    } catch (err) { message.error(err?.msg || '触发失败，请确认已登录作者账号'); }
    finally { setTriggering(false); }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <Title level={2} style={{ fontFamily: "'Noto Serif SC',serif", color: '#4A3728', marginBottom: 8 }}>
            <FileTextOutlined style={{ marginRight: 8 }} />AI 论文速递
          </Title>
          <Paragraph style={{ color: '#A0937D', marginBottom: 0 }}>
            Arxiv 最新 AI 论文自动抓取与中文摘要 · 每天 18:00 更新 · 保留 15 天
          </Paragraph>
        </div>
        {isAuthor && (
          <Button type="primary" icon={<SyncOutlined spin={triggering} />} loading={triggering}
            onClick={handleTrigger}
            style={{ background: '#8B5E3C', borderColor: '#8B5E3C', borderRadius: 8 }}>
            触发抓取
          </Button>
        )}
      </div>

      <Space wrap style={{ marginBottom: 16, marginTop: 24 }}>
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
        <DatePicker
          value={selectedDate ? dayjs(selectedDate) : null}
          onChange={(d) => { setSelectedDate(d ? d.format('YYYY-MM-DD') : ''); setPage(1); }}
          placeholder="按日期筛选"
          style={{ borderRadius: 8 }}
          allowClear
        />
      </Space>

      {availableDates.length > 0 && !selectedDate && (
        <div style={{ marginBottom: 16, display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ color: '#A0937D', fontSize: 13, marginRight: 4 }}>📅 最近日期:</span>
          {availableDates.slice(0, 10).map(d => (
            <Tag key={d.date} color="#E8D5C4" style={{ cursor: 'pointer', borderRadius: 6, fontSize: 12 }}
              onClick={() => { setSelectedDate(d.date); setPage(1); }}>
              {d.date} ({d.count})
            </Tag>
          ))}
        </div>
      )}

      {loading && items.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[1, 2, 3].map(i => <Card key={i} style={{ border: 'none' }}><Skeleton active /></Card>)}
        </div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#A0937D' }}>
          {selectedDate ? `${selectedDate} 暂无数据` : '暂无论文摘要'}<br />
          {isAuthor && <Button type="link" onClick={handleTrigger} loading={triggering} style={{ marginTop: 12 }}>点击触发首次抓取</Button>}
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
