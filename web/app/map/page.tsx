'use client';
import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function MapPage() {
  const [items, setItems] = useState<any[]>([]);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

  useEffect(() => {
    if (!API_BASE) return;
    axios.get(`${API_BASE}/api/mood`, {
      headers: {
        // Optionally attach Authorization if needed
      }
    }).then(r => setItems(r.data)).catch(console.error);
  }, [API_BASE]);

  const color = (label: string) => {
    switch (label) {
      case 'happy': return 'bg-green-100';
      case 'calm': return 'bg-cyan-100';
      case 'sad': return 'bg-blue-100';
      case 'anxious': return 'bg-yellow-100';
      case 'angry': return 'bg-red-100';
      default: return 'bg-gray-100';
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Mood Map</h2>
      <div className="space-y-3">
        {items.length === 0 && <div className="text-slate-600">No snapshots yet. Create one from the Mood page.</div>}
        {items.map(item => (
          <div key={item.id} className={`p-3 rounded ${color(item.detected_emotion)} flex justify-between`}>
            <div>
              <div className="font-medium">{item.detected_emotion || 'unknown'}</div>
              <div className="text-sm text-slate-700">{item.raw_text || '—'}</div>
            </div>
            <div className="text-xs text-slate-600">{new Date(item.created_at).toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
