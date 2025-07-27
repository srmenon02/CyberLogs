import React, { useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_URL;


function Spinner() {
  return (
    <div className="flex justify-center items-center py-20">
      <div
        className="w-10 h-10 border-4 border-gray-600 border-t-coral-400 rounded-full animate-spin"
        style={{ borderTopColor: "transparent" }}
      ></div>
    </div>
  );
}

export default function LogsDashboard() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [totalCount, setTotalCount] = useState(0);

  const [cache, setCache] = useState({});
  const [levelFilter, setLevelFilter] = useState("All");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [sortOrder, setSortOrder] = useState("desc"); // default newest first

  const fetchLogs = (page, level = "All") => {
    const cacheKey = `${level}_${page}_${searchKeyword.trim()}`;
    if (cache[cacheKey]) {
      setLogs(cache[cacheKey].logs);
      setTotalCount(cache[cacheKey].totalCount);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    let url = `${API_BASE_URL}/logs?page=${page}&page_size=${pageSize}&sort_by=timestamp&sort_order=${sortOrder}`;
;
    if (level !== "All") {
      url += `&level=${level}`;
    }
    if (searchKeyword.trim()) url += `&event_keyword=${encodeURIComponent(searchKeyword.trim())}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch logs");
        return res.json();
      })
      .then((data) => {
        setCache((prev) => ({
          ...prev,
          [cacheKey]: { logs: data.logs, totalCount: data.total_count },
        }));
        setLogs(data.logs);
        setTotalCount(data.total_count);
        setLoading(false);

        // Prefetch next page with same level filter
        const totalPages = Math.ceil(data.total_count / pageSize);
        if (page < totalPages) {
          const nextCacheKey = `${level}_${page + 1}`;
          fetch(
            `${API_BASE_URL}/logs?page=${page + 1}&page_size=${pageSize}${
              level !== "All" ? `&level=${level}` : ""
            }` // <-- Modified
          )
            .then((res) => res.json())
            .then((nextData) => {
              setCache((prev) => ({
                ...prev,
                [nextCacheKey]: {
                  logs: nextData.logs,
                  totalCount: nextData.total_count,
                },
              }));
            })
            .catch(() => {});
        }
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
  fetchLogs(page, levelFilter);
  }, [page, levelFilter, searchKeyword]);


  const totalPages = Math.ceil(totalCount / pageSize);

  if (error) return <p className="text-red-600">Error: {error}</p>;

  return (
    <div className="min-h-screen bg-charcoal-900 p-8 text-gray-100 font-sans">
      <main className="max-w-6xl mx-auto bg-charcoal-800 rounded-3xl shadow-xl p-10">
        <header className="mb-10">
          <h1
            className="text-5xl font-extrabold tracking-tight mb-2"
            style={{ letterSpacing: "-0.03em" }}
          >
            Latest Logs
          </h1>
          <div className="mb-6 flex items-center gap-4">
            <label htmlFor="levelFilter" className="font-semibold text-gray-300">
              Filter by Level:
            </label>
            <select
              id="levelFilter"
              value={levelFilter}
              onChange={(e) => {
                setPage(1);
                setLevelFilter(e.target.value);
              }}
              
              className="bg-charcoal-700 text-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-coral-400"
            >
              <option>All</option>
              <option>Info</option>
              <option>Warning</option>
              <option>Error</option>
            </select>
            
            {loading && (
              <svg
                className="w-5 h-5 animate-spin text-coral-400 ml-2"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                ></path>
              </svg>
            )}

          <label htmlFor="sortOrder" className="font-semibold text-gray-300">
            Sort by Time:
          </label>
          <select
            id="sortOrder"
            value={sortOrder}
            onChange={(e) => {
              setPage(1);
              setSortOrder(e.target.value);
            }}
            className="bg-charcoal-700 text-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-coral-400"
          >
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>
          <button
            disabled={loading}
            onClick={() => {
                window.open(`${API_BASE_URL}/logs/export`, "_blank");
            }}
            className="ml-auto bg-coral-600 hover:bg-coral-700 text-white font-semibold px-4 py-2 rounded-xl shadow transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Download CSV
          </button>
          </div>
          <div className="flex items-center gap-4 mt-4">
          <label htmlFor="searchKeyword" className="font-semibold text-gray-300">
          Keyword Search:
          </label>
          <input
            type="text"
            id="searchKeyword"
            value={searchKeyword}
            onChange={(e) => {
              setPage(1); // Reset to first page
              setSearchKeyword(e.target.value);
            }}
            placeholder="e.g. access, reboot, disk..."
            className="bg-charcoal-700 text-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-coral-400 w-72"
          />
        </div>
                  </header>

        <ul className="space-y-8">
          {logs.map((log) => (
            <li
              key={log._id || log.timestamp}
              className="bg-charcoal-700 rounded-3xl shadow-lg p-8 transition-shadow hover:shadow-coral-600/50 border border-charcoal-600"
            >
              <div className="flex items-center justify-between mb-5">
                <time className="text-sm font-mono text-teal-300 tracking-wide">
                  {new Date(log.timestamp).toLocaleString()}
                </time>
                <span
                  className={`px-4 py-1 rounded-full text-sm font-semibold tracking-wide ${
                    log.level === "ERROR"
                      ? "bg-coral-600 text-coral-100"
                      : log.level === "WARNING"
                      ? "bg-yellow-500 text-yellow-100"
                      : "bg-teal-600 text-teal-100"
                  }`}
                >
                  {log.level}
                </span>
              </div>
              <h2 className="text-2xl font-semibold text-gray-100 mb-4 leading-snug">
                {log.event}
              </h2>
              <div className="text-base text-gray-300 flex gap-8">
                <div>
                  <span className="font-semibold text-gray-200">Host:</span> {log.host}
                </div>
                <div>
                  <span className="font-semibold text-gray-200">IP:</span> {log.ip}
                </div>
              </div>
            </li>
          ))}
        </ul>

        <nav className="mt-10 flex flex-col items-center gap-4">
          <div className="flex justify-center items-center gap-6">
            <button
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              disabled={page === 1 || loading}
              className={`px-4 py-2 rounded-lg text-white font-semibold transition ${
                page === 1 || loading
                  ? "bg-gray-600 cursor-not-allowed"
                  : "bg-coral-600 hover:bg-coral-700"
              }`}
            >
              Previous
            </button>

            <span className="text-gray-300 font-mono">
              Page {page} of {totalPages}
            </span>

            <button
              onClick={() => setPage((p) => (p < totalPages ? p + 1 : p))}
              disabled={page === totalPages || loading}
              className={`px-4 py-2 rounded-lg text-white font-semibold transition ${
                page === totalPages || loading
                  ? "bg-gray-600 cursor-not-allowed"
                  : "bg-coral-600 hover:bg-coral-700"
              }`}
            >
              Next
            </button>
          </div>

          {loading && (
            <div className="flex items-center gap-2 text-gray-300 text-sm font-mono select-none">
              <svg
                className="w-5 h-5 animate-spin text-coral-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                ></path>
              </svg>
              Loading page {page}…
            </div>
          )}
        </nav>
      </main>
    </div>
  );
}
