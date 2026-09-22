import { useCallback, useEffect, useState } from "react";
import { deleteRun, getComparison, getDatasets, getRun, startRuns } from "./api";
import { ComparisonTable } from "./components/ComparisonTable";
import { JobLauncher } from "./components/JobLauncher";
import type { ComparisonResponse, DatasetInfo, ModelName, RunStatusResponse } from "./types";

const MODELS: { key: ModelName; label: string }[] = [
  { key: "laya", label: "Laya Typed-Decisions (ModernBERT-large, 421M)" },
  { key: "open_jev", label: "Open-Jev 2B (Zefan-Cai, Qwen3.5-2B)" },
];

// model -> dataset -> latest known status for that (model, dataset) pair.
type StatusMap = Record<ModelName, Record<string, RunStatusResponse>>;

export default function App() {
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo[]>([]);
  const [selectedDatasets, setSelectedDatasets] = useState<string[]>(["easy"]);
  const [limit, setLimit] = useState<number | "">("");
  const [statuses, setStatuses] = useState<StatusMap>({ laya: {}, open_jev: {} });
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);

  useEffect(() => {
    getDatasets()
      .then((d) => setDatasetInfo(d.datasets))
      .catch((e) => console.error(e));
  }, []);

  const effectiveLimit = limit === "" ? null : limit;

  const refreshComparison = useCallback(() => {
    if (selectedDatasets.length === 0) {
      setComparison(null);
      return;
    }
    getComparison(selectedDatasets, effectiveLimit)
      .then(setComparison)
      .catch((e) => console.error(e));
  }, [selectedDatasets, effectiveLimit]);

  useEffect(() => {
    refreshComparison();
  }, [refreshComparison]);

  // Poll every (model, dataset) job currently running.
  useEffect(() => {
    const running: RunStatusResponse[] = [];
    for (const model of MODELS.map((m) => m.key)) {
      for (const run of Object.values(statuses[model])) {
        if (run.status === "running") running.push(run);
      }
    }
    if (running.length === 0) return;
    const id = setInterval(() => {
      running.forEach((job) => {
        getRun(job.slug)
          .then((s) => {
            setStatuses((prev) => ({
              ...prev,
              [s.model]: { ...prev[s.model], [s.dataset]: s },
            }));
            if (s.status !== "running") refreshComparison();
          })
          .catch((e) => console.error(e));
      });
    }, 2000);
    return () => clearInterval(id);
  }, [statuses, refreshComparison]);

  function toggleDataset(name: string) {
    setSelectedDatasets((prev) =>
      prev.includes(name) ? prev.filter((d) => d !== name) : [...prev, name]
    );
  }

  async function handleStart(model: ModelName, forceRerun: boolean) {
    if (selectedDatasets.length === 0) return;
    const batch = await startRuns(model, selectedDatasets, effectiveLimit, forceRerun);
    setStatuses((prev) => {
      const forModel = { ...prev[model] };
      for (const run of batch.runs) forModel[run.dataset] = run;
      return { ...prev, [model]: forModel };
    });
    if (batch.runs.every((r) => r.status !== "running")) refreshComparison();
  }

  async function handleClearDataset(model: ModelName, dataset: string) {
    const run = statuses[model][dataset];
    if (!run) return;
    await deleteRun(run.slug);
    setStatuses((prev) => {
      const forModel = { ...prev[model] };
      delete forModel[dataset];
      return { ...prev, [model]: forModel };
    });
    refreshComparison();
  }

  return (
    <div className="page">
      <header>
        <h1>Laya vs Open-Jev on JevBench</h1>
        <p className="subtitle">
          Typed-decision models scored by the same unmodified JevBench harness, fully offline.
        </p>
      </header>

      <section className="panel">
        <h2>Datasets</h2>
        <div className="split-picker">
          {datasetInfo.map((d) => (
            <label key={d.name} className="split-option">
              <input
                type="checkbox"
                checked={selectedDatasets.includes(d.name)}
                onChange={() => toggleDataset(d.name)}
              />
              {d.label} ({d.n})
            </label>
          ))}
        </div>
        <label className="limit-input">
          Limit per dataset (optional)
          <input
            type="number"
            min={1}
            value={limit}
            onChange={(e) => setLimit(e.target.value === "" ? "" : Number(e.target.value))}
            placeholder="all tasks in each dataset"
          />
        </label>
      </section>

      <section className="launchers">
        {MODELS.map(({ key, label }) => (
          <JobLauncher
            key={key}
            label={label}
            selectedDatasets={selectedDatasets}
            datasetInfo={datasetInfo}
            statuses={statuses[key]}
            disabled={selectedDatasets.length === 0}
            onStart={() => handleStart(key, false)}
            onRerun={() => handleStart(key, true)}
            onClearDataset={(dataset) => handleClearDataset(key, dataset)}
          />
        ))}
      </section>

      <section className="panel">
        <h2>Comparison</h2>
        {comparison ? (
          <ComparisonTable comparison={comparison} datasetInfo={datasetInfo} />
        ) : (
          <p>Loading...</p>
        )}
      </section>
    </div>
  );
}
