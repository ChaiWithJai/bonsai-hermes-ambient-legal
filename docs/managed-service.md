# Prepare legal drafts while counsel is away

The managed LaunchAgent checks the local queue every five minutes and processes one item per check, nearest due first. It starts the local model only when an eligible packet has no draft. After Hermes saves the draft and its final receipt, the worker verifies both records and stops its owned model and proxy. Counsel still decides whether to approve a draft or take any external action.

First, configure one database path for submissions and the scheduled profile:

```sh
export AMBIENT_DB="$HOME/.local/state/bonsai-ambient-legal/ambient.sqlite"
export AMBIENT_RUNS="$HOME/.local/state/bonsai-ambient-legal/runs"
python3 setup.py --out "$HOME/.hermes/profiles/ambient-legal-managed"
```

An existing queue can be used by setting `AMBIENT_DB` to its current path. Setup preserves existing data and refuses to overwrite a profile. For MLflow tool spans, use an interpreter with MLflow installed and set `AMBIENT_TRACE=1` before setup.

Second, set the downloaded model and matching Prism runtime paths, then install on a workstation dedicated to the demo:

```sh
export LLAMA_SERVER="/absolute/path/to/llama-server"
export BONSAI_MODEL="/absolute/path/to/Ternary-Bonsai-2-27B-PQ2_0.gguf"
python3 install_launch_agent.py \
  --managed-model "$BONSAI_MODEL" \
  --runtime "$LLAMA_SERVER" \
  --profile ambient-legal-managed \
  --dedicated-host
```

On the shared lab Mac, replace `--dedicated-host` with `--queue-module /absolute/path/to/gpu_queue.py`. The lab adapter reserves the Mac lane after three clear checks thirty seconds apart, and it leaves another model or queue reservation untouched. The repository does not require the lab adapter on a dedicated workstation.

Stop an existing manually managed model or proxy before enabling owned startup. If the older repository proxy LaunchAgent is installed, back up its plist and unload it with `launchctl bootout gui/$(id -u)/com.prismml.ambient-legal-proxy`. The managed job preserves occupied ports and waits instead of replacing their listeners. Pause an older Hermes cron job before relying on the managed scheduler so two schedulers do not target the same queue.

The worker rejects a new draft longer than 180 words, verifies that the selected packet is awaiting counsel, and requires a durable final Hermes answer. It preserves attempt records and stops after three attempts for an item revision. Existing drafts and reviewed packets remain unchanged. The source clause and proposed action still require counsel review; successful persistence does not establish legal quality.

Inspect the queue and installed job:

```sh
python3 ambient.py packets
launchctl print gui/$(id -u)/com.prismml.bonsai-ambient-legal
tail -n 20 "$HOME/Library/Logs/PrismML/ambient-legal.out.log"
```

Stop the service with `launchctl bootout gui/$(id -u)/com.prismml.bonsai-ambient-legal`. The Mac must stay awake and the user must remain logged in. The service does not refresh agreements, send messages or change ownership. A reboot recovery claim requires a separate test.
