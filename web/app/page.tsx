import Link from 'next/link';

export default function Home() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Welcome to Pulse</h1>
      <p className="text-slate-700">
        Pulse helps you track and gently regulate your emotional state with short mood snapshots.
      </p>
      <div className="flex gap-3">
        <Link href="/mood" className="px-4 py-2 bg-indigo-600 text-white rounded">Take Mood Snapshot</Link>
        <Link href="/map" className="px-4 py-2 border rounded">View Mood Map</Link>
      </div>
    </div>
  );
}
