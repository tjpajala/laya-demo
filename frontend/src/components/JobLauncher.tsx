import type { ModelName, RunStatusResponse } from "../types";

interface Props {
  model: ModelName;
  label: string;
  status: RunStatusResponse | null;
  disabled: boolean;
  onStart: () => void;
  onRerun: () => void;
  onClear: () => void;
}

function pct(v: number | null | undefined): string {
  return v == null ? "-" : `${(v * 100).toFixed(1)}%`;
}

export function JobLauncher({ label, status, disabled, onStart, onRerun, onClear }: Props) {
  const state = status?.status ?? "idle";

  return (
    <div className="launcher-card">
      <h3>{label}</h3>
      <div className={`badge badge-${state}`}>{state}</div>

      {status?.status === "running" && (
        <div className="progress">
          <progress value={status.n_done} max={status.n_planned} />
          <span>
            {status.n_done} / {status.n_planned}
          </span>
        </div>
      )}

      {status?.status === "failed" && <p className="error">{status.error}</p>}

      {status?.status === "done" && status.summary && (
        <p className="quick-stats">
          accuracy {pct(status.summary.accuracy)} | brier{" "}
          {status.summary.brier_mean?.toFixed(3) ?? "-"}
        </p>
      )}

      <div className="actions">
        <button disabled={disabled || state === "running"} onClick={onStart}>
          {state === "done" ? "Use cached result" : "Run"}
        </button>
        <button disabled={disabled || state === "running"} onClick={onRerun}>
          Force rerun
        </button>
        {status && state !== "running" && (
          <button className="secondary" onClick={onClear}>
            Clear cache
          </button>
        )}
      </div>
    </div>
  );
}
