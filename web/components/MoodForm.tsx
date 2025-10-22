'use client';
import React, { useState } from 'react';
import axios from 'axios';
import { supabase } from '../lib/supabaseClient';

type Props = { onResult?: (res: any) => void };

export default function MoodForm({ onResult }: Props) {
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [postAsChat, setPostAsChat] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!API_BASE) {
    throw new Error(
      '❌ NEXT_PUBLIC_API_BASE_URL not set. Please check your Vercel environment variables.'
    );
  }

  // 🔄 Submit handler
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

      // 🗨️ --- Chat mode ---
      if (postAsChat && text.trim()) {
        const resp = await axios.post(
          `${API_BASE}/api/chat`,
          { content: text },
          { headers }
        );

        if (!resp.data) throw new Error('Empty response from chat API.');

        setResult(resp.data);
        onResult?.(resp.data);
        setText('');
        setFile(null);
        return;
      }

      // 🌤️ --- Mood snapshot mode ---
      const form = new FormData();
      if (text) form.append('text', text);
      if (file) form.append('file', file);

      headers['Content-Type'] = 'multipart/form-data';

      const resp = await axios.post(`${API_BASE}/api/mood`, form, { headers });

      if (!resp.data) throw new Error('Empty response from mood API.');

      setResult(resp.data);
      onResult?.(resp.data);
      setText('');
      setFile(null);
    } catch (err: any) {
      console.error('Submission error:', err);

      if (axios.isAxiosError(err)) {
        const msg =
          err.response?.data?.detail ||
          err.response?.data?.error ||
          err.message ||
          'Unexpected API error.';
        setError(`⚠️ ${msg}`);
      } else {
        setError('⚠️ Network or authentication error. Please try again.');
      }
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
          disabled={loading}
        />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <input
            type="file"
            accept="audio/*,image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            disabled={loading}
          />

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={postAsChat}
              onChange={(e) => setPostAsChat(e.target.checked)}
              disabled={loading}
            />
            <span>Send to AI Chat Companion</span>
          </label>

          <button
            type="submit"
            disabled={loading}
            className={`px-4 py-2 rounded text-white ${
              loading
                ? 'bg-indigo-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {loading
              ? 'Sending...'
              : postAsChat
              ? 'Chat Now 💬'
              : 'Send Snapshot 🌤️'}
          </button>
        </div>
      </form>

      {error && (
        <div className="text-red-600 text-sm text-center mt-2">{error}</div>
      )}

      {/* === Result block === */}
      {result && (
        <div className="mt-6 p-4 border rounded bg-slate-50">
          {/* Chat mode result */}
          {result.assistant_message ? (
            <>
              <h3 className="font-semibold text-indigo-700 mb-2">
                AI Companion Response 🤖
              </h3>
              <p className="mb-2">{result.assistant_message.content}</p>

              {result.assistant_message.detected_emotion && (
                <p className="text-sm text-slate-500 mb-3">
                  Mood Detected:{' '}
                  <span className="font-medium text-slate-700">
                    {result.assistant_message.detected_emotion}
                  </span>
                </p>
              )}

              {result.recommendations && (
                <div className="mt-3">
                  <h4 className="font-medium mb-2 text-slate-700">
                    Suggested for You 🎧 🎬
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="font-semibold text-indigo-600 mb-1">
                        Spotify
                      </div>
                      {result.recommendations.spotify?.slice(0, 3).map(
                        (t: any, i: number) => (
                          <div key={i}>
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
                        )
                      )}
                    </div>
                    <div>
                      <div className="font-semibold text-indigo-600 mb-1">
                        Movies
                      </div>
                      {result.recommendations.tmdb?.slice(0, 3).map(
                        (m: any, i: number) => (
                          <div key={i}>
                            🎬{' '}
                            <a
                              href={m.tmdb_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-blue-600 hover:underline"
                            >
                              {m.title}
                            </a>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Snapshot mode result */}
              <h3 className="font-semibold text-indigo-700 mb-2">
                Mood Analysis 🌈
              </h3>
              <p>
                Emotion Detected:{' '}
                <span className="font-medium text-slate-700">
                  {result.detected_emotion || 'Unknown'}
                </span>
              </p>
              {result.confidence && (
                <p className="text-sm text-slate-500">
                  Confidence: {(result.confidence * 100).toFixed(1)}%
                </p>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
