'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '../lib/supabaseClient';

export default function HeaderClient() {
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    // Load Supabase session
    supabase.auth.getUser().then(({ data }) => {
      setUserEmail(data.user?.email || null);
    });

    // Listen for login/logout
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserEmail(session?.user?.email || null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUserEmail(null);
    window.location.href = '/login';
  };

  return (
    <header className="w-full bg-white shadow-sm">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="text-2xl font-semibold text-indigo-600">
          Pulse
        </Link>

        <div className="flex items-center gap-4">
          <nav className="space-x-4">
            <Link href="/mood" className="text-sm text-slate-700 hover:text-indigo-600">
              Mood
            </Link>
            <Link href="/chat" className="text-sm text-slate-700 hover:text-indigo-600">
              Chat
            </Link>
            <Link href="/map" className="text-sm text-slate-700 hover:text-indigo-600">
              Mood Map
            </Link>
          </nav>

          {userEmail ? (
            <div className="flex items-center gap-3 text-sm">
              <span className="text-slate-600 hidden sm:inline">{userEmail}</span>
              <button
                onClick={handleLogout}
                className="px-3 py-1 border rounded text-slate-700 hover:bg-slate-100"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="space-x-3 text-sm">
              <Link href="/login" className="text-indigo-600 hover:underline">
                Login
              </Link>
              <Link href="/signup" className="text-indigo-600 hover:underline">
                Signup
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
