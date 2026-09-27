# Client request preparation

Prepare the governing clause, missing information and a proposed follow-up before counsel reviews a client request. Counsel reads the saved draft and records the decision.

## How it works

A scheduled worker asks Hermes and local Bonsai to prepare one pending request. It saves the source clause and draft together, then stops the model services it started.

The [reviewed retention draft](evidence/evidence-status-replay-20260927/README.md) asks counsel to identify the responsible party and obtain deletion evidence by October 6.

## Get started

With Python 3.10 or newer, process the sample requests. The first run creates four review packets; repeating it creates no duplicates.

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
| [Setup](docs/setup.md) | Configure Bonsai and Hermes. |
| [Scheduling](docs/managed-service.md) | Install and operate the scheduled worker. |
| [Architecture](docs/architecture.md) | Follow the tools, records and failure handling. |
| [Model parameters](docs/parameter-guide.md) | Choose settings and inspect the supporting measurements. |
| [Configuration capture](docs/recorded-configuration.md) | See the model and Hermes settings used in the recorded run. |
| [Google intake](docs/connected-intake.md) | Import a commitment and its agreement. |
| [Development](docs/development.md) | Find the implementation and run its tests. |
