import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthCallback = ({ onLogin }) => {
  const [processing, setProcessing] = useState(true);

  useEffect(() => {
    const processSessionId = async () => {
      // Check for session_id in URL fragment
      const fragment = window.location.hash;
      const sessionMatch = fragment.match(/session_id=([^&]+)/);
      
      if (sessionMatch) {
        const sessionId = sessionMatch[1];
        
        try {
          const response = await axios.post(`${API}/auth/session-data`, {}, {
            headers: {
              'X-Session-ID': sessionId
            }
          });
          
          // Clean URL fragment
          window.history.replaceState(null, null, window.location.pathname);
          
          // Call onLogin with user data and session token
          onLogin(response.data.user, response.data.session_token);
          
        } catch (error) {
          console.error('Session processing error:', error);
          toast.error('Authentication failed. Please try again.');
          // Redirect to landing page on error
          window.location.href = '/';
        }
      } else {
        // No session_id, check if user is already authenticated
        try {
          const response = await axios.get(`${API}/auth/me`);
          onLogin(response.data, null); // Already has session
        } catch (error) {
          // Not authenticated, redirect to landing
          window.location.href = '/';
        }
      }
      
      setProcessing(false);
    };

    processSessionId();
  }, [onLogin]);

  if (processing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center" data-testid="auth-processing">
        <div className="text-center max-w-md">
          <div className="mb-6">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-slate-300 border-t-slate-800 mx-auto"></div>
          </div>
          <h2 className="text-2xl font-semibold text-slate-800 mb-2 font-space">Processing Authentication</h2>
          <p className="text-slate-600">Please wait while we securely log you in...</p>
        </div>
      </div>
    );
  }

  return null;
};

export default AuthCallback;
