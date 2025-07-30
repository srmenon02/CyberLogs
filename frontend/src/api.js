export async function fetchLogs() {
  const apiBaseUrl = import.meta.env.VITE_API_URL;
  const res = await fetch(`${apiBaseUrl}/logs`); 
  if (!res.ok) {
    throw new Error(`HTTP error! status: ${res.status}`);
  }
  return res.json();
}

import React from 'react';
import LogsDashboard from './components/LogsDashboard';

function App() {
  return (
    <div>
      <LogsDashboard />
    </div>
  );
}

export default App;

