'use client';
import React, { useState } from 'react';
import axios from 'axios';
import { supabase } from '../lib/supabaseClient';

type Props = {
  onResult?: (r: any) => void;
};

export default function MoodForm({ onResult }: Props) {
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [postAsChat, setPostAsChat] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!API_BASE) {
    throw new Error('❌ NEXT_PUBLIC_API_BASE_URL not set.');
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

      let resp;

      if (postAsChat && text.trim()) {
        console.log('💬 Sending to Chat API');
        resp = await axios.post(`${API_BASE}/api/chat`, { content: text }, { headers });
      } else {
        console.log('🌤 Sending to Mood API');
        const form = new FormData();
        if (text) form.append('text', text);
        if (file) form.append('file', file);
        headers['Content-Type'] = 'multipart/form-data';
        resp = await axios.post(`${API_BASE}/api/mood`, form, { headers });
      }

      console.log('✅ API response:', resp.data);
      setResult(resp.data);
      onResult?.(resp.data);

      // 🔄 Push to chat page via localStorage + event
      localStorage.setItem('lastMoodResponse', JSON.stringify(resp.data));
      window.dispatchEvent(new Event('newChatMessage'));
    } catch (err) {
      console.error('❌ Submission error:', err);
      setError('Error submitting form.');
    } finally {
      setLoading(false);
      setText('');
      setFile(null);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow-sm space-y-4 border border-slate-200">
      <form onSubmit={submit} className="space-y-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type or record your feeling..."
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
        <div className="mt-4 p-3 border rounded bg-gray-50 text-sm text-gray-700">
          ✅ Processed successfully. Check the chat window for the AI response.
        </div>
      )}
    </div>
  );
}
