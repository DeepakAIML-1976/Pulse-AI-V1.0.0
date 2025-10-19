'use client';
import React, { useState } from 'react';
import MoodForm from '../../components/MoodForm';

export default function MoodPage() {
  const [result, setResult] = useState<any>(null);
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Mood Snapshot</h2>
      <p className="text-slate-600">Type or record a short voice note (30–60s). Pulse analyzes and suggests a quick nudge.</p>
      <MoodForm onResult={(r) => setResult(r)} />
      {result && (
        <div className="mt-4 p-4 border rounded bg-white">
          <div><strong>Detected:</strong> {result.detected_emotion}</div>
          <div><strong>Confidence:</strong> {Math.round((result.confidence||0)*100)}%</div>
          <div className="mt-2 text-slate-600 text-sm">Created: {new Date(result.created_at).toLocaleString()}</div>
        </div>
      )}
    </div>
  );
}
