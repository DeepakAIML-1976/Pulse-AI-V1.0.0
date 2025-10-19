'use client';
import React, { useState } from 'react';
import { supabase } from '../lib/supabaseClient';

export default function AuthForm() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const signIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOtp({ email });
      if (error) throw error;
      alert(`Check ${email} for the login link (magic link).`);
      setEmail('');
    } catch (err: any) {
      console.error(err);
      alert('Error signing in: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    window.location.reload();
  };

  return (
    <div className="flex items-center gap-2">
      <form onSubmit={signIn} className="flex gap-2">
        <input value={email} onChange={(e)=> setEmail(e.target.value)} placeholder="you@example.com" className="border p-2 rounded" />
        <button disabled={loading} className="px-3 py-2 bg-indigo-600 text-white rounded">{loading ? 'Sending...' : 'Magic Link'}</button>
      </form>
      <button onClick={signOut} className="text-sm text-slate-600">Sign out</button>
    </div>
  );
}
