'use client';

import React, { useState } from 'react';
import { supabase } from '../../lib/supabaseClient';
import { useRouter } from 'next/navigation';

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'error' | 'success'; text: string } | null>(null);

  const SITE_URL =
    process.env.NEXT_PUBLIC_SITE_URL ||
    (typeof window !== 'undefined' ? window.location.origin : '');

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const redirectTo = `${SITE_URL}/login`; // After confirmation, send them to login

      const { data, error } = await supabase.auth.signUp(
        { email, password },
        { emailRedirectTo: redirectTo }
      );

      if (error) {
        const msg = error.message.toLowerCase();
        if (msg.includes('already registered') || msg.includes('exists')) {
          setMessage({
            type: 'error',
            text: 'User already exists. Please sign in instead.',
          });
        } else {
          setMessage({
            type: 'error',
            text: 'Signup failed. Please try again.',
          });
        }
        setLoading(false);
        return;
      }

      setMessage({
        type: 'success',
        text:
          '✅ A confirmation email has been sent to your inbox. Please verify to complete registration.',
      });

      setEmail('');
      setPassword('');
    } catch (err: any) {
      console.error('Signup error:', err);
      setMessage({ type: 'error', text: 'Unexpected error. Please try again later.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-12">
      <h1 className="text-2xl font-semibold mb-4">Create Account</h1>

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

      <form onSubmit={handleSignup} className="bg-white p-6 rounded shadow space-y-4">
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
            placeholder="Choose a secure password"
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
          {loading ? 'Creating Account...' : 'Sign Up'}
        </button>
      </form>

      <p className="mt-4 text-sm text-gray-600 text-center">
        Already have an account?{' '}
        <a href="/login" className="text-indigo-600 hover:underline">
          Sign in
        </a>
      </p>
    </div>
  );
}
