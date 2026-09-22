import type {
  ComparisonResponse,
  DatasetsResponse,
  ModelName,
  RunStatusResponse,
  Split,
} from "./types";

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return (await res.json()) as T;
}

export async function getDatasets(): Promise<DatasetsResponse> {
  return asJson<DatasetsResponse>(await fetch("/api/datasets"));
}

export async function startRun(
  model: ModelName,
  splits: Split[],
  limit: number | null,
  forceRerun = false
): Promise<RunStatusResponse> {
  const res = await fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, splits, limit, force_rerun: forceRerun }),
  });
  return asJson<RunStatusResponse>(res);
}

export async function getRun(slug: string): Promise<RunStatusResponse> {
  return asJson<RunStatusResponse>(await fetch(`/api/runs/${encodeURIComponent(slug)}`));
}

export async function deleteRun(slug: string): Promise<void> {
  const res = await fetch(`/api/runs/${encodeURIComponent(slug)}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
}

export async function getComparison(
  splits: Split[],
  limit: number | null
): Promise<ComparisonResponse> {
  const params = new URLSearchParams({ splits: splits.join(",") });
  if (limit) params.set("limit", String(limit));
  const res = await fetch(`/api/comparison?${params.toString()}`);
  return asJson<ComparisonResponse>(res);
}
