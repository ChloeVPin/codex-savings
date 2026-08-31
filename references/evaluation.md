# Evaluation plan

Evaluate the current workflow and each rewrite against the same task set. Do
not claim an improvement from prompt wording alone; record outputs, failures,
tokens, handoffs, and verification results.

## Quality hierarchy

Correctness and citation validity are hard gates. Among runs that pass those
gates, compare the weighted score:

- answer correctness: 40%
- citation validity and source support: 35%
- token efficiency: 20%
- handoff efficiency: 5%

Do not trade a quality regression for a lower token count. Handoff efficiency
means reducing redundant handoffs, not maximizing the smallest raw handoff
count.

## Metrics

### Answer correctness

Score whether the final answer or code change satisfies the definition of done.
Use an oracle, deterministic test, or qualified human review. Record partial
credit only when the task definition permits it.

### Citation validity

For every material research claim, check that the cited passage exists and
actually supports the claim. Track:

- statement support rate: supported material claims divided by checked claims;
- unsupported-claim rate;
- contradiction disclosure rate;
- source coverage across the defined subquestions.

A structural packet check is not semantic citation validation. Use passage-level
review by Sol, an independent reviewer, or the user. The report's suggested
90% response-level-support target is an experiment target, not a built-in fact or
universal acceptance threshold.

### Token efficiency

Measure total input and output tokens for the complete task, including retries
and handoffs. Also record packet size and approximate cost per successful task.
Successful-task cost is more useful than the cheapest individual call.

### Handoff efficiency

Record total handoffs, redundant handoffs, plan changes, and cycles to done.
Calculate redundant-handoff rate as redundant handoffs divided by total
handoffs. Treat a 10% ceiling as an initial hypothesis to test, not a guarantee.

## Benchmark set

Use at least these twelve tasks:

1. Narrow one-file coding fix where direct execution should be sufficient.
2. Ambiguous cross-file bug requiring a Sol plan.
3. Refactor constrained by a public API.
4. Failing test with two plausible root causes.
5. Security-sensitive configuration change requiring explicit verification.
6. Long-context repository task where compaction is necessary.
7. Factual question answerable by one current primary source.
8. Research question requiring decomposition into multiple subquestions.
9. Topic with conflicting primary and secondary sources.
10. Time-sensitive question with stale and current sources.
11. Research request where no reliable source supports the desired conclusion.
12. Mixed task where external documentation must inform a code change.

For each task, define the oracle, permitted sources, expected stopping point,
and whether a Sol handoff is required before running the baseline.

## Run record

Record a compact JSON or Markdown entry containing:

```yaml
task_id: "research-08"
workflow_version: "1.0"
mode: research
success: true
correctness: 0.0
citation_validity: 0.0
input_tokens: 0
output_tokens: 0
packet_tokens: 0
handoffs: 0
redundant_handoffs: 0
unsupported_claims: 0
contradictions: 0
notes: "Observed failure or verification evidence."
```

Compare the baseline and rewrite by task category, not only by aggregate
score. A rewrite is acceptable only if correctness and citation validity do not
regress on the benchmark set and the efficiency gains are reproducible.
