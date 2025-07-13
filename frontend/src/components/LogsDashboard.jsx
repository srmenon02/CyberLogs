import React, { useEffect, useState } from 'react';

export default function LogsDashboard() {
  // State to hold logs, loading status, and errors
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/logs?limit=10')  // ← optional: switch to page/page_size
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch logs');
        }
        return response.json();
      })
      .then(data => {
        console.log('Fetched logs:', data);
        setLogs(data.logs);  // ✅ Use the "logs" field from the response
        setLoading(false);
      })
      .catch(err => {
        console.error('Fetch error:', err); // ADD THIS
        setError(err.message);
        setLoading(false);
      });
  }, []);


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
