# Hand a commitment to the morning review

Import a commitment from the legal workstation's Google register when counsel needs a draft follow-up. The importer reads the Sheet and its supporting Drive clause, then submits a snapshot to the local queue used by Hermes. It preserves the recorded owner, source revision and any unknown deadline.

First, configure Google access in a checkout of the [legal workstation](https://github.com/ChaiWithJai/bonsai-hermes-legal-workstation), including its private source index. Use the same `AMBIENT_DB` path supplied when creating the ambient Hermes profile.

```sh
export LEGAL_GOOGLE_TOKEN_FILE="$HOME/.config/bonsai-demo/google-access-token"
export AMBIENT_DB="$HOME/.local/state/bonsai-ambient-legal/requests.sqlite"
python3 scripts/import_commitment.py \
  --legal-repo /absolute/path/to/bonsai-hermes-legal-workstation \
  --commitment APL-008 \
  --request-id AMB-108
```

The command prints the imported ID, source revision and clause hash. It rejects local source fallback, completed commitments and duplicate request IDs. Credentials and Drive file IDs are omitted from its output. The importer changes the local queue only; it does not assign an owner or update Google Sheets.

The next morning job can prepare the request using the existing queue tools. To exercise the installed job immediately, find its ID with `hermes --profile ambient-legal-demo cron list`, then run `hermes --profile ambient-legal-demo cron run <job-id>`. Inspect the durable result with `hermes --profile ambient-legal-demo cron runs <job-id>` and the saved draft with `python3 ambient.py packets`.

An imported request is a snapshot. Subsequent Google edits do not update an existing packet, so counsel must check the current agreement and register before acting. Importing again requires a new request ID. Automatic source refresh and folder watching are not implemented.

## Recorded run

On September 26, the importer read APL-008 at revision 1 through the Google APIs and submitted AMB-108. The existing Hermes job completed execution `25b4dd0daca440149d9d7c2a4bd96bf0` and saved a model draft in AMB-108-r0. The [packet and agent review](../evidence/connected-intake-first-run.json) preserve the source clause and output.

The draft incorrectly called five calendar days business days and questioned the recorded owner. It remains unaccepted. The tool field now explicitly names calendar days and includes the recorded owner in the queue result. The revised instructions require the model to distinguish recorded ownership from acceptance. A replay on an isolated database copy corrected both statements. The draft still claimed that the schedule and leads were not on file, although the source only identified evidence needed. The [replay review](../evidence/connected-replay-v2-review.json) records that unsupported claim. Neither draft has human acceptance.

A [third replay](../evidence/connected-replay-v3-review.json) made the supporting-document boundary explicit and preserved the corrected date and owner. The saved draft had 201 words against 180-word guidance. The tool rejected a subsequent attempt to replace the pending draft. The tool now returns a computed word count on both initial and repeated saves.

## Request accounting

The third replay's Hermes summary reported seven model calls, but its normal usage log contained six. The [proxy accounting](../evidence/connected-replay-v3-proxy-usage.json) recovers the missing request from the saved HTTP exchanges. Each successive request extends the same conversation, and the last response completes the answer.

The missing request reached the 1,536-token output cap and took 78.1 seconds before Hermes requested a continuation. All seven requests used 58,538 input tokens and 5,719 output tokens, including 45,286 cached input tokens. Their request durations sum to 284.5 seconds; that sum excludes tool time and does not measure Slack response time. A separate [title-generation request](../evidence/connected-replay-v3-auxiliary-usage.json) used another 344 input and 534 output tokens.

The original incomplete-log record remains in evidence. The recovered counts describe this run's workload, not a price or a savings result. Hosted billing, human review and operating costs require separate measurements.
