# Managed legal review for an existing request

The LaunchAgent loaded the local model, read the existing request queue and saved a draft for AMB-003-r0. The selected packet concerns deletion evidence under Aster amendment v2 section 1, which replaces the earlier MSA retention period. The worker verified the saved packet and the final Hermes receipt before marking the run complete.

The draft contains 168 words. The save tool first rejected 197 words, then 181 words, before accepting 168. Six native MLflow tool traces preserve the scan, packet read, preparation and all three save attempts. Model HTTP captures preserve the associated inference. The run took 168.78 seconds and consumed 45,631 input tokens and 3,051 output tokens, with 35,683 cached input tokens. The timing includes validation retries and is not an isolated model benchmark.

The source clause, October 6 deadline and request for counsel review are supported. The draft's final sentence says that no deletion occurred, which overstates what missing evidence establishes. Human review remains pending. The future profile now instructs the model to distinguish missing evidence from event nonoccurrence and focus on the clause, dependency and next action. That prompt change has not received an additional inference test.

The run used the actual September 26 local date and the existing database. Every request row and every other packet, including AMB-108, remained unchanged. The previous database and standalone proxy plist were backed up. The worker stopped both owned services and released the shared Mac queue.

The canonical five-minute managed LaunchAgent is installed. Its startup found no further pending drafts and did not invoke inference. The temporary job was unloaded, and the old weekday Hermes cron was paused to avoid duplicate scheduling. During the legal run, the installed finance scheduler detected the occupied service and waited instead of starting another model. The services require an awake Mac with the user logged in; reboot recovery was not tested.
