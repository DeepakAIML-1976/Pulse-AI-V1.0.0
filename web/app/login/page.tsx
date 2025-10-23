'use client';

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabaseClient';
import { useRouter, useSearchParams } from 'next/navigation';
export const dynamic = 'force-dynamic';
export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  // ✅ Detect if user is already logged in (persistent session)
  useEffect(() => {
    const checkSession = async () => {
      const { data } = await supabase.auth.getSession();
      if (data?.session?.user) router.push('/chat');
    };
    checkSession();

    const { data: listener } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session?.user) router.push('/chat');
      if (event === 'SIGNED_OUT') router.push('/login');
    });

    return () => {
      listener?.subscription.unsubscribe();
    };
  }, [router]);

  // ✅ Detect confirmation redirect from Supabase (Bug #3 fix)
  useEffect(() => {
    const confirmed = searchParams.get('type');
    if (confirmed === 'signup') {
      setMessage({
        type: 'success',
        text: '✅ Your email has been verified successfully! You can now log in.',
      });
    }
  }, [searchParams]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setLoading(true);

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        const msg = error.message.toLowerCase();

        if (msg.includes('email not confirmed') || msg.includes('verify')) {
          setMessage({
            type: 'error',
            text:
              '⚠️ Please verify your email before logging in. Check your inbox for the confirmation link.',
          });
        } else if (msg.includes('invalid login') || msg.includes('invalid credentials')) {
          setMessage({
            type: 'error',
            text: '❌ Invalid email or password. Please try again.',
          });
        } else {
          setMessage({
            type: 'error',
            text: 'Login failed. Please try again later.',
          });
        }

        setLoading(false);
        return;
      }

      if (data?.user && !data.user.confirmed_at) {
        setMessage({
          type: 'error',
          text:
            '⚠️ Your account isn’t verified yet. Please confirm your email before continuing.',
        });
        setLoading(false);
        return;
      }

      setMessage({ type: 'success', text: '✅ Login successful! Redirecting...' });
      setTimeout(() => router.push('/chat'), 1200);
    } catch (err: any) {
      console.error('Login error:', err);
      setMessage({
        type: 'error',
        text: 'Unexpected error occurred. Please try again later.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    setMessage({ type: 'success', text: '✅ Signed out successfully.' });
  };

  return (
    <div className="max-w-md mx-auto mt-12">
      <h1 className="text-2xl font-semibold mb-4">Welcome Back</h1>

      {message && (
        <div
          className={`mb-4 p-3 rounded ${
            message.type === 'error'
              ? 'bg-red-50 border border-red-200 text-red-700'
              : 'bg-green-50 border border-green-200 text-green-700'
          }`}
        >
          {message.text}
        </div>
      )}

      <form onSubmit={handleLogin} className="bg-white p-6 rounded shadow space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input
            type="email"
            className="w-full border rounded px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="you@example.com"
            disabled={loading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Password</label>
          <input
            type="password"
            className="w-full border rounded px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="Enter your password"
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 rounded text-white ${
            loading ? 'bg-indigo-400' : 'bg-indigo-600 hover:bg-indigo-700'
          }`}
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      <p className="mt-4 text-sm text-gray-600 text-center">
        Don’t have an account?{' '}
        <a href="/signup" className="text-indigo-600 hover:underline">
          Create one
        </a>
      </p>

      <div className="mt-6 text-center">
        <button
          onClick={handleSignOut}
          className="text-sm text-gray-500 hover:text-red-500 underline"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}
