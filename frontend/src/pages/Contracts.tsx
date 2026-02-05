import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listContracts, ContractListItem } from "../api";

export default function Contracts() {
  const [items, setItems] = useState<ContractListItem[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await listContracts();
        setItems(r.items);
      } catch (e: any) {
        setErr(e?.message ?? String(e));
      }
    })();
  }, []);

  return (
    <div className="container">
      <div className="card">
        <div className="row">
          <h2 style={{ margin: 0 }}>Contracts</h2>
          <span className="muted">{items.length} items</span>
        </div>

        {err && (
          <>
            <div style={{ height: 12 }} />
            <div className="error">{err}</div>
          </>
        )}

        <div style={{ height: 10 }} />

        {items.map((c) => (
          <div key={c.id} className="card" style={{ marginTop: 10 }}>
            <div className="row">
              <div>
                <div style={{ fontWeight: 600 }}>{c.original_filename}</div>
                <div className="muted">
                  #{c.id} · {c.processing_status} · created {new Date(c.created_at).toLocaleString()}
                </div>
              </div>
              <Link className="btn" to={`/contracts/${c.id}`}>Open</Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
