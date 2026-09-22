import type { DatasetInfo, RunStatusResponse } from "../types";

interface Props {
  label: string;
  selectedDatasets: string[];
  datasetInfo: DatasetInfo[];
  statuses: Record<string, RunStatusResponse>;
  disabled: boolean;
  onStart: () => void;
  onRerun: () => void;
  onClearDataset: (dataset: string) => void;
}

function pct(v: number | null | undefined): string {
  return v == null ? "-" : `${(v * 100).toFixed(1)}%`;
}

function labelFor(datasetInfo: DatasetInfo[], name: string): string {
  return datasetInfo.find((d) => d.name === name)?.label ?? name;
}

export function JobLauncher({
  label,
  selectedDatasets,
  datasetInfo,
  statuses,
  disabled,
  onStart,
  onRerun,
  onClearDataset,
}: Props) {
  const anyRunning = selectedDatasets.some((d) => statuses[d]?.status === "running");
  const doneCount = selectedDatasets.filter((d) => statuses[d]?.status === "done").length;

  return (
    <div className="launcher-card">
      <h3>{label}</h3>
      <p className="quick-stats">
        {doneCount}/{selectedDatasets.length} dataset{selectedDatasets.length === 1 ? "" : "s"} ready
      </p>

      <ul className="dataset-rows">
        {selectedDatasets.map((dataset) => {
          const run = statuses[dataset];
          const state = run?.status ?? "idle";
          return (
            <li key={dataset} className="dataset-row">
              <span className="dataset-row-name">{labelFor(datasetInfo, dataset)}</span>
              <span className={`badge badge-${state}`}>{state}</span>
              {state === "running" && (
                <span className="progress">
                  <progress value={run.n_done} max={run.n_planned} />
                  <span>
                    {run.n_done}/{run.n_planned}
                  </span>
                </span>
              )}
              {state === "done" && run.summary && (
                <span className="quick-stats">accuracy {pct(run.summary.accuracy)}</span>
              )}
              {state === "failed" && <span className="error">{run.error}</span>}
              {run && state !== "running" && (
                <button className="secondary small" onClick={() => onClearDataset(dataset)}>
                  Clear cache
                </button>
              )}
            </li>
          );
        })}
      </ul>

      <div className="actions">
        <button disabled={disabled || anyRunning} onClick={onStart}>
          Run selected
        </button>
        <button disabled={disabled || anyRunning} onClick={onRerun}>
          Force rerun selected
        </button>
      </div>
    </div>
  );
}
