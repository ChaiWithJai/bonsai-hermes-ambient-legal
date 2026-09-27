# From incoming request to counsel's decision

The application stores incoming requests and prepared packets in SQLite. Each request carries its agreement clause and dependency information. CLI submission and the Google intake importer write into the same queue configured by `AMBIENT_DB`.

A scheduled check selects one eligible request, nearest due first. The managed worker starts its model server and sampling proxy, waits for readiness, and invokes the isolated Hermes profile. Hermes exposes tools for queue scanning, packet preparation, draft saving and readback. Bonsai reads the tool results and proposes the draft.

The application rejects a new draft above 180 words and verifies persistence before reporting completion. A final Hermes answer must also exist in durable session storage. Attempts are preserved; the worker limits retries and leaves a failed item for investigation after its budget is exhausted. The worker stops only the model and proxy processes it started.

Counsel reads the packet and records a decision through the review command. The model's tools cannot record that decision, assign an owner or send a client message. A recorded approval is a local review event; an external action needs a separate integration.

## Storage and connections

| Component | Data and responsibility |
| --- | --- |
| SQLite queue | Requests, packet revisions, drafts and review audit events. |
| Google importer | Reads a selected register commitment and its Drive agreement using your credentials. |
| Hermes profile | Stores the model endpoint, tool paths and instructions. |
| Bonsai and proxy | Serve local model requests; the proxy captures request and response payloads. |
| Run directory | Preserves worker results and attempts. |
| Optional MLflow | Records tool inputs, outputs and execution status. |

Set one absolute database path for the CLI and profile before installation. An existing listener or occupied GPU reservation leaves a managed pass waiting instead of replacing another service. The Mac must remain awake and logged in. The service processes supplied requests; automatic Drive folder watching and source refresh are separate integration work.

See [setup](setup.md), [Google intake](connected-intake.md) and [managed operation](managed-service.md) for commands and inspection steps.
