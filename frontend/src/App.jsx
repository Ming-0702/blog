import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout, ConfigProvider } from 'antd';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import PostList from './pages/PostList';
import PostDetail from './pages/PostDetail';
import CreatePost from './pages/CreatePost';
import EditPost from './pages/EditPost';
import './App.css';

const { Content, Footer } = Layout;

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 8,
        },
      }}
    >
      <AuthProvider>
        <BrowserRouter>
          <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
            <Navbar />
            <Content>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/posts" element={<PostList />} />
                <Route path="/posts/new" element={<CreatePost />} />
                <Route path="/posts/:id" element={<PostDetail />} />
                <Route path="/posts/:id/edit" element={<EditPost />} />
              </Routes>
            </Content>
            <Footer style={{ textAlign: 'center', background: '#f5f5f5' }}>
              MyBlog ©{new Date().getFullYear()} - 用 ❤️ 和 FastAPI + React 构建
            </Footer>
          </Layout>
        </BrowserRouter>
      </AuthProvider>
    </ConfigProvider>
  );
}

export default App;
