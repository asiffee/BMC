import { useEffect, useState } from 'react';
import { api } from '../api.js';

export default function AdminDashboard() {
  const [posts, setPosts] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [image, setImage] = useState(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  function loadAll() {
    api.getPosts().then(setPosts).catch((e) => setError(e.message));
    api.getProfiles().then(setProfiles).catch((e) => setError(e.message));
  }

  useEffect(loadAll, []);

  async function handlePostSubmit(e) {
    e.preventDefault();
    setError('');
    setMessage('');
    const fd = new FormData();
    fd.append('title', title);
    fd.append('content', content);
    if (image) fd.append('image', image);
    try {
      await api.createPost(fd);
      setTitle('');
      setContent('');
      setImage(null);
      setMessage('Post published to Home page.');
      loadAll();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeletePost(id) {
    if (!confirm('Delete this post?')) return;
    await api.deletePost(id).catch((e) => setError(e.message));
    loadAll();
  }

  async function handleDeleteProfile(id) {
    if (!confirm('Delete this profile?')) return;
    await api.deleteProfile(id).catch((e) => setError(e.message));
    loadAll();
  }

  return (
    <div className="page">
      <h1>Admin Panel</h1>
      <p className="muted">Full access: manage Home page posts and every matchmaker's profiles.</p>

      <h2 className="section-title">Publish a Home Page Post</h2>
      <form className="card-form" onSubmit={handlePostSubmit} encType="multipart/form-data">
        <label>Title</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        <label>Content</label>
        <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={4} />
        <label>Image (optional)</label>
        <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} />
        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}
        <button className="btn-primary" type="submit">Publish</button>
      </form>

      <div className="post-grid">
        {posts.map((p) => (
          <article key={p.id} className="post-card">
            {p.image_url && <img src={p.image_url} alt={p.title} />}
            <div className="post-body">
              <h3>{p.title}</h3>
              <p>{p.content}</p>
              <button className="btn-ghost small" onClick={() => handleDeletePost(p.id)}>Delete</button>
            </div>
          </article>
        ))}
      </div>

      <h2 className="section-title">All Registered Profiles (Full Access)</h2>
      <div className="profile-grid">
        {profiles.map((p) => (
          <div key={p.id} className="profile-card">
            {p.photo_url && <img src={p.photo_url} alt={p.full_name} />}
            <h3>{p.full_name}</h3>
            <p>{p.gender === 'male' ? 'Groom' : 'Bride'} · Age {p.age || '—'}</p>
            <p>Father: {p.father_name || '—'}</p>
            <p>Phone: {p.phone || '—'}</p>
            <p>Address: {p.address || '—'}</p>
            <p>Caste: {p.caste || '—'}</p>
            <p>Education: {p.education || '—'}</p>
            <button className="btn-ghost small" onClick={() => handleDeleteProfile(p.id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}
