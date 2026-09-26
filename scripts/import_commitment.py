"""Submit one Google-backed commitment snapshot to the local counsel queue."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ambient


def request_from_commitment(row, request_id):
    if row.get("source_kind") != "google_drive_api":
        raise ValueError("Connected intake requires a clause read through the Drive API.")
    if row.get("status") == "complete":
        raise ValueError("The commitment is already complete.")
    source = f"{row['id']} revision {row['revision']}, {row['source_file']} {row['source_section']}"
    return {
        "id": request_id,
        "client": row["customer"],
        "request": row["obligation"],
        "source": source,
        "clause": row["clause"],
        "due": row["due_date"] or None,
        "owner": row["owner"] or None,
        "dependency": row.get("evidence_needed") or "Completion evidence must be checked with the delivery team.",
        "next_action": "Prepare a source-grounded follow-up for counsel to review against the current register.",
        "draft_outline": [
            "State the obligation and cite its source section.",
            "Identify the evidence needed before claiming completion.",
            "Ask counsel to confirm responsibility and approve the proposed follow-up.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legal-repo", type=Path, required=True)
    parser.add_argument("--commitment", required=True)
    parser.add_argument("--request-id", required=True)
    args = parser.parse_args()
    module_path = args.legal_repo.expanduser().resolve() / "commitments.py"
    spec = importlib.util.spec_from_file_location("commitment_intake_source", module_path)
    legal = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legal)
    if not legal.google_configured():
        raise ValueError("Set LEGAL_GOOGLE_TOKEN_FILE to read the connected register.")
    row = legal.execute("get_commitment", {"commitment_id": args.commitment})
    request = request_from_commitment(row, args.request_id)
    result = ambient.submit_request(request)
    print(json.dumps({
        **result,
        "source_commitment": row["id"],
        "source_revision": row["revision"],
        "source_kind": row["source_kind"],
        "clause_sha256": hashlib.sha256(row["clause"].encode()).hexdigest(),
        "intake_kind": "google_snapshot",
        "register_updated": False,
    }, indent=2))


if __name__ == "__main__":
    main()
