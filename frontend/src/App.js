import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import Landing from '@/components/Landing';
import Dashboard from '@/components/Dashboard';
import AuthCallback from '@/components/AuthCallback';
import '@/App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios defaults
axios.defaults.withCredentials = true;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionToken, setSessionToken] = useState(null);

  // Check for existing session on app load
  useEffect(() => {
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.log('No existing session');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (userData, token) => {
    setUser(userData);
    setSessionToken(token);
    
    // Set session token in cookie
    document.cookie = `session_token=${token}; path=/; secure; samesite=none; max-age=${7 * 24 * 60 * 60}`;
    
    // Set axios header for future requests
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    
    toast.success('Successfully logged in!');
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    setUser(null);
    setSessionToken(null);
    
    // Clear cookie
    document.cookie = 'session_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    
    // Clear axios header
    delete axios.defaults.headers.common['Authorization'];
    
    toast.success('Successfully logged out!');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-600 mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Loading Manuscript-TM DocWise...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App font-inter">
      <Router>
        <Routes>
          {/* Public routes */}
          <Route 
            path="/" 
            element={
              user ? <Navigate to="/dashboard" replace /> : <Landing onLogin={handleLogin} />
            } 
          />
          
          {/* Auth callback route */}
          <Route 
            path="/dashboard" 
            element={
              !user ? 
                <AuthCallback onLogin={handleLogin} /> : 
                <Dashboard user={user} onLogout={handleLogout} />
            } 
          />
          
          {/* Protected routes */}
          <Route 
            path="/app" 
            element={
              user ? <Dashboard user={user} onLogout={handleLogout} /> : <Navigate to="/" replace />
            } 
          />
        </Routes>
      </Router>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
