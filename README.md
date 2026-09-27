# Client request preparation

Prepare the governing clause, missing information and a proposed follow-up before counsel reviews a client request. Counsel reads the saved draft and records the decision.

## How it works

A scheduled worker takes one pending request, starts local Bonsai inference and asks Hermes to prepare a draft. The application saves the packet and stops the model services it started. See the [architecture](docs/architecture.md) for data flow, persistence and failure handling.

The [recorded scheduled run](evidence/managed-launchd-20260927/README.md) saved a 168-word retention draft citing the controlling amendment and October 6 deadline.

## Get started

The example uses sample agreements and requests. With Python 3.10 or newer, run the sample queue. The first tick creates four packets; repeating it creates no duplicates. [Setup](docs/setup.md) adds model drafts, and [scheduling](docs/managed-service.md) enables automatic preparation.

```sh
git clone https://github.com/ChaiWithJai/bonsai-hermes-ambient-legal.git
cd bonsai-hermes-ambient-legal
python3 -m unittest discover -s tests -v
export AMBIENT_DB="$(mktemp -d)/requests.sqlite"
python3 ambient.py tick --as-of 2026-09-26
python3 ambient.py packets
```

## Resources

| Resource | Use it to |
| --- | --- |
| [Setup](docs/setup.md) | Run the agent and connect its inputs. |
| [Model parameters](docs/parameter-guide.md) | Understand the settings, evidence and tuning tradeoffs. |
| [Configuration capture](docs/recorded-configuration.md) | Inspect the recorded model and Hermes settings. |
| [Google intake](docs/connected-intake.md) | Import a commitment and its agreement. |
| [Development](docs/development.md) | Find the implementation and run its tests. |
