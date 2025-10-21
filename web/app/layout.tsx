import '../styles/globals.css';
import React from 'react';
import HeaderClient from '../components/HeaderClient';

export const metadata = {
  title: 'Pulse',
  description: 'AI Emotional Health Companion',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        {/* ✅ Client-side header */}
        <HeaderClient />

        <main className="max-w-4xl mx-auto px-4 py-8">{children}</main>

        <footer className="border-t bg-white py-3 mt-8 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} Pulse — AI Emotional Health Companion
        </footer>
      </body>
    </html>
  );
}
