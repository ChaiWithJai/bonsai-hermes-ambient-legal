"""Create clearly labeled deterministic evidence without a model or credentials."""
import json
import tempfile
from pathlib import Path

import ambient

ROOT = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as directory:
    ambient.DB = Path(directory) / "ambient.sqlite"
    before = ambient.scan_queue("2026-09-26")
    first = ambient.tick("2026-09-26")
    second = ambient.tick("2026-09-26")
    packets = ambient.list_packets()
    with ambient.connect() as conn:
        audit = [dict(row) for row in conn.execute("SELECT seq,at,action,item_id,packet_id,detail FROM audit ORDER BY seq")]
    evidence = {
        "kind": "deterministic_fixture_run",
        "model_inference": False,
        "hermes_execution": False,
        "slack_delivery": False,
        "as_of": "2026-09-26",
        "before": before,
        "first_tick": first,
        "second_tick": second,
        "packets": packets,
        "audit": audit,
    }
    destination = ROOT / "evidence" / "deterministic-run.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"Wrote {destination}")
