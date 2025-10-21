'use client';

import React, { useState } from 'react';
import { supabase } from '../../lib/supabaseClient';
import { useRouter } from 'next/navigation';
import axios from 'axios';

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  const signUp = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { full_name: name } }
      });
      if (error) throw error;

      const token = data.session?.access_token;
      if (token) await axios.post(`${API_BASE}/api/users/sync`, { access_token: token });

      alert('Signup successful! Please check your email to confirm.');
      router.push('/login');
    } catch (err: any) {
      alert(err.message || 'Signup failed');
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 bg-white p-6 rounded shadow">
      <h2 className="text-2xl font-bold mb-4 text-center">Create your Pulse account</h2>
      <form onSubmit={signUp} className="space-y-3">
        <input
          type="text"
          placeholder="Full Name"
          className="w-full border rounded p-2"
          value={name}
          onChange={e => setName(e.target.value)}
          required
        />
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
        <button type="submit" className="w-full bg-indigo-600 text-white py-2 rounded">
          Sign Up
        </button>
      </form>
      <p className="text-center mt-4 text-sm">
        Already have an account? <a href="/login" className="text-indigo-600">Login</a>
      </p>
    </div>
  );
}
