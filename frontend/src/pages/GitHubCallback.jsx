import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Spin, message } from 'antd';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../api/client';

export default function GitHubCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setAuth } = useAuth();

  useEffect(() => {
    const code = searchParams.get('code');
    if (!code) {
      navigate('/login');
      return;
    }

    authAPI.githubCallback(code)
      .then((res) => {
        setAuth(res.data.access_token, res.data.user);
        message.success('GitHub 登录成功！');
        navigate('/');
      })
      .catch(() => {
        message.error('GitHub 登录失败');
        navigate('/login');
      });
  }, []);

  return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
}
