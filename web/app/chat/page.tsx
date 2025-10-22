'use client';
import React, { useEffect, useState, useRef } from 'react';
import { supabase } from '../../lib/supabaseClient';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant' | 'recs';
  content: string;
  detected_emotion?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!API_BASE) {
    throw new Error('❌ NEXT_PUBLIC_API_BASE_URL not set. Check your Vercel environment variables.');
  }

  const scrollToBottom = () => {
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 200);
  };

  // 🧠 Load chat history
  useEffect(() => {
    (async () => {
      try {
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        if (!token) {
          console.warn('⚠️ No Supabase token found.');
          return;
        }

        const resp = await axios.get(`${API_BASE}/api/chat/history`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        console.log('✅ Chat history response:', resp.data);

        const validMessages = Array.isArray(resp.data)
          ? resp.data
              .filter((m: any) => m && m.role && m.content)
              .map((m: any) => ({
                role: m.role,
                content: m.content,
                detected_emotion: m.detected_emotion,
              }))
          : [];

        setMessages(validMessages);
        scrollToBottom();
      } catch (err) {
        console.error('❌ Failed to load chat history:', err);
        setError('Unable to load chat history.');
      }
    })();
  }, []);

  // 💬 Send message
  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (!token) throw new Error('No session token found.');

      const userMsg: Message = { role: 'user', content: input };
      setMessages((prev) => [...prev, userMsg]); // Show user message immediately

      console.log('💬 Sending to API:', input);
      const resp = await axios.post(
        `${API_BASE}/api/chat`,
        { content: input },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      console.log('✅ Chat API response:', resp.data);

      const { user_message, assistant_message, recommendations } = resp.data || {};

      // Combine all available responses into a proper chat sequence
      const newMessages: Message[] = [
        ...(user_message ? [user_message] : []),
        ...(assistant_message ? [assistant_message] : []),
      ];

      if (recommendations) {
        newMessages.push({
          role: 'recs',
          content: JSON.stringify(recommendations, null, 2),
        });
      }

      setMessages((prev) => [
        ...prev,
        ...newMessages.filter((m) => m && m.content),
      ]);
      setInput('');
      scrollToBottom();
    } catch (err) {
      console.error('❌ Chat send error:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // 🪄 Render UI
  return (
    <div className="max-w-3xl mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-4 text-indigo-700">
        Pulse Chat Companion 💬
      </h2>

      <div className="bg-white border rounded p-4 h-[60vh] overflow-y-auto shadow-sm">
        {error && <div className="text-red-600 text-sm mb-3">{error}</div>}

        {messages.length > 0 ? (
          messages.map((m, i) => (
            <div
              key={i}
              className={`my-2 ${
                m.role === 'assistant' ? 'text-left' : m.role === 'user' ? 'text-right' : ''
              }`}
            >
              {m.role === 'recs' ? (
                <div className="bg-slate-50 border rounded p-2 text-sm text-slate-700">
                  <strong>🎧 Suggestions:</strong>
                  <pre className="text-xs whitespace-pre-wrap">{m.content}</pre>
                </div>
              ) : (
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
              )}
            </div>
          ))
        ) : (
          <div className="text-gray-500 text-center mt-20">
            👋 No messages yet — start chatting below!
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
