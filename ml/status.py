"""ML research monitoring: aggregate per-asset artifacts into ml_status.json.

Observation only. Reads the three artifacts of every asset, hashes them, and
writes the snapshot the dashboard renders. The payload itself is assembled by
ml/report.py; this module only does IO and stamps generated_at_utc, the single
piece of wall-clock metadata in the file (it sits outside the determinism
claim, which covers the per-asset artifacts).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime

from . import artifacts, config, report

ARTIFACT_KINDS = ("hpo", "metrics", "strategy")


def sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="aggregate ML artifacts -> dashboard/ml_status.json")
    ap.add_argument("--tickers", default=",".join(config.TICKERS), help="comma-separated subset")
    args = ap.parse_args()

    assets, docs = [], []
    for t in [x.strip().upper() for x in args.tickers.split(",") if x.strip()]:
        adir = config.ASSETS_DIR / f"Asset_{t}"
        paths = {k: adir / f"{k}_{t}.json" for k in ARTIFACT_KINDS}
        if not all(p.exists() for p in paths.values()):
            continue
        loaded = {k: artifacts.read_json(p) for k, p in paths.items()}
        docs.extend(loaded.values())
        assets.append(
            report.asset_report(
                t, loaded["hpo"], loaded["metrics"], loaded["strategy"],
                {k: sha256_file(p) for k, p in paths.items()},
            )
        )
    assert assets, "no complete artifact set found — run the ML chain first"

    payload = report.payload(assets, report.envelope(docs))
    payload["generated_at_utc"] = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
    out = config.ASSETS_DIR.parent / "dashboard" / "ml_status.json"
    out.write_text(json.dumps(artifacts.canon(payload), sort_keys=True, indent=1) + "\n",
                   encoding="utf-8")

    for a in assets:
        print(f"{a['ticker']:5} test_logloss={a['test']['logloss']:.4f} "
              f"bAcc={a['test']['balanced_accuracy']:.3f} mcc={a['test']['mcc']:.3f} "
              f"tau={a['strategy']['tau']} sharpe={a['strategy']['test']['sharpe']} "
              f"trades={a['strategy']['test']['n_trades']}")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB, schema v{report.SCHEMA_VERSION})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
