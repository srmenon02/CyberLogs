import React, { useEffect, useState } from 'react';
import axios from 'axios';

type Log = {
  _id: string;
  event?: string;
  status?: string;
  [key: string]: any;
};

const LogTable: React.FC = () => {
  const [logs, setLogs] = useState<Log[]>([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get('https://backend-wandering-bird-8180.fly.dev');
        setLogs(response.data);
      } catch (error) {
        console.error('Error fetching logs:', error);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 5000); // auto-refresh every 5 sec
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>📄 Latest Logs</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Event</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log._id}>
              <td>{log._id}</td>
              <td>{log.event ?? '-'}</td>
              <td>{log.status ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LogTable;
