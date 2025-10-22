'use client';
import React, { useState } from 'react';
import axios from 'axios';
import { supabase } from '../lib/supabaseClient';

export default function MoodForm() {
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [postAsChat, setPostAsChat] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!API_BASE) {
    throw new Error('❌ NEXT_PUBLIC_API_BASE_URL not found. Check Vercel environment variables.');
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const session = await supabase.auth.getSession();
      const token = session?.data?.session?.access_token;
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      console.log('🧠 Submitting mood form → chat mode?', postAsChat);

      if (postAsChat && text.trim()) {
        console.log('💬 Sending to /api/chat →', text);
        const resp = await axios.post(
          `${API_BASE}/api/chat`,
          { content: text },
          { headers }
        );
        console.log('✅ /api/chat response:', resp.data);
        setResult(resp.data);
        return;
      }

      const form = new FormData();
      if (text) form.append('text', text);
      if (file) form.append('file', file);
      headers['Content-Type'] = 'multipart/form-data';

      console.log('🎧 Uploading to /api/mood...');
      const resp = await axios.post(`${API_BASE}/api/mood`, form, { headers });
      console.log('✅ /api/mood response:', resp.data);
      setResult(resp.data);
    } catch (err) {
      console.error('❌ Submission error:', err);
      setError('Error submitting form.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow-sm space-y-4 border border-slate-200">
      <form onSubmit={submit} className="space-y-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="How are you feeling today?"
          className="w-full border rounded p-2 min-h-[100px]"
        />
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={postAsChat}
            onChange={(e) => setPostAsChat(e.target.checked)}
          />
          <span>Send to AI Chat Companion</span>
        </div>

        <button
          type="submit"
          disabled={loading}
          className={`px-4 py-2 rounded text-white ${
            loading ? 'bg-indigo-400' : 'bg-indigo-600 hover:bg-indigo-700'
          }`}
        >
          {loading ? 'Processing...' : 'Submit'}
        </button>
      </form>

      {error && <div className="text-red-600 text-sm">{error}</div>}

      {result && (
        <div className="mt-4 p-3 border rounded bg-gray-50">
          <h3 className="font-semibold text-indigo-700 mb-2">Response</h3>
          <pre className="text-xs text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
