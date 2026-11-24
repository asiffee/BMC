import { useEffect, useState } from 'react';
import { api } from '../api.js';

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .getPosts()
      .then(setPosts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <section className="hero">
        <h1>Find the Right Match, The Trusted Way</h1>
        <p>Bandhan Marriage Consultant connects families through a trusted network of matchmakers.</p>
      </section>

      <section>
        <h2 className="section-title">Latest Updates</h2>
        {loading && <p>Loading...</p>}
        {error && <p className="error">{error}</p>}
        {!loading && posts.length === 0 && <p>No posts yet. Please check back soon.</p>}
        <div className="post-grid">
          {posts.map((p) => (
            <article key={p.id} className="post-card">
              {p.image_url && <img src={p.image_url} alt={p.title} />}
              <div className="post-body">
                <h3>{p.title}</h3>
                <p>{p.content}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
