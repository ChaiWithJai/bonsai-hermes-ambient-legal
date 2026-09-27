"""Local ambient legal demo. Fictional input, draft preparation, human decisions."""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from contextlib import contextmanager
from collections.abc import Iterator
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get("AMBIENT_DB", ROOT / "ambient.sqlite"))
SEED = ROOT / "fixtures/seed.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=10, isolation_level=None)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS items (id TEXT PRIMARY KEY, body TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS packets (id TEXT PRIMARY KEY, item_id TEXT NOT NULL, item_revision INTEGER NOT NULL, body TEXT NOT NULL, state TEXT NOT NULL, created_at TEXT NOT NULL, reviewed_at TEXT, reviewer TEXT, decision TEXT, FOREIGN KEY(item_id) REFERENCES items(id))")
        conn.execute("CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY, at TEXT NOT NULL, action TEXT NOT NULL, item_id TEXT NOT NULL, packet_id TEXT, detail TEXT NOT NULL)")
        conn.execute("BEGIN IMMEDIATE")
        try:
            if not conn.execute("SELECT 1 FROM items LIMIT 1").fetchone():
                items = json.loads(SEED.read_text())["items"]
                conn.executemany("INSERT INTO items(id,body,revision) VALUES (?,?,0)", [(r["id"], json.dumps(r)) for r in items])
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        with conn:
            yield conn
    finally:
        conn.close()


def get_item(conn: sqlite3.Connection, item_id: str) -> dict:
    row = conn.execute("SELECT body,revision FROM items WHERE id=?", (item_id,)).fetchone()
    if row is None:
        raise ValueError("Use an exact item ID from scan_queue.")
    return {**json.loads(row["body"]), "revision": row["revision"]}


def submit_request(item: dict) -> dict:
    required = {"id", "client", "request", "source", "clause", "due", "owner", "dependency", "next_action", "draft_outline"}
    if set(item) != required:
        raise ValueError(f"Request fields must be exactly: {', '.join(sorted(required))}.")
    if not re.fullmatch(r"AMB-[0-9]{3,}", item["id"]):
        raise ValueError("ID must match AMB- followed by at least three digits.")
    for field in ("client", "request", "source", "clause", "dependency", "next_action"):
        if not isinstance(item[field], str) or not item[field].strip():
            raise ValueError(f"{field} must be nonempty text.")
    if item["due"] is not None:
        date.fromisoformat(item["due"])
    if item["owner"] is not None and (not isinstance(item["owner"], str) or not item["owner"].strip()):
        raise ValueError("owner must be null or a nonempty name.")
    if not isinstance(item["draft_outline"], list) or not item["draft_outline"] or any(not isinstance(x, str) or not x.strip() for x in item["draft_outline"]):
        raise ValueError("draft_outline must contain nonempty text entries.")
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            if conn.execute("SELECT 1 FROM items WHERE id=?", (item["id"],)).fetchone():
                raise ValueError("Request ID already exists; no existing record was changed.")
            conn.execute("INSERT INTO items(id,body,revision) VALUES (?,?,0)", (item["id"], json.dumps(item)))
            conn.execute("INSERT INTO audit(at,action,item_id,packet_id,detail) VALUES (?,?,?,?,?)", (now(), "request_submitted", item["id"], None, json.dumps({"source": item["source"]})))
            conn.commit()
            return {"id": item["id"], "revision": 0, "accepted": True, "external_message_sent": False}
        except Exception:
            conn.rollback()
            raise


def scan_queue(as_of: str) -> dict:
    today = date.fromisoformat(as_of)
    with connect() as conn:
        rows = [get_item(conn, r["id"]) for r in conn.execute("SELECT id FROM items ORDER BY id")]
        result = []
        for r in rows:
            due = date.fromisoformat(r["due"]) if r["due"] else None
            days = (due - today).days if due else None
            if days is not None and days > 14:
                continue
            packet = conn.execute("SELECT id,state FROM packets WHERE item_id=? AND item_revision=? ORDER BY created_at DESC LIMIT 1", (r["id"], r["revision"])).fetchone()
            result.append({"id": r["id"], "client": r["client"], "request": r["request"], "source": r["source"], "due": r["due"], "calendar_days_until_due": days, "known_owner": r["owner"], "dependency": r["dependency"], "revision": r["revision"], "packet": dict(packet) if packet else None})
        result.sort(key=lambda r: (r["due"] is None, r["due"] or "", r["id"]))
        return {"fictional": True, "as_of": as_of, "count": len(result), "items": result}


