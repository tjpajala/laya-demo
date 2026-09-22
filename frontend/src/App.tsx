import { useCallback, useEffect, useState } from "react";
import { deleteRun, getComparison, getDatasets, getRun, startRun } from "./api";
import { ComparisonTable } from "./components/ComparisonTable";
import { JobLauncher } from "./components/JobLauncher";
import type { ComparisonResponse, ModelName, RunStatusResponse, Split, SplitInfo } from "./types";

const ALL_SPLITS: Split[] = ["easy", "original", "hard"];
const MODELS: { key: ModelName; label: string }[] = [
  { key: "laya", label: "Laya Typed-Decisions (ModernBERT-large, 421M)" },
  { key: "open_jev", label: "Open-Jev 2B (Zefan-Cai, Qwen3.5-2B)" },
];

export default function App() {
  const [splitInfo, setSplitInfo] = useState<SplitInfo[]>([]);
  const [selectedSplits, setSelectedSplits] = useState<Split[]>(["easy"]);
  const [limit, setLimit] = useState<number | "">("");
  const [statuses, setStatuses] = useState<Record<ModelName, RunStatusResponse | null>>({
    laya: null,
    open_jev: null,
  });
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);

  useEffect(() => {
    getDatasets()
      .then((d) => setSplitInfo(d.splits))
      .catch((e) => console.error(e));
  }, []);

  const effectiveLimit = limit === "" ? null : limit;

  const refreshComparison = useCallback(() => {
    if (selectedSplits.length === 0) {
      setComparison(null);
      return;
    }
    getComparison(selectedSplits, effectiveLimit)
      .then(setComparison)
      .catch((e) => console.error(e));
  }, [selectedSplits, effectiveLimit]);

  useEffect(() => {
    refreshComparison();
  }, [refreshComparison]);

  // Poll any job currently running.
  useEffect(() => {
    const running = Object.values(statuses).filter(
      (s): s is RunStatusResponse => !!s && s.status === "running"
    );
    if (running.length === 0) return;
    const id = setInterval(() => {
      running.forEach((job) => {
        getRun(job.slug)
          .then((s) => {
            setStatuses((prev) => ({ ...prev, [s.model]: s }));
            if (s.status !== "running") refreshComparison();
          })
          .catch((e) => console.error(e));
      });
    }, 2000);
    return () => clearInterval(id);
  }, [statuses, refreshComparison]);

  function toggleSplit(split: Split) {
    setSelectedSplits((prev) =>
      prev.includes(split) ? prev.filter((s) => s !== split) : [...prev, split]
    );
  }

  async function handleStart(model: ModelName, forceRerun: boolean) {
    if (selectedSplits.length === 0) return;
    const status = await startRun(model, selectedSplits, effectiveLimit, forceRerun);
    setStatuses((prev) => ({ ...prev, [model]: status }));
    if (status.status !== "running") refreshComparison();
  }

  async function handleClear(model: ModelName) {
    const current = statuses[model];
    if (!current) return;
    await deleteRun(current.slug);
    setStatuses((prev) => ({ ...prev, [model]: null }));
    refreshComparison();
  }

  return (
    <div className="page">
      <header>
        <h1>Laya vs Open-Jev on JevBench</h1>
        <p className="subtitle">
          Two typed-decision models scored by the same unmodified JevBench harness, fully offline.
        </p>
      </header>

      <section className="panel">
        <h2>Dataset scope</h2>
        <div className="split-picker">
          {ALL_SPLITS.map((split) => {
            const info = splitInfo.find((s) => s.name === split);
            return (
              <label key={split} className="split-option">
                <input
                  type="checkbox"
                  checked={selectedSplits.includes(split)}
                  onChange={() => toggleSplit(split)}
                />
                {split} {info ? `(${info.n})` : ""}
              </label>
            );
          })}
        </div>
        <label className="limit-input">
          Limit (optional)
          <input
            type="number"
            min={1}
            value={limit}
            onChange={(e) => setLimit(e.target.value === "" ? "" : Number(e.target.value))}
            placeholder="all tasks in selected splits"
          />
        </label>
      </section>

      <section className="launchers">
        {MODELS.map(({ key, label }) => (
          <JobLauncher
            key={key}
            model={key}
            label={label}
            status={statuses[key]}
            disabled={selectedSplits.length === 0}
            onStart={() => handleStart(key, false)}
            onRerun={() => handleStart(key, true)}
            onClear={() => handleClear(key)}
          />
        ))}
      </section>

      <section className="panel">
        <h2>Comparison</h2>
        {comparison ? <ComparisonTable comparison={comparison} /> : <p>Loading...</p>}
      </section>
    </div>
  );
}
