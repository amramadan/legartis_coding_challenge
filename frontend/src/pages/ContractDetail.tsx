import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getContract, setOverride, ContractDetail as Detail } from "../api";

export default function ContractDetail() {
  const { id } = useParams();
  const contractId = Number(id);

  const [data, setData] = useState<Detail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  async function refresh() {
    try {
      const d = await getContract(contractId);
      setData(d);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contractId]);

  async function applyOverride(clauseTypeId: number, confirmed: boolean | null) {
    const key = `${contractId}:${clauseTypeId}:${confirmed}`;
    setBusyKey(key);
    setErr(null);
    try {
      await setOverride(contractId, clauseTypeId, confirmed);
      await refresh();
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setBusyKey(null);
    }
  }

  if (!data) {
    return (
      <div className="container">
        <div className="card">
          <div className="row">
            <h2 style={{ margin: 0 }}>Contract #{contractId}</h2>
            <Link className="btn" to="/contracts">Back</Link>
          </div>
          <div className="muted">Loading…</div>
          {err && <div className="error">{err}</div>}
        </div>
      </div>
    );
  }

  const c = data.contract;

  return (
    <div className="container">
      <div className="card">
        <div className="row">
          <div>
            <h2 style={{ margin: 0 }}>{c.original_filename}</h2>
            <div className="muted">
              #{c.id} · {c.processing_status} · created {new Date(c.created_at).toLocaleString()}
            </div>
          </div>
          <Link className="btn" to="/contracts">Back</Link>
        </div>

        {c.error_message && (
          <>
            <div style={{ height: 10 }} />
            <div className="error">{c.error_message}</div>
          </>
        )}

        {err && (
          <>
            <div style={{ height: 10 }} />
            <div className="error">{err}</div>
          </>
        )}

        <div style={{ height: 14 }} />

        <table className="table">
          <thead>
            <tr>
              <th>Clause</th>
              <th>System</th>
              <th>User</th>
              <th>Effective</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.matrix.map((r) => {
              const sys = r.detected ? "Present" : "Missing";
              const usr = r.confirmed === null ? "—" : r.confirmed ? "Confirm present" : "Confirm missing";
              const eff = r.effective ? "Present" : "Missing";
              const pillClass = r.effective ? "pill ok" : "pill bad";

              return (
                <tr key={r.clause_type.id}>
                  <td style={{ fontWeight: 600 }}>{r.clause_type.name}</td>
                  <td>{sys}</td>
                  <td>{usr}</td>
                  <td><span className={pillClass}>{eff}</span></td>
                  <td>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button
                        className="btn"
                        disabled={!!busyKey}
                        onClick={() => applyOverride(r.clause_type.id, null)}
                      >
                        Auto
                      </button>
                      <button
                        className="btn"
                        disabled={!!busyKey}
                        onClick={() => applyOverride(r.clause_type.id, true)}
                      >
                        Yes
                      </button>
                      <button
                        className="btn"
                        disabled={!!busyKey}
                        onClick={() => applyOverride(r.clause_type.id, false)}
                      >
                        No
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {busyKey && <div className="muted" style={{ marginTop: 10 }}>Saving…</div>}
      </div>
    </div>
  );
}
