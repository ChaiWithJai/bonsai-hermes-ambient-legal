"""Run one local counsel draft and verify its durable packet and final response."""
import fcntl
import json
import os
import subprocess
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
import ambient
from lib.hermes_result import cursor, final_answer


def run_review(item, as_of, profile, runs):
    key = f"{item['id']}-r{item['revision']}"
    runs.mkdir(parents=True, exist_ok=True)
    with (runs / f'.{key}.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'already_running', 'packet_id': key}
        prompt = (f"Review date: {as_of}. Prepare only item {item['id']} revision {item['revision']}. "
                  "Scan the queue and read existing packets, then prepare the selected packet if needed. "
                  "Read its exact source clause, write and save one draft of at most180 words for counsel. "
                  "Distinguish source facts, unknown evidence and proposed action. Do not claim that "
                  "a deletion, delivery, assignment or approval occurred. Finish with a short receipt "
                  "identifying the saved packet and the decision counsel needs to make.")
        prompt = prompt.replace('most180', 'most 180')
        database = Path.home() / '.hermes/profiles' / profile / 'state.db'
        before = cursor(database)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        destination = runs / f'{key}-{stamp}.json'
        result = {'packet_id': key, 'as_of': as_of, 'status': 'running', 'created_at_utc': datetime.now(timezone.utc).isoformat()}
        destination.write_text(json.dumps(result, indent=2) + '\n')
        started = time.monotonic()
        try:
            proc = subprocess.run(['hermes', '--profile', profile, 'chat', '--oneshot', '-Q', '--run-budget', '480', '-q', prompt],
                                  capture_output=True, text=True, timeout=540, env=os.environ.copy())
            destination.with_suffix('.stdout.log').write_text(proc.stdout)
            destination.with_suffix('.stderr.log').write_text(proc.stderr)
            result['exit_code'] = proc.returncode
            if proc.returncode:
                raise ValueError('Hermes exited without completing the review')
            session, answer = final_answer(database, before, prompt)
            packet = next((p for p in ambient.list_packets()['packets'] if p['packet_id'] == key), None)
            if not packet or not packet['model_draft'] or packet['state'] != 'awaiting_counsel':
                raise ValueError('The selected packet has no saved draft awaiting counsel')
            if len(packet['model_draft'].split()) > 180:
                raise ValueError('Saved draft exceeds the requested 180 words')
            result.update(status='completed', session_id=session, final_answer=answer,
                          model_draft=packet['model_draft'], draft_words=len(packet['model_draft'].split()), human_review='pending')
        except (ValueError, OSError, sqlite3.Error, subprocess.TimeoutExpired) as error:
            result.update(status='failed', error=str(error))
        finally:
            result['elapsed_seconds'] = round(time.monotonic() - started, 2)
            temporary = destination.with_suffix('.pending')
            temporary.write_text(json.dumps(result, indent=2) + '\n')
            os.replace(temporary, destination)
        return result
