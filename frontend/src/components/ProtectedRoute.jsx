import { Navigate } from 'react-router-dom';
import { useAuth } from '../AuthContext.jsx';

export default function ProtectedRoute({ role, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/matchmaker-login" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;
  return children;
}
