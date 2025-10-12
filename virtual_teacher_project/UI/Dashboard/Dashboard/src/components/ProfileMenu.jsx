import React, { useEffect, useRef, useState } from "react";

export default function ProfileMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Mock user data - replace with actual user data from your auth system
  const user = {
    email: "john.doe@example.com",
    name: "John Doe",
  };

  const getUserInitials = (name) => {
    return name
      .split(" ")
      .map((word) => word.charAt(0))
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  useEffect(() => {
    const onClick = (e) => {
      if (!ref.current) return;
      if (!ref.current.contains(e.target)) setOpen(false);
    };
    const onEsc = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onEsc);
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
        {/* Empty circle - no initials */}
      </button>
      <div
        className={`absolute right-0 mt-3 w-56 rounded-xl border border-slate-700/60 bg-slate-900/95 backdrop-blur p-2 shadow-xl transition-all duration-200 ${
          open
            ? "opacity-100 translate-y-0"
            : "pointer-events-none opacity-0 -translate-y-1"
        }`}
        role="menu"
      >
        {/* Email and Settings removed - only Sign out */}
        <button
          className="w-full text-left rounded-lg px-3 py-2 text-sm text-rose-300 hover:bg-rose-900/40"
          role="menuitem"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
