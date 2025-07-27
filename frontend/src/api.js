export async function fetchLogs() {
  const res = await fetch('https://backend-wandering-bird-8180.fly.dev');
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

