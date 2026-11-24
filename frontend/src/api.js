const BASE = '/api';

function authHeaders() {
  const token = localStorage.getItem('bandhan_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Something went wrong.');
  return data;
}

export const api = {
  login: (username, password) =>
    fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then(handle),

  registerMatchmaker: (payload) =>
    fetch(`${BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handle),

  getPosts: () => fetch(`${BASE}/posts`).then(handle),

  createPost: (formData) =>
    fetch(`${BASE}/posts`, { method: 'POST', headers: authHeaders(), body: formData }).then(handle),

  deletePost: (id) =>
    fetch(`${BASE}/posts/${id}`, { method: 'DELETE', headers: authHeaders() }).then(handle),

  getProfiles: () => fetch(`${BASE}/profiles`, { headers: authHeaders() }).then(handle),

  createProfile: (formData) =>
    fetch(`${BASE}/profiles`, { method: 'POST', headers: authHeaders(), body: formData }).then(handle),

  updateProfile: (id, formData) =>
    fetch(`${BASE}/profiles/${id}`, { method: 'PUT', headers: authHeaders(), body: formData }).then(handle),

  deleteProfile: (id) =>
    fetch(`${BASE}/profiles/${id}`, { method: 'DELETE', headers: authHeaders() }).then(handle),
};
