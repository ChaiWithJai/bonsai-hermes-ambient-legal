# Package check

On September 26, 2026, `python3 -m unittest -v test_ambient.py` passed all five tests. Python compilation succeeded for the package scripts, and shell syntax checks passed for `start_model.sh` and `install_schedule.sh`.

A recursive text scan of publishable files found no absolute `/Users/` paths, Slack or GitHub token prefixes, private key markers, gateway key assignments, or the user's email. The scan excluded `exchanges/`, `logs/`, local SQLite files, and Python bytecode. Those paths are also excluded by `.gitignore`; they contain runtime data and must stay out of the public repository. The source uses placeholders for the runtime and model paths.

The live model evidence is in `live-verification.md`. The LaunchAgent was running when checked, the Hermes scheduler reported one active job, and three of four prepared packets had model drafts. AMB-003 was the next queued item. The package does not include Slack credentials, a Drive connection, or a service that starts the shared model server.
