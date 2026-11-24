import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext.jsx';
import { api } from '../api.js';

export default function Register() {
  const [form, setForm] = useState({ full_name: '', phone: '', username: '', password: '' });
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      const data = await api.registerMatchmaker(form);
      login(data.token, data.user);
      navigate('/matchmaker');
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page narrow">
      <h1>Matchmaker Registration</h1>
      <form className="card-form" onSubmit={handleSubmit}>
        <label>Full Name</label>
        <input value={form.full_name} onChange={(e) => update('full_name', e.target.value)} required />
        <label>Phone</label>
        <input value={form.phone} onChange={(e) => update('phone', e.target.value)} />
        <label>Username</label>
        <input value={form.username} onChange={(e) => update('username', e.target.value)} required />
        <label>Password</label>
        <input type="password" value={form.password} onChange={(e) => update('password', e.target.value)} required />
        {error && <p className="error">{error}</p>}
        <button className="btn-primary" type="submit">Create Account</button>
      </form>
    </div>
  );
}
