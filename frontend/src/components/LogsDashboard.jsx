import React, { useEffect, useState } from 'react';

export default function LogsDashboard() {
  // State to hold logs, loading status, and errors
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch logs from backend API
    fetch('http://localhost:8000/logs?limit=10')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch logs');
        }
        return response.json();
      })
      .then(data => {
        setLogs(data);         // Store logs data in state
        setLoading(false);     // Done loading
      })
      .catch(err => {
        setError(err.message); // Show error message if fetch fails
        setLoading(false);
      });
  }, []); // Empty deps array means this runs once on mount

  // Display loading message
  if (loading) return <p>Loading logs...</p>;

  // Display error message
  if (error) return <p className="text-red-600">Error: {error}</p>;

  // Render logs list
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Latest Logs</h1>
      <ul className="space-y-2">
        {logs.map(log => (
          <li key={log._id} className="border p-2 rounded shadow-sm">
            <pre>{JSON.stringify(log, null, 2)}</pre>
          </li>
        ))}
      </ul>
    </div>
  );
}
