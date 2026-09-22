#!/usr/bin/env python3
"""Build-time model fetcher.

Runs only inside `docker build` (the models stage of backend/Dockerfile),
never at container runtime. Skips the network entirely once a pinned
revision is already present on disk, so rebuilding after an app-code change
does not re-download anything — only bumping a revision in
models_manifest.json triggers a fresh download.

Two on-disk layouts, matching how each downstream loader actually resolves
its weights (see models_manifest.json's "note" fields for why):

  hub_cache  - populate the standard Hugging Face hub cache layout, so
               `AutoModel.from_pretrained(repo_id, revision=...)` /
               `laya.load(repo_id)` resolve it offline via HF_HOME. Also
               writes a `refs/main` pointer at the pinned commit: some
               callers (laya.load) don't pass a revision and default to
               "main", which only resolves offline if that ref exists
               locally — snapshot_download(revision=<exact hash>) alone
               does not create it.
  local_dir  - a plain directory copy, for loaders that take a literal
               filesystem path (open-jev-serve --checkpoint).

Completeness in both layouts is judged ONLY by a marker file written after
snapshot_download() returns successfully — never by "does some file exist",
which a build interrupted mid-download (crash, ENOSPC, cancellation) can
satisfy while still missing the actual multi-GB weight files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def fetched_marker(entry_dir: Path) -> Path:
    return entry_dir / ".fetched_revision"


def already_fetched(entry_dir: Path, revision: str) -> bool:
    marker = fetched_marker(entry_dir)
    return marker.exists() and marker.read_text().strip() == revision


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dest", required=True, help="root dir for hf_home/ and local_dir/ entries")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    dest = Path(args.dest)
    hf_home = dest / manifest["hf_home"]
    hf_home.mkdir(parents=True, exist_ok=True)

    from huggingface_hub import snapshot_download

    for entry in manifest["entries"]:
        name, repo_id, revision, layout = entry["name"], entry["repo_id"], entry["revision"], entry["layout"]

        if layout == "hub_cache":
            org_name = repo_id.replace("/", "--")
            repo_cache_dir = hf_home / "hub" / f"models--{org_name}"
            if already_fetched(repo_cache_dir, revision):
                print(f"[fetch_models] {name}: {repo_id}@{revision} already cached, skipping network", flush=True)
                continue
            print(f"[fetch_models] {name}: downloading {repo_id}@{revision} into hub cache", flush=True)
            snapshot_download(repo_id=repo_id, revision=revision, cache_dir=str(hf_home / "hub"))
            refs_dir = repo_cache_dir / "refs"
            refs_dir.mkdir(parents=True, exist_ok=True)
            (refs_dir / "main").write_text(revision)
            fetched_marker(repo_cache_dir).write_text(revision)
        elif layout == "local_dir":
            target = dest / entry["local_dir"]
            if already_fetched(target, revision):
                print(f"[fetch_models] {name}: {repo_id}@{revision} already cached, skipping network", flush=True)
                continue
            print(f"[fetch_models] {name}: downloading {repo_id}@{revision} into {target}", flush=True)
            snapshot_download(
                repo_id=repo_id, revision=revision, local_dir=str(target), local_dir_use_symlinks=False
            )
            fetched_marker(target).write_text(revision)
        else:
            raise ValueError(f"unknown layout {layout!r} for entry {name!r}")
        print(f"[fetch_models] {name}: done", flush=True)

    print("[fetch_models] all entries ready", flush=True)


if __name__ == "__main__":
    main()
