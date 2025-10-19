'use client';
import React, { useState } from 'react';
import axios from 'axios';
import { supabase } from '../lib/supabaseClient';

type Props = { onResult?: (res: any) => void };

export default function MoodForm({ onResult }: Props) {
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!API_BASE) {
    throw new Error('NEXT_PUBLIC_API_BASE_URL not set. See .env.example');
    }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const form = new FormData();
      if (text) form.append('text', text);
      if (file) form.append('file', file as File);

      const session = await supabase.auth.getSession();
      const token = session?.data?.session?.access_token;
      const headers: any = { 'Content-Type': 'multipart/form-data' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const resp = await axios.post(`${API_BASE}/api/mood`, form, { headers });
      onResult?.(resp.data);
      setText('');
      setFile(null);
    } catch (err: any) {
      console.error(err);
      alert('Failed to submit snapshot. Check console.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4 bg-white p-4 rounded shadow-sm">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="How are you feeling? (type a short sentence)"
        className="w-full border rounded p-2 min-h-[100px]"
      />
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2">
          <input type="file" accept="audio/*" onChange={(e)=> setFile(e.target.files?.[0] || null)} />
        </label>
        <button type="submit" disabled={loading} className="px-4 py-2 bg-indigo-600 text-white rounded">
          {loading ? 'Sending...' : 'Send Snapshot'}
        </button>
      </div>
    </form>
  );
}
