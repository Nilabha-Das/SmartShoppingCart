import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('LOCKED'); // LOCKED, VERIFYING, GREETING, IDLE
  const [error, setError] = useState(null);

  useEffect(() => {
    const savedToken = localStorage.getItem('cart_auth_token');
    const savedUser = localStorage.getItem('cart_user_profile');
    if (savedToken && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
        setStatus('IDLE');
      } catch (e) {
        logout();
      }
    }
  }, []);

  const verifyUser = async (credentials = {}) => {
    setStatus('VERIFYING');
    setError(null);
    try {
      // Attempt backend verification or fallback to mock mode
      let res;
      try {
        res = await api.post('/auth/verify', credentials);
      } catch (err) {
        // Dev fallback mode if backend is offline
        if (import.meta.env.DEV) {
          await new Promise((r) => setTimeout(r, 1200));
          res = {
            data: {
              token: 'mock-jwt-token-98765',
              user: { name: 'Alex Johnson', id: 'USR-8821', storeId: 'Store-04' },
            },
          };
        } else {
          throw err;
        }
      }

      const { token, user: userData } = res.data;
      localStorage.setItem('cart_auth_token', token);
      localStorage.setItem('cart_user_profile', JSON.stringify(userData));
      setUser(userData);
      setStatus('GREETING');
      return userData;
    } catch (err) {
      setError(err.response?.data?.message || 'Verification failed. Please check cart terminal.');
      setStatus('ERROR');
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('cart_auth_token');
    localStorage.removeItem('cart_user_profile');
    setUser(null);
    setStatus('LOCKED');
  };

  return (
    <AuthContext.Provider value={{ user, status, setStatus, error, verifyUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);