def make_packet(item: dict, as_of: str) -> dict:
    due_text = item["due"] or "Unknown; confirm the delivery date before calculating an acceptance deadline"
    return {
        "fictional": True,
        "item_id": item["id"],
        "as_of": as_of,
        "client": item["client"],
        "draft_subject": f"Counsel review: {item['request']}",
        "source": item["source"],
        "source_clause": item["clause"],
        "due": item["due"],
        "due_display": due_text,
        "known_owner": item["owner"],
        "open_dependency": item["dependency"],
        "supporting_documents_checked": False,
        "evidence_scope": "This packet contains the request and source clause. No search for delivery evidence or supporting files was performed. An open dependency does not establish that a file is absent.",
        "proposed_next_action": item["next_action"],
        "draft_work_product": item["draft_outline"],
        "model_draft": None,
        "model_draft_status": "No model-authored draft has been saved; this outline is a deterministic fixture.",
        "approval_needed": "Counsel must approve any assignment, external communication, or assertion of completion.",
    }


def prepare_packet(item_id: str, expected_revision: int, as_of: str) -> dict:
    date.fromisoformat(as_of)
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            item = get_item(conn, item_id)
            if item["revision"] != expected_revision:
                raise ValueError("The item changed. Scan the queue and retry with its current revision.")
            packet_id = f"{item_id}-r{expected_revision}"
            previous = conn.execute("SELECT body,state FROM packets WHERE id=?", (packet_id,)).fetchone()
            if previous:
                result = {**json.loads(previous["body"]), "packet_id": packet_id, "state": previous["state"], "created": False}
                conn.commit()
                return result
            body = make_packet(item, as_of)
            conn.execute("INSERT INTO packets(id,item_id,item_revision,body,state,created_at) VALUES (?,?,?,?,?,?)", (packet_id, item_id, expected_revision, json.dumps(body), "awaiting_counsel", now()))
            conn.execute("INSERT INTO audit(at,action,item_id,packet_id,detail) VALUES (?,?,?,?,?)", (now(), "packet_prepared", item_id, packet_id, json.dumps({"as_of": as_of, "source": item["source"]})))
            conn.commit()
            return {**body, "packet_id": packet_id, "state": "awaiting_counsel", "created": True}
        except Exception:
            conn.rollback()
            raise


def review_packet(packet_id: str, reviewer: str, decision: str, note: str) -> dict:
    if decision not in {"approve_draft", "request_changes", "defer"}:
        raise ValueError("Decision must be approve_draft, request_changes, or defer.")
    if not reviewer.strip() or not note.strip():
        raise ValueError("A named reviewer and a decision note are required.")
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            packet = conn.execute("SELECT item_id,state FROM packets WHERE id=?", (packet_id,)).fetchone()
            if not packet:
                raise ValueError("Unknown packet ID.")
            if packet["state"] != "awaiting_counsel":
                raise ValueError("Packet already reviewed; inspect its current state.")
            conn.execute("UPDATE packets SET state=?,reviewed_at=?,reviewer=?,decision=? WHERE id=?", (decision, now(), reviewer.strip(), decision, packet_id))
            conn.execute("INSERT INTO audit(at,action,item_id,packet_id,detail) VALUES (?,?,?,?,?)", (now(), "human_review", packet["item_id"], packet_id, json.dumps({"reviewer": reviewer.strip(), "decision": decision, "note": note.strip()})))
            conn.commit()
            return {"packet_id": packet_id, "state": decision, "reviewer": reviewer.strip(), "note": note.strip(), "external_message_sent": False, "owner_changed": False}
        except Exception:
            conn.rollback()
            raise


def save_draft(packet_id: str, expected_item_revision: int, draft: str) -> dict:
    if not isinstance(draft, str) or len(draft.strip()) < 40 or len(draft) > 10000:
        raise ValueError("Draft must contain 40 to 10,000 characters.")
    if len(draft.split()) > 180:
        raise ValueError("Draft must contain at most 180 words. Shorten it before saving.")
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT item_id,item_revision,body,state FROM packets WHERE id=?", (packet_id,)).fetchone()
            if not row:
                raise ValueError("Unknown packet ID.")
            item = get_item(conn, row["item_id"])
            if row["state"] != "awaiting_counsel" or row["item_revision"] != expected_item_revision or item["revision"] != expected_item_revision:
                raise ValueError("Packet is stale or already reviewed. Read its current state.")
            body = json.loads(row["body"])
            if body["model_draft"]:
                if body["model_draft"] == draft.strip():
                    conn.commit()
                    return {"packet_id": packet_id, "saved": False, "state": row["state"], "model_draft": body["model_draft"], "word_count": len(body["model_draft"].split())}
                raise ValueError("A draft already exists. Human review is required before changing it.")
            body["model_draft"] = draft.strip()
            body["model_draft_status"] = "Unverified model draft for counsel review. No external message sent."
            conn.execute("UPDATE packets SET body=? WHERE id=?", (json.dumps(body), packet_id))
            conn.execute("INSERT INTO audit(at,action,item_id,packet_id,detail) VALUES (?,?,?,?,?)", (now(), "model_draft_saved", row["item_id"], packet_id, json.dumps({"characters": len(draft.strip())})))
            conn.commit()
            return {"packet_id": packet_id, "saved": True, "state": row["state"], "model_draft": body["model_draft"], "word_count": len(body["model_draft"].split()), "external_message_sent": False}
        except Exception:
            conn.rollback()
            raise


