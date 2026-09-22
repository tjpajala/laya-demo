import type { ComparisonResponse, DatasetInfo, MetricBlock, ModelComparisonEntry, Summary } from "../types";

function pct(v: number | null | undefined): string {
  return v == null ? "-" : `${(v * 100).toFixed(1)}%`;
}

function num3(v: number | null | undefined): string {
  return v == null ? "-" : v.toFixed(3);
}

function labelFor(datasetInfo: DatasetInfo[], name: string): string {
  return datasetInfo.find((d) => d.name === name)?.label ?? name;
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

function CombinedTable({
  laya,
  openJev,
}: {
  laya: ModelComparisonEntry;
  openJev: ModelComparisonEntry;
}) {
  if (!laya.combined || !openJev.combined) {
    const missing = (entry: ModelComparisonEntry) =>
      entry.per_dataset.filter((d) => !d.ready).map((d) => d.dataset);
    return (
      <p className="hint">
        Run every selected dataset for both models to see a combined comparison.
        {!laya.combined && ` Laya is missing: ${missing(laya).join(", ")}.`}
        {!openJev.combined && ` Open-Jev is missing: ${missing(openJev).join(", ")}.`}
      </p>
    );
  }
  const ls = laya.combined;
  const os = openJev.combined;
  return (
    <>
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Metric (combined across selected datasets)</th>
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

      <h3>Per-family accuracy (combined)</h3>
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

function PerDatasetTable({
  comparison,
  datasetInfo,
}: {
  comparison: ComparisonResponse;
  datasetInfo: DatasetInfo[];
}) {
  const datasetNames = comparison.laya.per_dataset.map((d) => d.dataset);
  const byName = (entry: ModelComparisonEntry, name: string) =>
    entry.per_dataset.find((d) => d.dataset === name);

  return (
    <table className="comparison-table">
      <thead>
        <tr>
          <th>Dataset</th>
          <th>Laya accuracy</th>
          <th>Open-Jev accuracy</th>
        </tr>
      </thead>
      <tbody>
        {datasetNames.map((name) => {
          const lm = byName(comparison.laya, name);
          const om = byName(comparison.open_jev, name);
          return (
            <tr key={name}>
              <td>{labelFor(datasetInfo, name)}</td>
              <td>{lm?.ready ? pct(lm.summary?.accuracy) : "not run"}</td>
              <td>{om?.ready ? pct(om.summary?.accuracy) : "not run"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function ComparisonTable({
  comparison,
  datasetInfo,
}: {
  comparison: ComparisonResponse;
  datasetInfo: DatasetInfo[];
}) {
  return (
    <>
      <h3>Per-dataset accuracy</h3>
      <PerDatasetTable comparison={comparison} datasetInfo={datasetInfo} />

      <h3>Combined</h3>
      <CombinedTable laya={comparison.laya} openJev={comparison.open_jev} />
    </>
  );
}
