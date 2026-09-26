"""Account for an explicitly selected, ordered model turn from proxy captures."""
import argparse
import hashlib
import json
from pathlib import Path


def export(paths, expected_calls):
    if len(paths) != expected_calls or not paths:
        raise ValueError("Capture count must match the completed turn's reported call count.")
    calls, seen, previous = [], set(), None
    for number, path in enumerate(paths, 1):
        raw = path.read_bytes()
        data = json.loads(raw)
        response = data["response"]
        messages = data["request"]["messages"]
        identifier = response["id"]
        if identifier in seen:
            raise ValueError("Duplicate response ID.")
        if data["http_status"] != 200:
            raise ValueError("Failed request requires separate accounting.")
        if previous is not None and (len(messages) <= len(previous) or messages[:len(previous)] != previous):
            raise ValueError("Captures are not an extending conversation in the supplied order.")
        usage = response["usage"]
        finish = response["choices"][0]["finish_reason"]
        calls.append({"call": number, "response_id": identifier,
                      "input_tokens": usage["prompt_tokens"],
                      "output_tokens": usage["completion_tokens"],
                      "cached_input_tokens": usage.get("prompt_tokens_details", {}).get("cached_tokens", 0),
                      "seconds": data["seconds"], "finish_reason": finish,
                      "capture_file": path.name, "capture_sha256": hashlib.sha256(raw).hexdigest()})
        previous = messages
        seen.add(identifier)
    if calls[-1]["finish_reason"] != "stop":
        raise ValueError("The final capture must contain a completed answer.")
    return {"calls": calls,
            "total_input_tokens": sum(c["input_tokens"] for c in calls),
            "total_output_tokens": sum(c["output_tokens"] for c in calls),
            "total_cached_input_tokens": sum(c["cached_input_tokens"] for c in calls),
            "sum_request_seconds": sum(c["seconds"] for c in calls),
            "scope": "Selected completed model turn, including truncation continuations. Auxiliary requests, tool time, human review and hosted pricing are separate. Request tokens include repeated and cached context."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-calls", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("captures", type=Path, nargs="+")
    args = parser.parse_args()
    result = export(args.captures, args.expected_calls)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(args.out)
