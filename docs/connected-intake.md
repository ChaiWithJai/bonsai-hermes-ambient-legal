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

The draft incorrectly called five calendar days business days and questioned the recorded owner. It remains unaccepted. The tool field now explicitly names calendar days and includes the recorded owner in the queue result. The revised instructions require the model to distinguish recorded ownership from acceptance. A new model run is still needed to validate those changes.
