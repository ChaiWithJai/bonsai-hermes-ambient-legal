"""Install the local ambient sampling proxy as a macOS user LaunchAgent."""
import argparse
import plistlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LABEL = "com.prismml.ambient-legal-proxy"
DESTINATION = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Write and start the user service")
    args = parser.parse_args()
    if not args.install:
        parser.error("Pass --install after stopping any manually started proxy on port 5262")
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    plist = {
        "Label": LABEL,
        "ProgramArguments": [sys.executable, str(ROOT / "settings_proxy.py")],
        "WorkingDirectory": str(ROOT),
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(logs / "proxy.stdout.log"),
        "StandardErrorPath": str(logs / "proxy.stderr.log"),
        "EnvironmentVariables": {"AMBIENT_PROXY_PORT": "5262", "BONSAI_UPSTREAM": "http://127.0.0.1:62737"},
    }
    data = plistlib.dumps(plist)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    if DESTINATION.exists() and DESTINATION.read_bytes() != data:
        parser.error(f"Refusing to replace a different service at {DESTINATION}")
    DESTINATION.write_bytes(data)
    domain = f"gui/{subprocess.check_output(['id', '-u'], text=True).strip()}"
    result = subprocess.run(["launchctl", "bootstrap", domain, str(DESTINATION)], text=True, capture_output=True)
    if result.returncode and "already loaded" not in result.stderr.lower():
        parser.error(result.stderr.strip() or result.stdout.strip() or "launchctl bootstrap failed")
    print(f"Installed {LABEL} in {domain}; model server at 127.0.0.1:62737 remains a separate prerequisite.")


if __name__ == "__main__":
    main()
