import '../styles/globals.css';
import React from 'react';
import Link from 'next/link';
import AuthForm from '../components/AuthForm';

export const metadata = {
  title: 'Pulse',
  description: 'AI Emotional Health Companion'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <header className="w-full bg-white shadow-sm">
          <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
            <Link href="/" className="text-2xl font-semibold text-indigo-600">Pulse</Link>
            <div className="flex items-center gap-4">
              <nav className="space-x-4">
                <Link href="/mood" className="text-sm text-slate-700">Mood</Link>
                <Link href="/map" className="text-sm text-slate-700">Mood Map</Link>
              </nav>
              <AuthForm />
            </div>
          </div>
        </header>
        <main className="max-w-4xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
