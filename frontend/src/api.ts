export type ContractListItem = {
  id: number;
  original_filename: string;
  processing_status: string;
  created_at: string;
  processed_at: string | null;
};

export type ContractDetail = {
  contract: {
    id: number;
    original_filename: string;
    processing_status: string;
    created_at: string;
    processed_at: string | null;
    error_message: string | null;
  };
  matrix: Array<{
    clause_type: { id: number; name: string };
    detected: boolean;
    confirmed: boolean | null;
    effective: boolean;
  }>;
};

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, init);
  if (!r.ok) {
    const body = await r.text();
    throw new Error(body || `${r.status} ${r.statusText}`);
  }
  return r.json() as Promise<T>;
}

export function listContracts(): Promise<{ items: ContractListItem[] }> {
  return http("/api/contracts");
}

export function getContract(id: number): Promise<ContractDetail> {
  return http(`/api/contracts/${id}`);
}

export async function uploadContract(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return http("/api/contracts", { method: "POST", body: fd });
}

export function setOverride(contractId: number, clauseTypeId: number, confirmed: boolean | null) {
  return http(`/api/contracts/${contractId}/clauses/${clauseTypeId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirmed }),
  });
}
