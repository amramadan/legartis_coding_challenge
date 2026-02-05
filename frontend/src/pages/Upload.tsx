import { useState } from "react";
import { uploadContract } from "../api";

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function onUpload() {
    if (!file) return;
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      const r = await uploadContract(file);
      setResult(r);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h2>Upload contract</h2>
        <p className="muted">Allowed: .txt, .md, .markdown</p>

        <input
          type="file"
          accept=".txt,.md,.markdown"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />

        <div style={{ height: 10 }} />

        <button className="btn primary" disabled={!file || busy} onClick={onUpload}>
          {busy ? "Uploading..." : "Upload"}
        </button>

        {err && (
          <>
            <div style={{ height: 12 }} />
            <div className="error">{err}</div>
          </>
        )}

        {result && (
          <>
            <div style={{ height: 12 }} />
            <pre style={{ margin: 0, background: "#fafafa", padding: 10, borderRadius: 10, overflowX: "auto" }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </>
        )}
      </div>
    </div>
  );
}
