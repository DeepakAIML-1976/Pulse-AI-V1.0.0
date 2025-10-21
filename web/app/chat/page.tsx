'use client';
import React, { useEffect, useState, useRef } from 'react';
import { supabase } from '../../lib/supabaseClient';
import axios from 'axios';

export default function ChatPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    const token = (await supabase.auth.getSession()).data.session?.access_token;
    if (!token) return;
    const resp = await axios.get(`${API_BASE}/api/chat/history`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    setMessages(resp.data.reverse ? resp.data.reverse() : resp.data);
    scrollToBottom();
  };

  const scrollToBottom = () => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    const token = (await supabase.auth.getSession()).data.session?.access_token;
    try {
      const resp = await axios.post(
        `${API_BASE}/api/chat`,
        { content: input },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const { user_message, assistant_message, recommendations } = resp.data;
      setMessages(prev => [...prev, user_message, assistant_message, { role: 'recs', content: recommendations }]);
      setInput('');
      scrollToBottom();
    } catch {
      alert('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-4">Pulse Chat Companion</h2>
      <div className="bg-white border rounded p-4 h-[60vh] overflow-y-auto">
        {messages.map((m, i) =>
          m.role === 'recs' ? (
            <div key={i} className="my-4 border-t pt-2 text-sm">
              <div className="font-semibold text-indigo-600">🎧 Spotify & 🎬 Movie Suggestions</div>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <div>
                  {m.content?.spotify?.slice(0, 3).map((t: any, idx: number) => (
                    <div key={idx}>
                      🎵 <a href={t.external_url} target="_blank" className="text-blue-600">{t.name}</a> — {t.artists}
                    </div>
                  ))}
                </div>
                <div>
                  {m.content?.tmdb?.slice(0, 3).map((mv: any, idx: number) => (
                    <div key={idx}>
                      🎬 <a href={mv.tmdb_url} target="_blank" className="text-blue-600">{mv.title}</a>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div key={i} className={`my-2 ${m.role === 'assistant' ? 'text-left' : 'text-right'}`}>
              <div className={`inline-block px-3 py-2 rounded ${m.role === 'assistant' ? 'bg-slate-100' : 'bg-indigo-600 text-white'}`}>
                <div>{m.content}</div>
                {m.detected_emotion && (
                  <div className="text-xs mt-1 opacity-75">Mood: {m.detected_emotion}</div>
                )}
              </div>
            </div>
          )
        )}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={sendMessage} className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 border rounded p-2"
        />
        <button disabled={loading} type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded">
          {loading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
