import React from 'react';

export default function GlowingBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-indigo-600/20 blur-3xl animate-blob" />
      <div className="absolute top-1/3 -right-24 h-80 w-80 rounded-full bg-blue-500/20 blur-3xl animate-blob" style={{ animationDelay: '2s' }} />
      <div className="absolute bottom-0 left-1/3 h-96 w-96 rounded-full bg-fuchsia-500/10 blur-3xl animate-blob" style={{ animationDelay: '4s' }} />
    </div>
  );
}


