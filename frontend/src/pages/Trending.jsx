import { useEffect, useState, useCallback } from 'react';
import { Card, List, Pagination, Tag, Spin, Skeleton, Typography, Button, message, DatePicker, Space } from 'antd';
import { StarOutlined, GithubOutlined, RobotOutlined, CalendarOutlined, SyncOutlined, FireOutlined } from '@ant-design/icons';
import { automationAPI } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';

const { Title, Paragraph } = Typography;

const LANG_COLORS = {
  'Python': '#3572A5', 'JavaScript': '#F7DF1E', 'TypeScript': '#3178C6',
  'Go': '#00ADD8', 'Rust': '#DEA584', 'Java': '#B07219',
  'C++': '#F34B7D', 'C': '#555555', 'Ruby': '#701516',
};

export default function Trending() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [selectedDate, setSelectedDate] = useState('');
  const [availableDates, setAvailableDates] = useState([]);
  const { isAuthor } = useAuth();

  const fetchData = useCallback(() => {
    setLoading(true);
    automationAPI.listTrending({ page, page_size: 20, date: selectedDate })
      .then(r => {
        setItems(r.data?.items || []);
        setTotal(r.data?.total || 0);
        setAvailableDates(r.data?.available_dates || []);
      })
      .catch(() => {}).finally(() => setLoading(false));
  }, [page, selectedDate]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const res = await automationAPI.triggerTrending();
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
            <FireOutlined style={{ marginRight: 8, color: '#D4A574' }} />GitHub Trending 解读
          </Title>
          <Paragraph style={{ color: '#A0937D', marginBottom: 0 }}>
            每日 GitHub Trending 仓库自动抓取与 AI 中文解读 · 每天 9:00 更新 · 保留 15 天
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

      <div style={{ marginTop: 24, marginBottom: 16 }}>
        <DatePicker
          value={selectedDate ? dayjs(selectedDate) : null}
          onChange={(d) => { setSelectedDate(d ? d.format('YYYY-MM-DD') : ''); setPage(1); }}
          placeholder="按日期筛选"
          style={{ borderRadius: 8 }}
          allowClear
        />
      </div>

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
          {selectedDate ? `${selectedDate} 暂无数据` : '暂无 Trending 数据'}<br />
          {isAuthor && <Button type="link" onClick={handleTrigger} loading={triggering} style={{ marginTop: 12 }}>点击触发首次抓取</Button>}
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
