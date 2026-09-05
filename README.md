# Codex Savings

A bounded workflow for coding, research, and mixed tasks. It separates evidence gathering, execution, and focused reasoning while keeping the packet passed between steps small enough to inspect.

## Install

Install the skill globally:

```sh
npx skills add ChloeVPin/codex-savings --skill codex-savings -g -a codex -y
```

Or install it in the current project:

```sh
npx skills add ChloeVPin/codex-savings --skill codex-savings -a codex -y
```

Update it with:

```sh
npx skills update codex-savings
```

## Use

The skill supports coding, research, and mixed modes. Its routing hints, role labels, packet budget, and handoff limit are advisory. The repository helpers do not enforce model identity, thread isolation, spending limits, or termination.

The canonical packet contract is in [references/task-packet.md](references/task-packet.md).

```sh
python3 codex-savings/scripts/route_task.py "Compare the current API docs"
python3 codex-savings/scripts/validate_packet.py packet.json
python3 codex-savings/scripts/validate_research.py packet.json
```

## Limits

The validators check structure, identifiers, cross-references, and claim-to-evidence consistency. They cannot prove semantic entailment or make an agent follow the protocol.

## License

MIT. See [LICENSE](LICENSE).
