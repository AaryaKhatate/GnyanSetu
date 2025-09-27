import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, User, Settings } from 'lucide-react';

export default function ProfileMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const { user, logout } = useAuth();

  const getUserInitials = (name) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  useEffect(() => {
    const onClick = (e) => {
      if (!ref.current) return;
      if (!ref.current.contains(e.target)) setOpen(false);
    };
    const onEsc = (e) => e.key === 'Escape' && setOpen(false);
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
        {getUserInitials(user.name)}
      </button>
      <div
        className={`absolute right-0 mt-3 w-56 rounded-xl border border-slate-700/60 bg-slate-900/95 backdrop-blur p-2 shadow-xl transition-all duration-200 ${open ? 'opacity-100 translate-y-0' : 'pointer-events-none opacity-0 -translate-y-1'}`}
        role="menu"
      >
        <div className="px-3 py-2 text-sm text-slate-300">
          Signed in as <span className="text-white">{user?.email || 'Unknown'}</span>
        </div>
        <hr className="border-slate-700/60 my-1" />
        
        <button 
          className="w-full text-left rounded-lg px-3 py-2 text-sm text-slate-200 hover:bg-slate-800/70 flex items-center gap-2" 
          role="menuitem"
        >
          <User className="w-4 h-4" />
          Profile
        </button>
        
        <button 
          className="w-full text-left rounded-lg px-3 py-2 text-sm text-slate-200 hover:bg-slate-800/70 flex items-center gap-2" 
          role="menuitem"
        >
          <Settings className="w-4 h-4" />
          Settings
        </button>
        
        <hr className="border-slate-700/60 my-1" />
        
        <button 
          onClick={async () => {
            setOpen(false);
            await logout();
          }}
          className="w-full text-left rounded-lg px-3 py-2 text-sm text-rose-300 hover:bg-rose-900/40 flex items-center gap-2" 
          role="menuitem"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </div>
  );
}


