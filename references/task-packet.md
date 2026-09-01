# Adaptive task packet

The packet is the only context Sol receives. It is a compact state artifact,
not a transcript. Use the same shape for coding, research, and mixed tasks;
omit research fields when they are not useful.

The canonical machine-readable shape is
[task-packet.schema.json](task-packet.schema.json). A Markdown packet may use
the same field names and ordering.

## Output punctuation

Never emit U+2014 in packet fields or generated responses. If source material
contains it, normalize the passage before including it and do not describe the
normalized text as an exact quotation.

## Budget and identity

- Target 1-3K tokens. If the packet approaches the limit, compact prose and old
  logs before removing current constraints, unresolved claims, failures,
  supporting excerpts, or the open question.
- `protocol_version` is currently `1.0`.
- `cycle` is a zero-based integer.
- Use stable IDs: `E1` for evidence, `C1` for claims, `Q1` for subquestions,
  `R1` for queries, `A1` for actions, `F1` for failures, `U1` for uncertainty,
  and `X1` for contradictions.
- Never use an array position as an identity. IDs must remain stable when the
  packet is compacted or reordered.

## Required core fields

```yaml
protocol_version: "1.0"
cycle: 0
mode: coding | research | mixed
goal: "One sentence describing the intended outcome."
definition_of_done: "Observable acceptance criteria."
scope:
  in_scope: ["Specific files, sources, or questions included."]
  out_of_scope: ["Explicit exclusions."]
  time_boundary: "Optional date or freshness requirement."
constraints:
  - "Public API, schema, dependency, safety, or compatibility limit."
key_code_or_evidence: []
attempted_work: []
failures: []
open_question_for_sol: "One focused decision Sol must make."
```

`key_code_or_evidence` contains concise, directly relevant items:

```yaml
key_code_or_evidence:
  - id: E1
    source_type: web_page | file | command_result | test_result | other
    summary: "The smallest useful summary."
    excerpt: "A short passage or output, normalized when needed."
    path: "Optional local path."
    url: "Optional source URL."
```

`attempted_work` records what Luna actually did, not proposed actions:

```yaml
attempted_work:
  - id: A1
    actor: luna
    action: "Command, search, inspection, or edit performed."
    result: "Observed result."
    evidence_ids: [E1]
```

Keep `failures` as concise objects so the next plan can distinguish a failed
attempt from an untried option:

```yaml
failures:
  - id: F1
    summary: "What failed and why it matters."
    recoverable: true
```

## Optional research fields

Use these only for research or mixed tasks:

```yaml
subquestions:
  - id: Q1
    question: "One atomic question."
    status: open | answered | blocked

queries:
  - id: R1
    subquestion_id: Q1
    query: "A targeted search query."
    status: planned | executed | discarded

source_metadata:
  - evidence_id: E1
    title: "Source title."
    url: "https://example.org/source"
    publisher: "Author or organization."
    publication_date: "YYYY-MM-DD or unknown"
    accessed_at: "YYYY-MM-DD"
    source_tier: primary | secondary | tertiary | firsthand | unknown
    quality_basis: "Why this source is credible for this claim."
    relevance: high | medium | low

claims:
  - id: C1
    text: "One externally checkable claim."
    status: supported | partial | unsupported | contradicted | unverified
    confidence: high | medium | low
    evidence_ids: [E1]
    uncertainty: "Reason for any limitation or uncertainty."

claim_evidence_map:
  C1: [E1]

uncertainty_log:
  - id: U1
    subject_id: C1
    level: high | medium | low
    reason: "What is uncertain and why."
    cycle: 0

contradictions:
  - id: X1
    claim_id: C1
    evidence_ids: [E1, E2]
    summary: "The conflict that must be resolved or exposed."
    status: open | resolved

routing_hint: direct_execution_allowed | needs_coding_plan | needs_research_plan | needs_validation | resolve_contradiction | escalate_to_sol | stop
routing_reason: "Why this route is appropriate for the current packet."
plan_history:
  - cycle: 0
    summary: "The prior plan in one or two lines."
    outcome: "What happened."
    changed: true

validation:
  status: not_run | needs_review | pass | fail
  checked_claim_ids: [C1]
  unsupported_claim_ids: []
  notes: "Structural or independent validation result."

state_digest: "Compact summary of older context removed during compaction."
```

Source quality is multi-dimensional. Do not substitute domain reputation or a
model-generated authority score for direct evidence, method quality, relevance,
recency, provenance, and conflicts of interest. For time-sensitive topics,
record both publication and access dates.

## Research output contract

Sol returns:

1. the selected mode and the one decision made;
2. subquestions and targeted queries when more research is needed;
3. source requirements and likely risks;
4. a claim/evidence or implementation plan;
5. validation steps and stopping criteria;
6. the smallest next action Luna can execute.

Luna updates the packet with observations and evidence. No claim is final until
its support status is checked. A URL existing is not proof that it supports a
claim. The structural validator checks IDs and references; semantic support
still requires passage-level review by Sol, an independent reviewer, or the
user.

## Coding output contract

Sol returns root cause, impact scope, implementation plan, risk points, and
verification steps. Luna makes the changes, runs the narrowest relevant checks,
and reports exact commands and results.

## Example: research packet

```yaml
protocol_version: "1.0"
cycle: 0
mode: research
goal: "Determine whether the proposed API behavior is supported by current official documentation."
definition_of_done: "Every conclusion has a checked source and unresolved conflicts are disclosed."
scope:
  in_scope: ["Official API documentation and release notes"]
  out_of_scope: ["Unverified social-media claims"]
  time_boundary: "Current as of the access date"
constraints: ["Prefer primary sources; do not infer undocumented behavior."]
key_code_or_evidence: []
attempted_work: []
failures: []
open_question_for_sol: "Which subquestion should Luna investigate first?"
routing_hint: needs_research_plan
subquestions:
  - id: Q1
    question: "Is feature X documented as supported?"
    status: open
queries:
  - id: R1
    subquestion_id: Q1
    query: "site:official.example feature X documentation"
    status: planned
```
