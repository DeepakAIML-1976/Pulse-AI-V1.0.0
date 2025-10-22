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
    throw new Error('❌ NEXT_PUBLIC_API_BASE_URL missing. Check your Vercel environment variables.');
  }

  const scrollToBottom = () => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

  // Load chat history
  useEffect(() => {
    (async () => {
      try {
        console.log('🔍 Loading chat history...');
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        if (!token) {
          console.warn('⚠️ No user token found.');
          return;
        }
        const resp = await axios.get(`${API_BASE}/api/chat/history`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        console.log('✅ Chat history response:', resp.data);

        const data = Array.isArray(resp.data)
          ? resp.data.filter((m) => m && (m.role || m.content))
          : [];
        setMessages(data.reverse ? data.reverse() : data);
      } catch (err) {
        console.error('❌ Failed to load chat history:', err);
        setError('Failed to load chat history.');
      } finally {
        scrollToBottom();
      }
    })();
  }, []);

  // Send message
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);

    try {
      console.log('💬 Sending message:', input);
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (!token) throw new Error('No session token found.');

      const resp = await axios.post(
        `${API_BASE}/api/chat`,
        { content: input },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      console.log('✅ Chat API response:', resp.data);

      const { user_message, assistant_message, recommendations } = resp.data || {};

      const newMessages = [
        ...(messages || []),
        ...(user_message ? [user_message] : []),
        ...(assistant_message ? [assistant_message] : []),
      ];

      if (recommendations) {
        console.log('🎧 Recommendations block received:', recommendations);
        newMessages.push({ role: 'recs', content: recommendations });
      }

      console.log('🧾 Updated messages array:', newMessages);
      setMessages(newMessages.filter((m) => m && (m.role || m.content)));
      setInput('');
      scrollToBottom();
    } catch (err: any) {
      console.error('❌ Chat send error:', err);
      setError('Failed to send message.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-4 text-indigo-700">Pulse Chat Companion 💬</h2>

      <div className="bg-white border rounded p-4 h-[60vh] overflow-y-auto shadow-sm">
        {error && <div className="text-red-600 text-sm mb-3">{error}</div>}

        {Array.isArray(messages) && messages.length > 0 ? (
          messages.map((m, i) => {
            if (!m) return null;

            console.log(`🗨️ Rendering message [${i}]:`, m);

            if (m.role === 'recs') {
              return (
                <div key={i} className="my-4 border-t pt-2 text-sm">
                  <div className="font-semibold text-indigo-600">🎧 Spotify & 🎬 Movies</div>
                  <pre className="text-xs text-gray-600">{JSON.stringify(m.content, null, 2)}</pre>
                </div>
              );
            }

            return (
              <div key={i} className={`my-2 ${m.role === 'assistant' ? 'text-left' : 'text-right'}`}>
                <div
                  className={`inline-block px-3 py-2 rounded ${
                    m.role === 'assistant' ? 'bg-slate-100 text-slate-900' : 'bg-indigo-600 text-white'
                  }`}
                >
                  <div>{m.content || '⚠️ No content'}</div>
                  {m.detected_emotion && (
                    <div className="text-xs mt-1 opacity-75">Mood: {m.detected_emotion}</div>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-gray-500 text-center my-8">No messages yet. 👇 Start chatting!</div>
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