def list_packets() -> dict:
    with connect() as conn:
        packets = []
        for row in conn.execute("SELECT id,body,state,created_at,reviewed_at,reviewer,decision FROM packets ORDER BY created_at,id"):
            packets.append({**json.loads(row["body"]), "packet_id": row["id"], "state": row["state"], "created_at": row["created_at"], "reviewed_at": row["reviewed_at"], "reviewer": row["reviewer"], "decision": row["decision"]})
        return {"fictional": True, "count": len(packets), "packets": packets}


def tick(as_of: str) -> dict:
    scan = scan_queue(as_of)
    results = [prepare_packet(r["id"], r["revision"], as_of) for r in scan["items"] if not r["packet"]]
    return {"fictional": True, "as_of": as_of, "new_packets": len(results), "packets": results, "awaiting_counsel": len([p for p in list_packets()["packets"] if p["state"] == "awaiting_counsel"])}


def tool(name: str, description: str, properties: dict, required=(), readonly=True) -> dict:
    return {"name": name, "description": description, "inputSchema": {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}, "annotations": {"readOnlyHint": readonly, "destructiveHint": False, "openWorldHint": False}}


TOOLS = [
    tool("scan_queue", "Inspect fictional local legal requests and existing review packet state. This is read only.", {"as_of": {"type": "string", "description": "ISO date for this review"}}, ["as_of"]),
    tool("prepare_packet", "Prepare one local draft packet using an exact item ID and current revision. It does not send messages or assign owners.", {"item_id": {"type": "string"}, "expected_revision": {"type": "integer"}, "as_of": {"type": "string"}}, ["item_id", "expected_revision", "as_of"], False),
    tool("save_draft", "Save one model-authored work product for counsel review. This local draft is unverified and never sent externally.", {"packet_id": {"type": "string"}, "expected_item_revision": {"type": "integer"}, "draft": {"type": "string"}}, ["packet_id", "expected_item_revision", "draft"], False),
    tool("list_packets", "Read all prepared local packets and counsel decisions.", {}),
]


def execute(name: str, args: dict) -> dict:
    if name == "scan_queue":
        return scan_queue(args["as_of"])
    if name == "prepare_packet":
        return prepare_packet(args["item_id"], args["expected_revision"], args["as_of"])
    if name == "list_packets":
        return list_packets()
    if name == "save_draft":
        return save_draft(args["packet_id"], args["expected_item_revision"], args["draft"])
    raise ValueError("Unknown tool.")


if os.environ.get("AMBIENT_TRACE") == "1":
    import mlflow

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210"))
    mlflow.set_experiment("ambient-legal-demo")
    execute = mlflow.trace(name="ambient_legal_tool", span_type="TOOL")(execute)


def mcp() -> None:
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if "id" not in request:
                continue
            method = request.get("method")
            if method == "initialize":
                result = {"protocolVersion": request.get("params", {}).get("protocolVersion", "2024-11-05"), "capabilities": {"tools": {}}, "serverInfo": {"name": "ambient-legal-demo", "version": "1.0.0"}}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = request["params"]
                try:
                    result = {"content": [{"type": "text", "text": json.dumps(execute(params["name"], params.get("arguments", {})))}]}
                except Exception as exc:
                    result = {"isError": True, "content": [{"type": "text", "text": str(exc)}]}
            else:
                result = {}
            print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}), flush=True)
        except Exception as exc:
            print(f"MCP request error: {exc}", file=sys.stderr)


def cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    tick_cmd = sub.add_parser("tick", help="Run one deterministic ambient pass without a model")
    tick_cmd.add_argument("--as-of", default=date.today().isoformat())
    scan_cmd = sub.add_parser("scan")
    scan_cmd.add_argument("--as-of", default=date.today().isoformat())
    sub.add_parser("packets")
    sub.add_parser("mcp")
    submit_cmd = sub.add_parser("submit", help="Add one structured fictional request to the local queue")
    submit_cmd.add_argument("--file", type=Path, required=True)
    review_cmd = sub.add_parser("review", help="Record a human counsel decision; not available to the model")
    review_cmd.add_argument("--packet", required=True)
    review_cmd.add_argument("--reviewer", required=True)
    review_cmd.add_argument("--decision", required=True, choices=["approve_draft", "request_changes", "defer"])
    review_cmd.add_argument("--note", required=True)
    args = parser.parse_args()
    if args.command == "mcp":
        mcp()
    elif args.command == "tick":
        print(json.dumps(tick(args.as_of), indent=2))
    elif args.command == "scan":
        print(json.dumps(scan_queue(args.as_of), indent=2))
    elif args.command == "packets":
        print(json.dumps(list_packets(), indent=2))
    elif args.command == "submit":
        print(json.dumps(submit_request(json.loads(args.file.read_text())), indent=2))
    elif args.command == "review":
        print(json.dumps(review_packet(args.packet, args.reviewer, args.decision, args.note), indent=2))


if __name__ == "__main__":
    cli()
