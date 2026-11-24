import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext.jsx';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/');
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        Bandhan <span>Marriage Consultant</span>
      </Link>
      <div className="nav-links">
        <Link to="/">Home</Link>
        <Link to="/contact">Contact</Link>
        {!user && <Link to="/matchmaker-login">Matchmaker Login</Link>}
        {user?.role === 'matchmaker' && <Link to="/matchmaker">Matchmaker Panel</Link>}
        {user?.role === 'admin' && <Link to="/admin">Admin Panel</Link>}
        {user && (
          <button className="btn-ghost" onClick={handleLogout}>
            Logout ({user.full_name})
          </button>
        )}
      </div>
    </nav>
  );
}
