'use client';
import React, { useEffect, useState, useRef } from 'react';
import { supabase } from '../../lib/supabaseClient';
import axios from 'axios';

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!API_BASE) {
    throw new Error(
      '❌ NEXT_PUBLIC_API_BASE_URL not set. Check your Vercel environment variables.'
    );
  }

  // Scroll to bottom helper
  const scrollToBottom = () => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

  // Load chat history on mount
  useEffect(() => {
    (async () => {
      try {
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        if (!token) return;
        const resp = await axios.get(`${API_BASE}/api/chat/history`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        const data = Array.isArray(resp.data)
          ? resp.data.filter((m) => m && m.role)
          : [];

        setMessages(data.reverse ? data.reverse() : data);
      } catch (err: any) {
        console.error('Failed to load chat history:', err);
        setError('Unable to load chat history. Please try again later.');
      } finally {
        scrollToBottom();
      }
    })();
  }, []);

  // Send a message
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (!token) throw new Error('No valid session token found.');

      const resp = await axios.post(
        `${API_BASE}/api/chat`,
        { content: input },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const { user_message, assistant_message, recommendations } = resp.data || {};

      const newMessages = [
        ...(messages || []),
        ...(user_message ? [user_message] : []),
        ...(assistant_message ? [assistant_message] : []),
      ];

      // Add recommendations block if available
      if (recommendations) {
        newMessages.push({ role: 'recs', content: recommendations });
      }

      setMessages(newMessages.filter((m) => m && m.role));
      setInput('');
      scrollToBottom();
    } catch (err: any) {
      console.error('Failed to send message:', err);
      setError('Failed to send message. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-4 text-indigo-700">
        Pulse Chat Companion 💬
      </h2>

      <div className="bg-white border rounded p-4 h-[60vh] overflow-y-auto shadow-sm">
        {error && (
          <div className="text-red-600 text-sm mb-3">{error}</div>
        )}

        {Array.isArray(messages) && messages.length > 0 ? (
          messages.map((m, i) => {
            if (!m || !m.role) return null;

            if (m.role === 'recs') {
              return (
                <div key={i} className="my-4 border-t pt-2 text-sm">
                  <div className="font-semibold text-indigo-600">
                    🎧 Spotify & 🎬 Movie Suggestions
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    <div>
                      {m.content?.spotify?.slice(0, 3).map((t: any, idx: number) => (
                        <div key={idx}>
                          🎵{' '}
                          <a
                            href={t.external_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {t.name}
                          </a>{' '}
                          — {t.artists}
                        </div>
                      ))}
                    </div>
                    <div>
                      {m.content?.tmdb?.slice(0, 3).map((mv: any, idx: number) => (
                        <div key={idx}>
                          🎬{' '}
                          <a
                            href={mv.tmdb_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {mv.title}
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            }

            return (
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
            );
          })
        ) : (
          <div className="text-gray-500 text-center my-8">
            No messages yet. Start a conversation below 👇
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={sendMessage} className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 border rounded p-2"
        />
        <button
          disabled={loading}
          type="submit"
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          {loading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
