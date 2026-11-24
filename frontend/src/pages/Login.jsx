import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../AuthContext.jsx';
import { api } from '../api.js';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      const data = await api.login(username, password);
      login(data.token, data.user);
      navigate(data.user.role === 'admin' ? '/admin' : '/matchmaker');
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page narrow">
      <h1>Login</h1>
      <form className="card-form" onSubmit={handleSubmit}>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="error">{error}</p>}
        <button className="btn-primary" type="submit">Login</button>
      </form>
      <p>
        New matchmaker? <Link to="/matchmaker-register">Register here</Link>
      </p>
    </div>
  );
}
