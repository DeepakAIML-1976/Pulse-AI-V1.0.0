'use client';

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { supabase } from '../../../lib/supabaseClient';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// ================================
// Types
// ================================
interface MoodHistoryItem {
  id: string;
  detected_emotion: string | null;
  confidence: number | null;
  raw_text: string | null;
  created_at: string;
}

// ================================
// Helper: Emotion Colors
// ================================
const emotionColors: Record<string, string> = {
  calm: '#4ade80',
  neutral: '#94a3b8',
  sad: '#60a5fa',
  angry: '#f87171',
  anxious: '#facc15',
  unknown: '#a1a1aa',
};

const emotionToValue = (emotion: string | null) => {
  switch (emotion?.toLowerCase()) {
    case 'calm':
      return 5;
    case 'neutral':
      return 3;
    case 'sad':
      return 1;
    case 'angry':
      return 2;
    case 'anxious':
      return 2.5;
    default:
      return 3;
  }
};

// ================================
// Component
// ================================
export default function MoodHistoryPage() {
  const [history, setHistory] = useState<MoodHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'map'>('timeline');
  const [insight, setInsight] = useState<string>('');
  const [loadingInsight, setLoadingInsight] = useState(false);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        if (!token) throw new Error('User not authenticated.');

        const resp = await axios.get(`${API_BASE}/mood/history`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        setHistory(resp.data || []);
      } catch (err: any) {
        console.error('❌ Mood history fetch failed:', err);
        setError('Failed to fetch mood history.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [API_BASE]);

  const chartData = history
    .slice()
    .reverse()
    .map((item) => ({
      date: new Date(item.created_at).toLocaleDateString(),
      emotion_value: emotionToValue(item.detected_emotion),
      emotion: item.detected_emotion || 'unknown',
    }));

  // ==========================
  // Dashboard Stats
  // ==========================
  const emotionCount = history.reduce((acc: Record<string, number>, item) => {
    const e = (item.detected_emotion || 'unknown').toLowerCase();
    acc[e] = (acc[e] || 0) + 1;
    return acc;
  }, {});

  const mostCommon = Object.entries(emotionCount)
    .sort((a, b) => b[1] - a[1])
    .map(([e, c]) => ({ emotion: e, count: c }));

  const gridData = history.slice(0, 42);

  // ==========================
  // Fetch AI Mood Insight
  // ==========================
  const fetchMoodInsight = async () => {
    try {
      setLoadingInsight(true);
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (!token) throw new Error('User not authenticated.');

      const resp = await axios.post(
        `${API_BASE}/mood/insight`,
        { moods: history.slice(0, 20) },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setInsight(resp.data?.insight || 'No insight available yet.');
    } catch (err: any) {
      console.error('❌ Mood insight fetch failed:', err);
      setInsight('Unable to generate insight right now.');
    } finally {
      setLoadingInsight(false);
    }
  };

  // Fetch insight automatically when switching to "map" tab
  useEffect(() => {
    if (activeTab === 'map' && history.length > 0) {
      fetchMoodInsight();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // ==========================
  // Render
  // ==========================
  return (
    <div className="max-w-5xl mx-auto mt-8">
      <h2 className="text-2xl font-semibold text-indigo-700 mb-4">Mood History 🌤️</h2>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b pb-2">
        <button
          onClick={() => setActiveTab('timeline')}
          className={`pb-1 font-medium ${
            activeTab === 'timeline'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          🗓️ Timeline
        </button>
        <button
          onClick={() => setActiveTab('map')}
          className={`pb-1 font-medium ${
            activeTab === 'map'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          📊 Mood Map
        </button>
      </div>

      {loading ? (
        <div className="text-gray-600">Loading mood data...</div>
      ) : error ? (
        <div className="text-red-600">{error}</div>
      ) : history.length === 0 ? (
        <div className="text-gray-500 text-center mt-16">
          No mood snapshots yet. Share your mood in the Mood Snapshot page 🌱
        </div>
      ) : activeTab === 'timeline' ? (
        <>
          {/* Trend Chart */}
          <div className="bg-white border rounded p-4 mb-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-3 text-gray-700">
              Mood Trend Over Time
            </h3>
            <div className="w-full h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[0, 6]} hide />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                    }}
                    labelStyle={{ fontWeight: 'bold' }}
                    formatter={(value: number, name: string, props: any) => [
                      props.payload.emotion,
                      'Emotion',
                    ]}
                  />
                  <Line
                    type="monotone"
                    dataKey="emotion_value"
                    stroke="#6366f1"
                    strokeWidth={2}
                    dot={{ r: 5 }}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Timeline View */}
          <div className="bg-white border rounded p-4 shadow-sm">
            <h3 className="text-lg font-semibold mb-3 text-gray-700">
              Mood Timeline
            </h3>
            <ul className="divide-y divide-gray-200">
              {history.map((mood) => (
                <li key={mood.id} className="py-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <p
                        className="text-gray-900 font-medium"
                        style={{
                          color:
                            emotionColors[mood.detected_emotion || 'unknown'],
                        }}
                      >
                        {mood.detected_emotion || 'Unknown'}
                      </p>
                      <p className="text-gray-600 text-sm mt-1">
                        {mood.raw_text || 'No text recorded.'}
                      </p>
                    </div>
                    <span className="text-gray-500 text-xs">
                      {new Date(mood.created_at).toLocaleString()}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </>
      ) : (
        /* =====================
           📊 Mood Map Dashboard
           ===================== */
        <div className="bg-white border rounded p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4 text-gray-700">
            Emotional Overview
          </h3>

          {/* Mood Heatmap Grid */}
          <div className="grid grid-cols-7 gap-2 mb-8">
            {gridData.map((mood) => (
              <div
                key={mood.id}
                title={`${mood.detected_emotion || 'Unknown'} – ${new Date(
                  mood.created_at
                ).toLocaleDateString()}`}
                className="w-10 h-10 rounded-md"
                style={{
                  backgroundColor:
                    emotionColors[mood.detected_emotion || 'unknown'],
                  opacity: 0.9,
                }}
              ></div>
            ))}
          </div>

          {/* Emotion Summary */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-700 mb-3">
              Most Frequent Emotions
            </h4>
            <ul className="space-y-1">
              {mostCommon.map(({ emotion, count }) => (
                <li key={emotion} className="flex justify-between">
                  <span className="capitalize text-gray-800">
                    {emotion === 'unknown' ? 'Unclassified' : emotion}
                  </span>
                  <span className="font-semibold text-indigo-600">
                    {count} times
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* AI Mood Insight */}
          <div className="bg-indigo-50 border border-indigo-200 rounded p-4">
            <h4 className="font-semibold text-indigo-700 mb-2">
              💬 AI Mood Insight
            </h4>
            {loadingInsight ? (
              <p className="text-gray-500">Analyzing your recent moods...</p>
            ) : (
              <p className="text-gray-800 leading-relaxed">{insight}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
