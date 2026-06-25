import { useEffect, useState, useCallback } from 'react';
import { Card, List, Pagination, Tag, Spin, Skeleton, Typography, Button, message, DatePicker, Space } from 'antd';
import { CalendarOutlined, LinkOutlined, RobotOutlined, SyncOutlined, RocketOutlined, ClearOutlined } from '@ant-design/icons';
import { automationAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';

const { Title, Paragraph } = Typography;

export default function Digests() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [availableDates, setAvailableDates] = useState([]);
  const { isAuthor } = useAuth();

  const fetchData = useCallback(() => {
    setLoading(true);
    automationAPI.listDigests({ page, page_size: 20, source_type: filter, date: selectedDate })
      .then(r => {
        setItems(r.data?.items || []);
        setTotal(r.data?.total || 0);
        setAvailableDates(r.data?.available_dates || []);
      })
      .catch(() => {}).finally(() => setLoading(false));
  }, [page, filter, selectedDate]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleFilter = (type) => { setFilter(type); setPage(1); };

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const res = await automationAPI.triggerDigests();
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
            <RocketOutlined style={{ marginRight: 8 }} />AI 资讯摘要
          </Title>
          <Paragraph style={{ color: '#A0937D', marginBottom: 0 }}>
            每日自动抓取科技资讯并生成 AI 中文摘要 · 每天 8:00 更新 · 保留 {15} 天
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
        {['', 'news', 'conference'].map(t => (
          <Tag key={t} color={filter === t ? '#D4A574' : '#E8D5C4'}
            style={{ cursor: 'pointer', borderRadius: 8, padding: '2px 12px', color: filter === t ? '#FFF' : '#8B5E3C' }}
            onClick={() => handleFilter(t)}>
            {t === '' ? '全部' : t === 'news' ? '📰 新闻' : '🎤 大会'}
          </Tag>
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
          {selectedDate ? `${selectedDate} 暂无数据` : '暂无资讯摘要'}<br />
          {isAuthor && <Button type="link" onClick={handleTrigger} loading={triggering} style={{ marginTop: 12 }}>点击触发首次抓取</Button>}
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
