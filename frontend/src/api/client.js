import axios from 'axios';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// 请求拦截器：自动附加 JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：统一处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error.response?.data || error);
  }
);

export default api;

// ===== 认证 API =====
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  githubLogin: () => api.get('/auth/github/login'),
  githubCallback: (code) => api.get('/auth/github/callback', { params: { code } }),
};

// ===== 博客 API =====
export const postsAPI = {
  list: (params) => api.get('/posts', { params }),
  hot: (params) => api.get('/posts/hot', { params }),
  search: (params) => api.get('/posts/search', { params }),
  random: () => api.get('/posts/random'),
  drafts: () => api.get('/posts/drafts'),
  upload: (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/posts/upload', fd); },
  generateSummary: (data) => api.post('/posts/generate-summary', data),
  listTags: () => api.get('/posts/tags'),
  get: (id) => api.get(`/posts/${id}`),
  create: (data) => api.post('/posts', data),
  update: (id, data) => api.put(`/posts/${id}`, data),
  delete: (id) => api.delete(`/posts/${id}`),
};

// ===== 评论 API =====
export const commentsAPI = {
  list: (postId) => api.get(`/comments/post/${postId}`),
  create: (postId, data) => api.post(`/comments?post_id=${postId}`, data),
  update: (commentId, data) => api.put(`/comments/${commentId}`, data),
  delete: (commentId) => api.delete(`/comments/${commentId}`),
};

// ===== 点赞 API =====
export const likesAPI = {
  toggle: (data) => api.post('/likes', data),
  status: (targetType, targetId) => api.get('/likes/status', { params: { target_type: targetType, target_id: targetId } }),
};

// ===== 用户 API =====
export const usersAPI = {
  get: (userId) => api.get(`/users/${userId}`),
  update: (data) => api.put('/users/me', data),
  uploadAvatar: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/users/me/avatar', formData);
  },
};

// ===== 自动化 API =====
export const automationAPI = {
  listDigests: (params) => api.get('/automation/digests', { params }),
  getDigest: (id) => api.get(`/automation/digests/${id}`),
  triggerDigests: () => api.post('/automation/digests/trigger'),
  listTrending: (params) => api.get('/automation/trending', { params }),
  getTrendingRepo: (id) => api.get(`/automation/trending/${id}`),
  triggerTrending: () => api.post('/automation/trending/trigger'),
  listPapers: (params) => api.get('/automation/papers', { params }),
  getPaper: (id) => api.get(`/automation/papers/${id}`),
  triggerPapers: () => api.post('/automation/papers/trigger'),
  getStatus: () => api.get('/automation/status'),
};
