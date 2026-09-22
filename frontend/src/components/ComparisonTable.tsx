import type { ComparisonResponse, MetricBlock, Summary } from "../types";

function pct(v: number | null | undefined): string {
  return v == null ? "-" : `${(v * 100).toFixed(1)}%`;
}

function num3(v: number | null | undefined): string {
  return v == null ? "-" : v.toFixed(3);
}

const METRIC_ROWS: { label: string; get: (s: Summary) => string }[] = [
  { label: "Accuracy", get: (s) => pct(s.accuracy) },
  { label: "Macro accuracy (per family)", get: (s) => pct(s.macro_accuracy) },
  { label: "Brier mean (lower is better)", get: (s) => num3(s.brier_mean) },
  { label: "Top-label ECE (lower is better)", get: (s) => num3(s.ece?.ece ?? null) },
  { label: "Score ordinal MAE (lower is better)", get: (s) => num3(s.ordinal_mae) },
  { label: "Strict schema validity", get: (s) => pct(s.schema_validity_strict) },
  { label: "Coverage (attempted / planned)", get: (s) => pct(s.coverage) },
  { label: "Latency p50 (s)", get: (s) => num3(s.latency?.p50_s ?? null) },
  { label: "Latency p95 (s)", get: (s) => num3(s.latency?.p95_s ?? null) },
];

function perFamilyRows(a: Record<string, MetricBlock>, b: Record<string, MetricBlock>) {
  const families = Array.from(new Set([...Object.keys(a), ...Object.keys(b)])).sort();
  return families.map((family) => ({
    family,
    laya: pct(a[family]?.accuracy ?? null),
    openJev: pct(b[family]?.accuracy ?? null),
  }));
}

export function ComparisonTable({ comparison }: { comparison: ComparisonResponse }) {
  const { laya, open_jev: openJev } = comparison;

  if (!laya.ready || !openJev.ready) {
    return (
      <p className="hint">
        Run both models on the same dataset scope to see a comparison.
        {!laya.ready && " Laya has no cached run for this scope yet."}
        {!openJev.ready && " Open-Jev has no cached run for this scope yet."}
      </p>
    );
  }

  const ls = laya.summary as Summary;
  const os = openJev.summary as Summary;

  return (
    <>
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Laya</th>
            <th>Open-Jev</th>
          </tr>
        </thead>
        <tbody>
          {METRIC_ROWS.map(({ label, get }) => (
            <tr key={label}>
              <td>{label}</td>
              <td>{get(ls)}</td>
              <td>{get(os)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Per-family accuracy</h3>
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Family</th>
            <th>Laya</th>
            <th>Open-Jev</th>
          </tr>
        </thead>
        <tbody>
          {perFamilyRows(ls.per_family, os.per_family).map((row) => (
            <tr key={row.family}>
              <td>{row.family}</td>
              <td>{row.laya}</td>
              <td>{row.openJev}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
