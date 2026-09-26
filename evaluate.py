"""Deterministic checks over observed packets; this is not a legal-quality judge."""
import argparse
import json
import os
from pathlib import Path

import ambient

ROOT = Path(__file__).resolve().parent


def evaluate():
    seed = {r["id"]: r for r in json.loads((ROOT / "seed.json").read_text())["items"]}
    packets = ambient.list_packets()["packets"]
    drafts = [p for p in packets if p["model_draft"]]
    with ambient.connect() as conn:
        audit = [dict(row) for row in conn.execute("SELECT action,item_id,packet_id FROM audit ORDER BY seq")]
    result = {
        "scope": "Deterministic checks on the current local SQLite state and saved model drafts. Human legal review is not included.",
        "packets": len(packets),
        "model_drafts": len(drafts),
        "source_fields_match_fixture": all(p["source"] == seed[p["item_id"]]["source"] and p["source_clause"] == seed[p["item_id"]]["clause"] for p in packets),
        "saved_drafts_cite_source": sum(p["source"] in p["model_draft"] for p in drafts),
        "saved_drafts_awaiting_counsel": sum(p["state"] == "awaiting_counsel" for p in drafts),
        "unknown_acceptance_due_preserved": next((p["due"] is None for p in packets if p["item_id"] == "AMB-004"), None),
        "amendment_record_points_to_v2": next(("amendment v2" in p["source"] and p["due"] == "2026-10-06" for p in packets if p["item_id"] == "AMB-003"), None),
        "human_review_events": sum(r["action"] == "human_review" for r in audit),
        "draft_word_counts": {p["packet_id"]: len(p["model_draft"].split()) for p in drafts},
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mlflow", action="store_true", help="Log numeric checks to local MLflow")
    parser.add_argument("--out", type=Path, help="Write JSON evidence to a file")
    args = parser.parse_args()
    result = evaluate()
    if args.mlflow:
        os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
        import mlflow

        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210"))
        mlflow.set_experiment("ambient-legal-demo")
        with mlflow.start_run(run_name="packet-state-checks") as run:
            mlflow.set_tag("evaluation_scope", "deterministic_packet_checks")
            mlflow.log_metrics({
                "packets": result["packets"],
                "model_drafts": result["model_drafts"],
                "source_fields_match_fixture": int(result["source_fields_match_fixture"]),
                "saved_drafts_cite_source": result["saved_drafts_cite_source"],
                "unknown_acceptance_due_preserved": int(bool(result["unknown_acceptance_due_preserved"])),
                "amendment_record_points_to_v2": int(bool(result["amendment_record_points_to_v2"])),
                "human_review_events": result["human_review_events"],
            })
            result["mlflow_run_id"] = run.info.run_id
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
