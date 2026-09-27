#!/bin/sh
set -eu
: "${LLAMA_SERVER:?Set LLAMA_SERVER to the matching Prism llama-server binary}"
: "${BONSAI_MODEL:?Set BONSAI_MODEL to Ternary-Bonsai-2-27B-PQ2_0.gguf}"
exec "$LLAMA_SERVER" -m "$BONSAI_MODEL" --host 127.0.0.1 --port 62737 --alias bonsai-ui-public-ternary-bonsai2 -c 65536 -np 1 -ngl 99 --jinja --reasoning-budget 512 --image-max-tokens 1024
