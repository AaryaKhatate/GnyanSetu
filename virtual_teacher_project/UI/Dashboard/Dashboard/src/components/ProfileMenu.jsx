import React, { useEffect, useRef, useState } from 'react';

export default function ProfileMenu() {
  const [open, setOpen] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [user, setUser] = useState({
    email: 'aarya@gmail.com',  // Your email as fallback
    name: 'Aarya'  // Your name as fallback
  });
  const ref = useRef(null);
  
  // Load user data from storage on component mount
  useEffect(() => {
    const loadUserData = () => {
      console.log("🔍 ProfileMenu: Loading user data...");
      
      // Try to get user data from localStorage
      const storedUser = localStorage.getItem('user');
      const userId = sessionStorage.getItem('userId') || localStorage.getItem('userId');
      const userEmail = sessionStorage.getItem('userEmail') || localStorage.getItem('userEmail');
      const userName = sessionStorage.getItem('userName') || localStorage.getItem('userName');
      
      console.log("📦 Storage check:", {
        storedUser: storedUser ? "Found" : "Missing",
        userId,
        userEmail,
        userName
      });
      
      if (storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setUser({
            email: parsedUser.email || userEmail || 'aarya@gmail.com',
            name: parsedUser.full_name || parsedUser.name || userName || 'Aarya',
            id: parsedUser.id || userId,
            username: parsedUser.username || parsedUser.email?.split('@')[0],
            profile_picture: parsedUser.profile_picture,
            google_id: parsedUser.google_id,
            learning_level: parsedUser.learning_level || 'beginner',
            is_verified: parsedUser.is_verified
          });
          console.log('✅ User data loaded from storage:', parsedUser);
        } catch (e) {
          console.error('❌ Error parsing user data:', e);
          // Use individual fields if JSON parse fails
          if (userEmail || userName) {
            setUser({
              email: userEmail || 'aarya@gmail.com',
              name: userName || 'Aarya',
              id: userId
            });
          }
        }
      } else if (userId || userEmail || userName) {
        // If no full user object but we have individual fields
        setUser({
          email: userEmail || 'aarya@gmail.com',
          name: userName || 'Aarya',
          id: userId
        });
        console.log('✅ User data from session:', { userId, userEmail, userName });
      } else {
        console.warn('⚠️ No user data found in storage - using fallback');
      }
    };
    
    loadUserData();
  }, []);

  const getUserInitials = (name) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to logout?')) {
      try {
        // Get tokens for logout request
        const refreshToken = localStorage.getItem('refresh_token');
        const accessToken = localStorage.getItem('access_token') || localStorage.getItem('gnyansetu_auth_token');
        
        // Call logout API to invalidate session
        if (accessToken) {
          try {
            await fetch('http://localhost:8000/api/auth/logout/', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
              },
              body: JSON.stringify({
                refresh_token: refreshToken
              })
            });
            console.log('✅ Logout API called successfully');
          } catch (error) {
            console.error('❌ Logout API error (continuing anyway):', error);
            // Continue with logout even if API fails
          }
        }
        
        // Clear all storage
        sessionStorage.clear();
        localStorage.removeItem('userId');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('userName');
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('gnyansetu_auth_token');
        localStorage.removeItem('currentConversationId');
        localStorage.removeItem('lessonId');
        
        console.log('✅ User logged out - storage cleared');
        
        // Redirect to landing page
        window.location.href = 'http://localhost:3000';
      } catch (error) {
        console.error('❌ Logout error:', error);
        // Still redirect to landing page even on error
        window.location.href = 'http://localhost:3000';
      }
    }
  };

  useEffect(() => {
    const onClick = (e) => {
      if (!ref.current) return;
      if (!ref.current.contains(e.target)) {
        setOpen(false);
        setShowProfile(false);
      }
    };
    const onEsc = (e) => {
      if (e.key === 'Escape') {
        setOpen(false);
        setShowProfile(false);
      }
    };
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onEsc);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onEsc);
    };
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="h-9 w-9 rounded-full bg-gradient-to-tr from-indigo-500 to-blue-500 ring-2 ring-slate-700/60 hover:ring-indigo-500/40 transition-shadow flex items-center justify-center text-white text-sm font-medium"
      >
        {user.profile_picture ? (
          <img src={user.profile_picture} alt={user.name} className="w-full h-full rounded-full object-cover" />
        ) : (
          getUserInitials(user.name)
        )}
      </button>
      
      {/* Dropdown Menu */}
      <div
        className={`absolute right-0 mt-3 w-56 rounded-xl border border-slate-700/60 bg-slate-900/95 backdrop-blur p-2 shadow-xl transition-all duration-200 ${open && !showProfile ? 'opacity-100 translate-y-0' : 'pointer-events-none opacity-0 -translate-y-1'}`}
        role="menu"
      >
        <div className="px-3 py-2 text-sm text-slate-300">
          Signed in as<br />
          <span className="text-white font-medium">{user.name}</span><br />
          <span className="text-slate-400 text-xs">{user.email}</span>
          {user.google_id && (
            <div className="mt-1 flex items-center gap-1 text-xs text-blue-400">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              <span>Google</span>
            </div>
          )}
        </div>
        <hr className="border-slate-700/60 my-1" />
        <button 
          onClick={() => {
            setShowProfile(true);
            setOpen(false);
          }}
          className="w-full text-left rounded-lg px-3 py-2 text-sm text-slate-200 hover:bg-slate-800/70" 
          role="menuitem"
        >
          View Profile
        </button>
        <button 
          onClick={handleLogout}
          className="w-full text-left rounded-lg px-3 py-2 text-sm text-rose-300 hover:bg-rose-900/40" 
          role="menuitem"
        >
          Logout
        </button>
      </div>

      {/* Profile Details Modal */}
      {showProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-slate-900 rounded-xl border border-slate-700 shadow-2xl max-w-md w-full mx-4 overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-500 to-blue-500 p-6 text-center">
              <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-white/10 backdrop-blur flex items-center justify-center text-white text-2xl font-bold overflow-hidden">
                {user.profile_picture ? (
                  <img src={user.profile_picture} alt={user.name} className="w-full h-full object-cover" />
                ) : (
                  getUserInitials(user.name)
                )}
              </div>
              <h2 className="text-2xl font-bold text-white">{user.name}</h2>
              <p className="text-blue-100 text-sm mt-1">{user.email}</p>
            </div>

            {/* Body */}
            <div className="p-6 space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                  <span className="text-slate-400 text-sm">User ID</span>
                  <span className="text-white text-sm font-mono">{user.id || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                  <span className="text-slate-400 text-sm">Username</span>
                  <span className="text-white text-sm">{user.username || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                  <span className="text-slate-400 text-sm">Learning Level</span>
                  <span className="text-white text-sm capitalize">{user.learning_level || 'beginner'}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                  <span className="text-slate-400 text-sm">Account Status</span>
                  <span className={`text-sm ${user.is_verified ? 'text-green-400' : 'text-yellow-400'}`}>
                    {user.is_verified ? '✓ Verified' : 'Unverified'}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                  <span className="text-slate-400 text-sm">Login Method</span>
                  <span className="text-white text-sm flex items-center gap-1">
                    {user.google_id ? (
                      <>
                        <svg className="w-4 h-4 text-blue-400" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                        </svg>
                        <span>Google</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <span>Email</span>
                      </>
                    )}
                  </span>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 pt-2 flex gap-3">
              <button
                onClick={() => setShowProfile(false)}
                className="flex-1 px-4 py-2 rounded-lg bg-slate-800 text-white hover:bg-slate-700 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowProfile(false);
                  handleLogout();
                }}
                className="flex-1 px-4 py-2 rounded-lg bg-rose-600 text-white hover:bg-rose-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}






