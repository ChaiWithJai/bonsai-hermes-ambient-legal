# Retention evidence and party attribution

The final replay saved a 152-word draft and a two-sentence receipt. It kept deletion status unverified and asked counsel to identify the responsible party and evidence holder. The supplied clause names a deletion deadline but does not name the obligated party.

| Attempt | Observed result |
| --- | --- |
| [First](first/review.json) | Correctly described missing evidence, then contradicted it by saying no actions had occurred. |
| [Revised](revised/review.json) | Preserved unverified deletion status, but attributed the obligation to Aster without source support. |
| [Attribution correction](attribution/review.json) | Preserved the unknown status and party, then requested counsel's decision. |

Each directory includes the source, model/runtime hashes, saved draft, final receipt and MLflow run. The same source was used in isolated queues. Instructions changed across attempts; sampling was stochastic. These development replays do not establish a general reliability rate or isolated performance improvement.

The worker verified durable drafts and final answers, then stopped its owned services. This was a manual invocation of the managed worker, not a new launchd-triggered run. The earlier [scheduled lifecycle evidence](../managed-launchd-20260927/README.md) remains separate. Human counsel review is pending.
