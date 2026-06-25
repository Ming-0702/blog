import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout, ConfigProvider } from 'antd';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import PostList from './pages/PostList';
import PostDetail from './pages/PostDetail';
import CreatePost from './pages/CreatePost';
import EditPost from './pages/EditPost';
import GitHubCallback from './pages/GitHubCallback';
import UserSettings from './pages/UserSettings';
import Digests from './pages/Digests';
import Trending from './pages/Trending';
import './App.css';

const { Content, Footer } = Layout;

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#8B5E3C',
          borderRadius: 12,
          fontFamily: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif",
          colorText: '#4A3728',
          colorBgContainer: '#FFFFFF',
          colorBorder: '#E8D5C4',
          colorLink: '#8B5E3C',
        },
      }}
    >
      <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Layout style={{ minHeight: '100vh', background: '#FDF8F4' }}>
            <Navbar />
            <Content style={{ paddingBottom: 48 }}>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/posts" element={<PostList />} />
                <Route path="/posts/new" element={<CreatePost />} />
                <Route path="/posts/:id" element={<PostDetail />} />
                <Route path="/posts/:id/edit" element={<EditPost />} />
                <Route path="/auth/github/callback" element={<GitHubCallback />} />
                <Route path="/settings" element={<UserSettings />} />
                <Route path="/digests" element={<Digests />} />
                <Route path="/trending" element={<Trending />} />
              </Routes>
            </Content>
            <Footer style={{
              textAlign: 'center',
              background: '#2D2420',
              color: '#A0937D',
              padding: '32px 16px',
              fontSize: 14,
            }}>
              <div style={{ fontFamily: "'Noto Serif SC', serif", fontSize: 16, color: '#D4A574', marginBottom: 8 }}>
                时不时丢点东西的神秘盒子
              </div>
              <div>偶尔更新，随心记录</div>
              <div style={{ marginTop: 8, opacity: 0.6 }}>
                &copy; {new Date().getFullYear()} &mdash; Built with React + FastAPI
              </div>
            </Footer>
          </Layout>
        </BrowserRouter>
      </AuthProvider>
      </ThemeProvider>
    </ConfigProvider>
  );
}

export default App;
