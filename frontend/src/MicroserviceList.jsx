import React, { useEffect, useState } from "react";
import "./App.css";

function ApiTester({ port, onClose }) {
  const [path, setPath] = useState("/");
  const [method, setMethod] = useState("GET");
  const [body, setBody] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResponse(null);
    try {
      const res = await fetch(`http://localhost:${port}${path}`, {
        method,
        headers: body && method !== "GET" ? { "Content-Type": "application/json" } : {},
        body: body && method !== "GET" ? body : undefined,
      });
      const text = await res.text();
      let data;
      try { data = JSON.parse(text); } catch { data = text; }
      setResponse({ status: res.status, data });
    } catch {
      setError("Request failed");
    }
    setLoading(false);
  };

  return (
    <div className="api-tester">
      <strong>Test API Endpoint</strong>
      <form onSubmit={handleSubmit} className="api-tester-form">
        <div>
          <label>Method: </label>
          <select value={method} onChange={e => setMethod(e.target.value)}>
            <option>GET</option>
            <option>POST</option>
            <option>PUT</option>
            <option>DELETE</option>
            <option>PATCH</option>
          </select>
        </div>
        <input type="text" value={path} onChange={e => setPath(e.target.value)} placeholder="/endpoint" className="api-tester-input" required />
        {(method !== "GET") && (
          <textarea value={body} onChange={e => setBody(e.target.value)} placeholder="JSON body (optional)" className="api-tester-textarea" />
        )}
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="submit" disabled={loading} className="api-tester-btn">{loading ? 'Sending...' : 'Send'}</button>
          <button type="button" onClick={onClose} className="api-tester-btn close">Close</button>
        </div>
      </form>
      {error && <div className="api-tester-error">{error}</div>}
      {response && (
        <div style={{ marginTop: 8 }}>
          <strong>Response ({response.status}):</strong>
          <pre className="api-tester-response">{typeof response.data === 'string' ? response.data : JSON.stringify(response.data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function MicroserviceList({ onBack }) {
  const [microservices, setMicroservices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusMap, setStatusMap] = useState({});
  const [actionLoading, setActionLoading] = useState({});
  const [apiTestFor, setApiTestFor] = useState(null); // folder name

  useEffect(() => {
    fetch("http://localhost:8000/list-microservices")
      .then((res) => res.json())
      .then((data) => {
        setMicroservices(data.microservices || []);
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to fetch microservices.");
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetch("http://localhost:8000/status-microservices")
      .then((res) => res.json())
      .then((data) => setStatusMap(data.running || {}));
  }, [loading]);

  const handleStart = async (folder) => {
    setActionLoading((prev) => ({ ...prev, [folder]: true }));
    try {
      const res = await fetch(`http://localhost:8000/start-microservice/${folder}`, { method: "POST" });
      await res.json();
      const statusRes = await fetch("http://localhost:8000/status-microservices");
      const statusData = await statusRes.json();
      setStatusMap(statusData.running || {});
    } catch {
      alert("Failed to start microservice.");
    }
    setActionLoading((prev) => ({ ...prev, [folder]: false }));
  };

  const handleStop = async (folder) => {
    setActionLoading((prev) => ({ ...prev, [folder]: true }));
    try {
      const res = await fetch(`http://localhost:8000/stop-microservice/${folder}`, { method: "POST" });
      await res.json();
      const statusRes = await fetch("http://localhost:8000/status-microservices");
      const statusData = await statusRes.json();
      setStatusMap(statusData.running || {});
    } catch {
      alert("Failed to stop microservice.");
    }
    setActionLoading((prev) => ({ ...prev, [folder]: false }));
  };

  return (
    <div className="App">
      <button
        className="nav-btn"
        onClick={onBack}
      >
        &larr; Back to Upload
      </button>
      <h1>Uploaded Microservices</h1>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {!loading && !error && (
        <ul style={{ textAlign: 'left', padding: 0 }}>
          {microservices.length === 0 && <li>No microservices found.</li>}
          {microservices.map((ms, idx) => {
            const running = statusMap[ms.folder];
            return (
              <li key={idx} className="ms-card">
                <strong>Name:</strong> {ms.name} <br />
                <strong>Description:</strong> {ms.description || <em>(none)</em>} <br />
                <strong>Files:</strong>
                <ul className="ms-files">
                  {ms.files.map((f, i) => (
                    <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {f}
                      <a
                        href={`http://localhost:8000/download/${ms.folder}/${encodeURIComponent(f)}`}
                        download
                        className="ms-file-link"
                      >
                        Download
                      </a>
                    </li>
                  ))}
                </ul>
                <div style={{ marginTop: 10 }}>
                  {running ? (
                    <>
                      <span className="ms-status">Running on port {running.port}</span>
                      <button
                        className="ms-btn stop"
                        onClick={() => handleStop(ms.folder)}
                        disabled={actionLoading[ms.folder]}
                      >
                        {actionLoading[ms.folder] ? 'Stopping...' : 'Stop'}
                      </button>
                      <button
                        className="ms-btn"
                        onClick={() => setApiTestFor(apiTestFor === ms.folder ? null : ms.folder)}
                      >
                        {apiTestFor === ms.folder ? 'Hide API Tester' : 'Test API'}
                      </button>
                      {apiTestFor === ms.folder && <ApiTester port={running.port} onClose={() => setApiTestFor(null)} />}
                    </>
                  ) : (
                    <button
                      className="ms-btn"
                      onClick={() => handleStart(ms.folder)}
                      disabled={actionLoading[ms.folder]}
                    >
                      {actionLoading[ms.folder] ? 'Starting...' : 'Start'}
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default MicroserviceList;
