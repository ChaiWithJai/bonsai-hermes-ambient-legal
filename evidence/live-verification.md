# Live verification, September 26, 2026

The local profile used Hermes, Ternary Bonsai 2 27B, the loopback sampling proxy, SQLite tools, and the running Hermes scheduler. The model and tool inputs used fictional agreements. No Slack app or Google Drive source was connected to this second demo.

The sampling proxy is installed as the macOS user LaunchAgent `com.prismml.ambient-legal-proxy`. `launchctl print` reported it running with PID 53757, and a GET to `127.0.0.1:5262/v1/models` returned the Bonsai model ID. The service restarts the proxy, but it does not start the shared Bonsai model server on port 62737.

The manual Hermes run called `scan_queue`, `prepare_packet`, and `save_draft` for AMB-004. It saved a 1,595-character model draft in packet `AMB-004-r0`. The packet retains `due: null` and asks counsel to confirm the delivery date before calculating the five-business-day acceptance window. It remains `awaiting_counsel`.

The first scheduled run, `12cf099789e74f1b8768031d41ab9671`, failed. It prepared packets for AMB-001, AMB-002, and AMB-003, then attempted three full draft tool calls in one response. The model repeatedly reached the configured 1,536-token output cap, so the attempt was interrupted. The durable Hermes run history records `failed` with `KeyboardInterrupt`. The three packets remained without model drafts. This failure led to the one-item, 180-word scheduled prompt in `install_schedule.sh` and `SOUL.md`.

The corrected scheduled run `f86294296cb54d7f8d7843549cbb74cb` completed. It saved a 1,224-character draft to `AMB-001-r0`. The next scheduled run, `3af3df8907a94be7ab107851165fff38`, also completed and saved a 1,244-character draft to `AMB-002-r0`. Both packets remain `awaiting_counsel`. The job ID is `943ea819227b`, active for weekdays at 7 a.m. America/New_York. The Hermes scheduler reported a running host gateway and the next run on September 28, 2026, at 7 a.m. Eastern. AMB-003 has a prepared packet but no model draft yet; it is the next eligible item.

The MLflow experiment `ambient-legal-demo` is experiment 43. The second corrected run produced four tool traces with state `OK`:

| Tool | MLflow trace |
| --- | --- |
| `scan_queue` | `tr-f9c76c886383e103cdfeaaac5de9322a` |
| `list_packets` | `tr-31e1f5edf6835221b9eba676fabe635a` |
| `prepare_packet` | `tr-2e662087247678ff572339510b6bbf16` |
| `save_draft` | `tr-984ef04a60f61983cbd1382c3bbb1477` |

The sampling proxy captured four HTTP 200 model exchanges for that run: `2d3ce61c07f848a6b0a0c222cabad19e`, `0f52d18fafe1456c96c0181ac0afd0a0`, `8b80ef347a1c48f1ab7d0e0ec245d420`, and `f3fa4ff54a5f47a082104a12e4fc0696`. Their respective elapsed times were 9.9, 33.0, 39.7, and 23.9 seconds. These are observed request times in this run, not a speedup claim. Full request and response captures remain local in the ignored `exchanges/` directory. The repository does not publish them.

The deterministic packet evaluation is logged in MLflow run `6eb0678f49694d9a8072fb387364f30b`, with machine-readable results in `evidence/evaluation.json`. It found four packets, three saved model drafts, three source citations in those drafts, the unknown AMB-004 acceptance date preserved, and AMB-003 linked to the controlling amendment. There were zero human review events. The observed draft lengths were 236, 171, and 186 words; the latter two came from the scheduled runs. The 180-word instruction is guidance to the model, not an enforced length gate, and AMB-002 exceeded it by six words.

The model drafts cite their fictional source sections and keep unknowns visible. They have not received human legal review. The traces prove that the named tools ran and returned successfully; they do not prove that every legal interpretation is correct, that the Mac will stay awake indefinitely, or that a recipient accepted an assignment. No owner was changed and no external message was sent by this tool surface. The model cannot call the human review command; counsel must use the local CLI after inspecting the draft.
