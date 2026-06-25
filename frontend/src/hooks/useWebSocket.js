import { useEffect, useRef, useState } from 'react';
import { message } from 'antd';

export default function useWebSocket() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const wsRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    const wsUrl = `ws://localhost:8000/ws/notifications?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => console.log('[WS] Connected');
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setNotifications((prev) => [msg, ...prev].slice(0, 50));
        setUnreadCount((prev) => prev + 1);

        if (msg.type === 'new_comment') {
          message.info(`${msg.data.from_user} 评论了你的文章`);
        } else if (msg.type === 'new_reply') {
          message.info(`${msg.data.from_user} 回复了你的评论`);
        }
      } catch { /* ignore */ }
    };
    ws.onclose = () => console.log('[WS] Disconnected');
    ws.onerror = () => console.log('[WS] Error');

    return () => {
      ws.close();
    };
  }, []);

  const clearUnread = () => setUnreadCount(0);

  return { notifications, unreadCount, clearUnread };
}
