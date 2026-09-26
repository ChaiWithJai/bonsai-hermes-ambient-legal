"""Create an isolated Hermes profile without copying credentials."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Profile path below ~/.hermes/profiles/")
    args = parser.parse_args()
    out = args.out.expanduser().resolve()
    expected_parent = (Path.home() / ".hermes" / "profiles").resolve()
    if out.parent != expected_parent:
        parser.error(f"Profile must be a direct child of {expected_parent}")
    if out.exists():
        parser.error(f"Refusing to overwrite {out}")
    config = json.loads((ROOT / "hermes-config.json").read_text())
    config["mcp_servers"]["ambient_legal"]["command"] = os.environ.get("AMBIENT_PYTHON", sys.executable)
    config["mcp_servers"]["ambient_legal"]["args"] = [str(ROOT / "ambient.py"), "mcp"]
    if os.environ.get("AMBIENT_TRACE") == "1":
        config["mcp_servers"]["ambient_legal"]["env"] = {"AMBIENT_TRACE": "1", "MLFLOW_DISABLE_AGENT_HINT": "1", "MLFLOW_TRACKING_URI": os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5210")}
    server_env = config["mcp_servers"]["ambient_legal"].setdefault("env", {})
    server_env["AMBIENT_DB"] = str(Path(os.environ.get("AMBIENT_DB", ROOT / "ambient.sqlite")).expanduser().resolve())
    out.mkdir(parents=True)
    (out / "config.yaml").write_text(json.dumps(config, indent=2) + "\n")
    shutil.copy2(ROOT / "SOUL.md", out / "SOUL.md")
    scripts_dir = out / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(ROOT / "ambient_date.py", scripts_dir / "ambient_date.py")
    print(f"Created {out}; no credentials were copied.")


if __name__ == "__main__":
    main()
