'use client';

import React, { useState } from 'react';
import axios from 'axios';
import { supabase } from '../lib/supabaseClient'; // adjust relative path if needed

interface MoodFormProps {
  onResult?: (result: any) => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  detected_emotion?: string;
}

export default function MoodForm({ onResult }: MoodFormProps) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!API_BASE) {
    console.error('NEXT_PUBLIC_API_BASE_URL missing');
  }

  const sendMood = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (!token) throw new Error('No Supabase user session found.');

      const resp = await axios.post(
        `${API_BASE}/mood`,
        { source: 'text', raw_text: input },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log('✅ Mood snapshot response:', resp.data);

      const aiMsg: Message = {
        role: 'assistant',
        content:
          resp.data.assistant_message ||
          'I have recorded your mood successfully.',
        detected_emotion: resp.data.detected_emotion,
      };

      setMessages((prev) => [...prev, aiMsg]);
      setInput('');

      // Optional: inform parent
      onResult?.(resp.data);

    } catch (err) {
      console.error('❌ Mood snapshot failed:', err);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Failed to record mood. Try again.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-4 text-indigo-700">Mood Snapshot 🌤️</h2>

      {/* Simple chat-style message display */}
      <div className="bg-white border rounded p-4 h-[60vh] overflow-y-auto shadow-sm">
        {messages.length > 0 ? (
          messages.map((m, i) => (
            <div
              key={i}
              className={`my-2 ${
                m.role === 'assistant' ? 'text-left' : 'text-right'
              }`}
            >
              <div
                className={`inline-block px-3 py-2 rounded ${
                  m.role === 'assistant'
                    ? 'bg-slate-100 text-slate-900'
                    : 'bg-indigo-600 text-white'
                }`}
              >
                <div>{m.content}</div>
                {m.detected_emotion && (
                  <div className="text-xs mt-1 opacity-75">
                    Mood: {m.detected_emotion}
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="text-gray-500 text-center mt-20">
            Share how you feel to start your mood journey 🌱
          </div>
        )}
      </div>

      <form onSubmit={sendMood} className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your mood..."
          className="flex-1 border rounded p-2"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          {loading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
