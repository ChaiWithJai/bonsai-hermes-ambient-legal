"""Start owned local inference only when a scheduled review needs it."""
from __future__ import annotations
import argparse
import fcntl
import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
import urllib.request
from zoneinfo import ZoneInfo
import ambient
from run_review import run_review

TZ = ZoneInfo("America/New_York")
RUNS = Path(os.environ.get("AMBIENT_RUNS", str(ambient.DB.parent / "scheduled-runs")))

ROOT = Path(__file__).resolve().parent


def pending_item(now):
    packets = {p['packet_id']: p for p in ambient.list_packets()['packets']}
    for item in ambient.scan_queue(now.astimezone(TZ).date().isoformat())['items']:
        packet = packets.get(f"{item['id']}-r{item['revision']}")
        if packet and (packet['model_draft'] or packet['state'] != 'awaiting_counsel'):
            continue
        if len(list(RUNS.glob(f"{item['id']}-r{item['revision']}-*.json"))) >= 3:
            continue
        return item
    return None


def model_ready():
    try:
        with urllib.request.urlopen('http://127.0.0.1:5262/v1/models', timeout=5) as response:
            return any(m.get('id') == 'bonsai-ui-public-ternary-bonsai2' for m in json.load(response).get('data', []))
    except (OSError, ValueError):
        return False


def port_open(port):
    with socket.socket() as client:
        client.settimeout(.2)
        return client.connect_ex(('127.0.0.1', port)) == 0


def load_queue(path):
    spec = importlib.util.spec_from_file_location('ambient_gpu_queue', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The queue scans command arguments, so our --runtime llama-server path can
    # look like a running server. Exclude only this wrapper PID, never its children.
    scanner = module.blocking_processes
    module.blocking_processes = lambda text: [line for line in scanner(text)
        if line.split(maxsplit=1)[0] != str(os.getpid())]
    return module


def run(args):
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / '.managed.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'already_running'}
        now = datetime.now(TZ)
        item = pending_item(now)
        if item is None:
            return {'status': 'no_inference_needed'}
        if any(port_open(port) for port in (62737, 5262)):
            return {'status': 'waiting_for_existing_service', 'detail': 'Owned startup will not replace another listener.'}
        queue = load_queue(args.queue_module) if args.queue_module else None
        job = 'ambient-legal-scheduled-' + uuid.uuid4().hex
        if queue:
            for index in range(3):
                clear, reason = queue.probe('mac')
                if not clear:
                    return {'status': 'waiting_for_gpu', 'detail': reason}
                if index < 2:
                    time.sleep(30)
            queue.put(job, 'mac', {'kind': 'manual-integration', 'scope': 'Scheduled ambient legal model lifecycle'})
            if not queue.claim('mac', job):
                queue.update(job, 'cancelled', 'Another job owns the Mac lane; next tick can retry')
                return {'status': 'waiting_for_gpu'}
        services = []
        state = 'failed'
        try:
            env = {**os.environ, 'LLAMA_SERVER': str(args.runtime), 'BONSAI_MODEL': str(args.model)}
            for name, command in [('model', ['sh', str(ROOT / 'start_model.sh')]),
                                  ('proxy', [sys.executable, str(ROOT / 'settings_proxy.py')])]:
                with (RUNS / f'{job}-{name}.log').open('w') as log:
                    services.append(subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT))
            for _ in range(120):
                if any(process.poll() is not None for process in services):
                    raise RuntimeError('An owned model service exited before readiness')
                if model_ready():
                    break
                time.sleep(1)
            else:
                raise RuntimeError('Owned model did not become ready within 120 seconds')
            checks = [run_review(item, now.date().isoformat(), args.profile, RUNS)]
            state = 'failed' if any(item['status'] != 'completed' for item in checks) else 'completed'
            return {'status': state, 'queue_job': job if queue else None, 'checks': checks}
        finally:
            clean = True
            for process in reversed(services):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        try:
                            process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            clean = False
            if queue:
                queue.update(job, state if clean else 'needs_review', 'Owned services stopped' if clean else 'Owned cleanup could not be verified')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--profile', default='ambient-legal-managed')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--queue-module', type=Path, help='Shared gpu_queue.py module on a shared Mac')
    mode.add_argument('--dedicated-host', action='store_true', help='Use only on a workstation dedicated to this service')
    args = parser.parse_args()
    for name in ('runtime', 'model', 'queue_module'):
        value = getattr(args, name)
        if value and not value.expanduser().absolute().is_file():
            parser.error(f'{name} does not name a file')
        if value:
            setattr(args, name, value.expanduser().absolute())
    def stop(signum, frame):
        raise KeyboardInterrupt('Service interrupted')
    signal.signal(signal.SIGTERM, stop)
    print(json.dumps(run(args)), flush=True)


if __name__ == '__main__':
    main()
