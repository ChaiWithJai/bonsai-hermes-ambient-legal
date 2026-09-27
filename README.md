# Ambient legal assistant

Prepare the next client request for counsel before the morning review. The scheduled agent assembles the source clause, unresolved dependency and proposed action, then saves a draft for counsel to inspect. Counsel still decides whether to accept a draft, assign an owner, send a message, or represent that work is complete.

The [public reproduction guide](https://gist.github.com/ChaiWithJai/24ac06f5349bf5f4c6ff3a3dae6d3557) gives the short command sequence and the observed limits of the scheduled run.

The sample A+ Active Services requests cover a workshop plan, escalation coverage, recording deletion evidence, and an acceptance date that cannot be calculated yet. AMB-003 cites an amendment that replaces the earlier retention clause. AMB-004 keeps its due date unknown because delivery has not been confirmed. No real client agreement, patient record, or employee interview is included.

## Inspect the workflow without a model

From this directory:

```sh
python3 -m unittest discover -s tests -v
AMBIENT_DB=/tmp/ambient-legal-demo.sqlite python3 ambient.py tick --as-of 2026-09-26
AMBIENT_DB=/tmp/ambient-legal-demo.sqlite python3 ambient.py packets
```

The first tick prepares four packets. A second tick makes no duplicates. This is a deterministic fixture run, not Bonsai inference. `python3 make_evidence.py` writes a labeled copy of that run to `evidence/deterministic-run.json` using a temporary database. The local SQLite database records packet preparation and review decisions in `audit`. It does not synchronize with Slack or Google Drive.

To add another request, copy `fixtures/incoming-example.json`, give it a new `AMB-` ID, and run `python3 ambient.py submit --file your-request.json`. The next scheduled pass will see it. Submission rejects duplicate IDs and records an audit event. This file-based handoff represents a local request source; the [connected intake guide](docs/connected-intake.md) imports a selected commitment from the Google register and its Drive agreement. Folder watching is not implemented.

## Run through Ternary Bonsai 2 27B and Hermes

Install the matching Prism runtime and GGUF from the [Bonsai demo](https://github.com/PrismML-Eng/Bonsai-demo) and [model card](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf). The reference setup is an M5 Pro with 48 GiB RAM and Prism runtime `b10709-9a9394a`. Stock llama.cpp lacks the required ternary kernels. Supply your own absolute paths:

```sh
export LLAMA_SERVER=/absolute/path/to/llama-server
export BONSAI_MODEL=/absolute/path/to/Ternary-Bonsai-2-27B-PQ2_0.gguf
sh start_model.sh
```

In another terminal, run `python3 settings_proxy.py`. On macOS, run `python3 install_proxy.py --install` after stopping the manual proxy to keep it running as a user LaunchAgent. It serves `127.0.0.1:5262` and forwards to the model on `127.0.0.1:62737`. It applies the settings in `config/sampling.json`: temperature 1, top-p 0.95, top-k 20, min-p 0.05, presence penalty 0, repetition penalty 1, medium thinking, and at most 1,536 response tokens. The server uses 65,536 context tokens, one slot, GPU offload, `--jinja`, and a 512-token reasoning budget. The proxy stores local request and response JSON under `exchanges/`, so keep that directory private if you replace the fictional data with sensitive material. The proxy service does not start the Bonsai model server; that remains a separate prerequisite.

Create the isolated profile under the installed Hermes home:

```sh
export AMBIENT_DB="$HOME/.local/state/bonsai-ambient-legal/requests.sqlite"
python3 setup.py --out "$HOME/.hermes/profiles/ambient-legal-demo"
hermes --profile ambient-legal-demo chat
```

Use the same `AMBIENT_DB` value for CLI submissions and inspection. Setup saves its absolute path in the MCP configuration so the scheduled agent reads the same queue, even from another working directory. An existing profile needs its MCP environment updated and its tool process restarted.

The setup refuses to overwrite an existing profile. It adds no credentials. The profile exposes four narrow tools: queue scan, packet preparation, draft saving, and packet readback. Tool search and memory are off. The model cannot approve its own work, send a client message, or assign an owner through these tools. Counsel can record a reviewed decision from a local terminal with `python3 ambient.py review --packet AMB-001-r0 --reviewer "Counsel name" --decision approve_draft --note "Reviewed against the source clause"`. This saves a local decision only. An approved draft remains a draft until a separate authorized workflow acts on it.

For MLflow tool spans, install MLflow in the Python interpreter used by the MCP server, set `AMBIENT_PYTHON=/absolute/path/to/that/python` and `AMBIENT_TRACE=1` when running `setup.py`, and point `MLFLOW_TRACKING_URI` at your local tracking server. The profile then creates the `ambient-legal-demo` experiment. The HTTP proxy captures model calls independently; tool spans alone do not establish model quality.

For a manual model run, ask: “Run the ambient legal review for 2026-09-26. Work on exactly one eligible item, save a useful draft, and report which decision counsel must make.” Then inspect `python3 ambient.py packets`. Ask separately why AMB-004 has no due date and which source controls AMB-003. Model-authored drafts are labeled unverified in the packet. Record a review decision in the local terminal only after inspecting the exact packet.

Run `python3 evaluate.py --out evidence/evaluation.json` to check saved packet fields, source citations, the unknown acceptance date, amendment precedence, and review events. Add `--mlflow` when MLflow is installed and listening locally to log those counts as metrics. These checks cover record consistency, not the legal quality of the generated text; counsel must review drafts. See `evidence/live-verification.md` for observed run and trace IDs, including the failed first schedule attempt and its correction.

## Schedule the handoff

For automatic model startup and cleanup, use the [managed service guide](docs/managed-service.md). It processes one pending packet per five-minute check and reserves the GPU on a shared lab machine. The older Hermes cron mode below still requires an independently available model.

After the profile and model work in a manual run, `sh install_schedule.sh` creates a Hermes cron job at 7 a.m. on weekdays. Hermes injects the current America/New_York date from the profile's `scripts/ambient_date.py`. The job scans the queue and works on one item per run, nearest due first, so the draft fits the local response budget. Its report remains local. It does not notify counsel or clients. Check `hermes --profile ambient-legal-demo cron list` and `hermes --profile ambient-legal-demo cron runs <job-id>` for durable execution results. The Mac, Hermes scheduler, proxy, and model must remain available. To make work visible in Slack, configure a separate Hermes Slack app and delivery target under your own credentials; this repository does not install one.

The [managed lifecycle run](evidence/managed-launchd-20260927/README.md) started local inference from launchd, saved a 168-word draft for an existing request, and stopped its owned services. The record includes six native MLflow tool traces and the two drafts rejected by the word limit. Counsel review remains pending; the preserved draft and its identified wording issue are available for inspection.

Agent configuration lives in `config/`, sample requests in `fixtures/`, and regression tests in `tests/`. Intake and evidence-export utilities live in `scripts/`. The root commands remain the entry points for queue operations, profile setup and service startup.
