'use client';

import React, { useState } from 'react';
import { supabase } from '../../lib/supabaseClient';
import { useRouter } from 'next/navigation';
import axios from 'axios';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  const signInPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      const token = data.session?.access_token;
      if (token) {
        await axios.post(`${API_BASE}/api/users/sync`, { access_token: token });
        router.push('/mood');
      }
    } catch (err: any) {
      alert(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const magicLink = async () => {
    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOtp({ email });
      if (error) throw error;
      alert(`Magic link sent to ${email}`);
    } catch (err: any) {
      alert(err.message || 'Magic link failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 bg-white p-6 rounded shadow">
      <h2 className="text-2xl font-bold mb-4 text-center">Sign in to Pulse</h2>
      <form onSubmit={signInPassword} className="space-y-3">
        <input
          type="email"
          placeholder="Email"
          className="w-full border rounded p-2"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          className="w-full border rounded p-2"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
        />
        <div className="flex gap-2">
          <button type="submit" disabled={loading} className="flex-1 bg-indigo-600 text-white py-2 rounded">
            {loading ? 'Loading...' : 'Login'}
          </button>
          <button type="button" onClick={magicLink} disabled={loading} className="flex-1 border py-2 rounded">
            Magic Link
          </button>
        </div>
      </form>
      <p className="text-center mt-4 text-sm">
        Don’t have an account? <a href="/signup" className="text-indigo-600">Sign up</a>
      </p>
    </div>
  );
}
