#!/bin/sh
set -eu
PROFILE="${AMBIENT_PROFILE:-ambient-legal-demo}"
DATE_SCRIPT="$HOME/.hermes/profiles/$PROFILE/scripts/ambient_date.py"
test -f "$DATE_SCRIPT" || { echo "Run setup.py first" >&2; exit 1; }
hermes --profile "$PROFILE" cron create '0 7 * * 1-5' \
  'Run the ambient legal review for the injected review date. Scan the queue and read packet state. Work on exactly one item: the nearest due item with no packet or no model draft. Prepare its packet, save one source-grounded draft of at most 180 words, and report what counsel must decide. Do not prepare or save multiple items in this run. Do not send external messages or claim an owner accepted work.' \
  --name 'Ambient legal morning handoff' \
  --script ambient_date.py \
  --deliver local \
  --failure-deliver local \
  --model bonsai-ui-public-ternary-bonsai2 \
  --provider custom \
  --reasoning-effort medium
