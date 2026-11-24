import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('bandhan_user');
    return saved ? JSON.parse(saved) : null;
  });

  function login(token, userData) {
    localStorage.setItem('bandhan_token', token);
    localStorage.setItem('bandhan_user', JSON.stringify(userData));
    setUser(userData);
  }

  function logout() {
    localStorage.removeItem('bandhan_token');
    localStorage.removeItem('bandhan_user');
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
