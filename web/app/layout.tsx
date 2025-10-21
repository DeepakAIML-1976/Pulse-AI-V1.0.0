import '../styles/globals.css';
import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '../lib/supabaseClient';

export const metadata = {
  title: 'Pulse',
  description: 'AI Emotional Health Companion',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    // Load Supabase session on mount
    supabase.auth.getUser().then(({ data }) => {
      setUserEmail(data.user?.email || null);
    });

    // Listen for login/logout changes
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
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
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

        <main className="max-w-4xl mx-auto px-4 py-8">{children}</main>

        <footer className="border-t bg-white py-3 mt-8 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} Pulse — AI Emotional Health Companion
        </footer>
      </body>
    </html>
  );
}
