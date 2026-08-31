# Codex Savings

Codex Savings is a bounded, role-separated workflow for coding, research, and
mixed tasks. Luna gathers evidence and executes. Sol receives only a compact
packet and provides focused reasoning. The protocol is designed to preserve
correctness while reducing unnecessary context and handoff cost.

## Install

Clone the repository and install the skill:

```bash
git clone https://github.com/ChloeVPin/codex-savings.git
cd codex-savings
./scripts/install.sh
```

For a local checkout, run:

```bash
./codex-savings/scripts/install.sh
```

Restart Codex and invoke `$codex-savings`. If the skill is unavailable, copy
`references/loop-prompt.md` into standard ChatGPT or another compatible agent.

## Modes

- `coding`: bounded implementation, debugging, testing, and verification.
- `research`: question decomposition, query planning, source triage,
  claim/evidence mapping, citation validation, and uncertainty reporting.
- `mixed`: external research that informs a repository change.

Research mode is opt-in. Codex-only capabilities such as local files,
terminals, or thread/model handoffs are optional; the standalone prompt uses
manual packet transfer as its fallback.

## Packet and helpers

The canonical packet contract is documented in
`references/task-packet.md` and `references/task-packet.schema.json`.

```bash
python3 codex-savings/scripts/route_task.py "Compare the current API docs"
python3 codex-savings/scripts/validate_packet.py packet.json
python3 codex-savings/scripts/validate_research.py packet.json
```

The routing helper is advisory. The packet validator checks structure, stable
IDs, cross-references, and the approximate 1-3K token budget. The research
validator checks claim/evidence consistency; it cannot prove semantic
entailment, so final citation review remains required.

## Evaluation

Use `references/evaluation.md` to compare the baseline and rewrite. Correctness
and citation validity are hard gates. Among passing runs, the suggested metric
weights are 40% correctness, 35% citation validity, 20% token efficiency, and
5% handoff efficiency.

Do not rely on fixed quota, price, or model-performance claims. Verify current
provider documentation before using those values for routing decisions.

## License

MIT.
