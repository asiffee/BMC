import { useEffect, useState } from 'react';
import { useAuth } from '../AuthContext.jsx';
import { api } from '../api.js';

const emptyForm = {
  gender: 'male',
  full_name: '',
  father_name: '',
  phone: '',
  address: '',
  caste: '',
  education: '',
  age: '',
  sisters_count: '',
  brothers_count: '',
  father_alive: 'yes',
  mother_alive: 'yes',
  household_members: '',
};

export default function MatchmakerDashboard() {
  const { user } = useAuth();
  const [form, setForm] = useState(emptyForm);
  const [photo, setPhoto] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  function loadProfiles() {
    api.getProfiles().then(setProfiles).catch((e) => setError(e.message));
  }

  useEffect(loadProfiles, []);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setMessage('');
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));
    if (photo) fd.append('photo', photo);

    try {
      await api.createProfile(fd);
      setMessage('Profile saved successfully.');
      setForm(emptyForm);
      setPhoto(null);
      loadProfiles();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this profile?')) return;
    try {
      await api.deleteProfile(id);
      loadProfiles();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h1>Matchmaker Panel</h1>
      <p className="muted">Welcome, {user?.full_name}. Add a new bride/groom profile below.</p>

      <form className="card-form profile-form" onSubmit={handleSubmit} encType="multipart/form-data">
        <div className="form-grid">
          <div>
            <label>I am adding a</label>
            <select value={form.gender} onChange={(e) => update('gender', e.target.value)}>
              <option value="male">Groom (Male)</option>
              <option value="female">Bride (Female)</option>
            </select>
          </div>
          <div>
            <label>Full Name *</label>
            <input value={form.full_name} onChange={(e) => update('full_name', e.target.value)} required />
          </div>
          <div>
            <label>Father's Name</label>
            <input value={form.father_name} onChange={(e) => update('father_name', e.target.value)} />
          </div>
          <div>
            <label>Phone Number</label>
            <input value={form.phone} onChange={(e) => update('phone', e.target.value)} />
          </div>
          <div>
            <label>Address</label>
            <input value={form.address} onChange={(e) => update('address', e.target.value)} />
          </div>
          <div>
            <label>Caste</label>
            <input value={form.caste} onChange={(e) => update('caste', e.target.value)} />
          </div>
          <div>
            <label>Education</label>
            <input value={form.education} onChange={(e) => update('education', e.target.value)} />
          </div>
          <div>
            <label>Age</label>
            <input type="number" value={form.age} onChange={(e) => update('age', e.target.value)} />
          </div>
          <div>
            <label>Number of Sisters</label>
            <input type="number" value={form.sisters_count} onChange={(e) => update('sisters_count', e.target.value)} />
          </div>
          <div>
            <label>Number of Brothers</label>
            <input type="number" value={form.brothers_count} onChange={(e) => update('brothers_count', e.target.value)} />
          </div>
          <div>
            <label>Father Alive?</label>
            <select value={form.father_alive} onChange={(e) => update('father_alive', e.target.value)}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
          <div>
            <label>Mother Alive?</label>
            <select value={form.mother_alive} onChange={(e) => update('mother_alive', e.target.value)}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
          <div>
            <label>Household Members (people living together)</label>
            <input type="number" value={form.household_members} onChange={(e) => update('household_members', e.target.value)} />
          </div>
          <div>
            <label>Photo</label>
            <input type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files[0])} />
          </div>
        </div>
        {error && <p className="error">{error}</p>}
        {message && <p className="success">{message}</p>}
        <button className="btn-primary" type="submit">Save Profile</button>
      </form>

      <h2 className="section-title">All Profiles</h2>
      <p className="muted">
        You can see full details of profiles you added yourself. For profiles added by other
        matchmakers, phone number and address are hidden.
      </p>
      <div className="profile-grid">
        {profiles.map((p) => (
          <div key={p.id} className="profile-card">
            {p.photo_url && <img src={p.photo_url} alt={p.full_name} />}
            <h3>{p.full_name}</h3>
            <p>{p.gender === 'male' ? 'Groom' : 'Bride'} · Age {p.age || '—'}</p>
            <p>Father: {p.father_name || '—'}</p>
            <p>Caste: {p.caste || '—'}</p>
            <p>Education: {p.education || '—'}</p>
            <p>Phone: {p.restricted ? <span className="locked">🔒 Hidden</span> : p.phone || '—'}</p>
            <p>Address: {p.restricted ? <span className="locked">🔒 Hidden</span> : p.address || '—'}</p>
            {p.matchmaker_id === user.id && (
              <button className="btn-ghost small" onClick={() => handleDelete(p.id)}>Delete</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
