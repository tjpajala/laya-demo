export type Split = "easy" | "original" | "hard";
export type ModelName = "laya" | "open_jev";
export type RunState = "running" | "done" | "failed";

export interface SplitInfo {
  name: Split;
  n: number;
}

export interface DatasetsResponse {
  splits: SplitInfo[];
}

export interface MetricBlock {
  n_planned: number;
  n_attempted: number;
  n_scorable: number;
  n_valid: number;
  n_correct: number;
  accuracy: number | null;
  coverage: number | null;
  schema_validity: number | null;
  schema_validity_strict: number | null;
  n_renormalized: number;
  operational_success: number | null;
  calibration_n: number;
  brier_mean: number | null;
  ece: { ece: number; n: number } | null;
  ordinal_mae: number | null;
  latency: { n: number; p50_s: number | null; p95_s: number | null };
  latency_failures: { n: number; p50_s: number | null; p95_s: number | null };
  price_per_1000_decisions_usd: number | null;
  cost_basis: string[];
}

export interface Summary extends MetricBlock {
  version: string;
  macro_accuracy: number | null;
  per_family: Record<string, MetricBlock>;
  complete: boolean;
  model_identities: string[];
  probability_sources: string[];
  splits: Record<string, MetricBlock>;
  ledger_charged_usd: number;
}

export interface RunStatusResponse {
  slug: string;
  model: ModelName;
  splits: Split[];
  limit: number | null;
  status: RunState;
  n_planned: number;
  n_done: number;
  error: string | null;
  summary: Summary | null;
}

export interface ComparisonEntry {
  slug: string;
  ready: boolean;
  summary: Summary | null;
}

export interface ComparisonResponse {
  laya: ComparisonEntry;
  open_jev: ComparisonEntry;
}
