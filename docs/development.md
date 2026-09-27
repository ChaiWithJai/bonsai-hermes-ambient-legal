# Development

| Location | What to change |
| --- | --- |
| `ambient.py` | Queue, packet persistence, review decisions and MCP tools. |
| `managed_tick.py`, `run_review.py` | Scheduled model lifecycle and draft verification. |
| `config/` | Agent instructions, tools and sampling. |
| `fixtures/` | Sample requests, clauses and submission format. |
| `scripts/` | Google intake, date context and usage export. |
| `tests/` | Source, persistence and scheduling regression checks. |
| `docs/`, `evidence/` | Operating guides and recorded runs. |

Run `python3 -m unittest discover -s tests -v` after changing the workflow. Keep generated drafts and runtime state in their configured data directories; the source checkout contains the implementation and sample inputs.
