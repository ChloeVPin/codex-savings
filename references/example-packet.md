# Example packets

These examples show the compact handoff shape. Sol receives the packet only;
Luna adds observations after executing the plan.

## Coding example

```yaml
protocol_version: "1.0"
cycle: 0
mode: coding
goal: "Fix the intermittent 500 error after a login token refresh."
definition_of_done: "The failing case is reproduced before the fix and three consecutive refresh logins pass afterward."
scope:
  in_scope: ["src/auth/login.ts", "src/auth/session.ts", "tests/auth/login.test.ts"]
  out_of_scope: ["Public sign-in API changes", "New dependencies"]
constraints:
  - "Keep signIn(email, password) unchanged."
  - "Use the existing Node 20 dependency set."
key_code_or_evidence:
  - id: E1
    source_type: file
    summary: "refresh() returns a new JWT but the cache key retains the old exp claim."
    excerpt: "The relevant session refresh and cache-key lines."
    path: "src/auth/session.ts:88-104"
attempted_work:
  - id: A1
    actor: luna
    action: "Retried refresh with backoff."
    result: "The 500 persisted, so the failure is not transient network loss."
failures: []
open_question_for_sol: "Should refresh invalidate the old cache entry before writing the new one, or should the token become the cache key?"
routing_hint: needs_coding_plan
```

## Research example

```yaml
protocol_version: "1.0"
cycle: 1
mode: research
goal: "Determine whether the proposed API behavior is supported by current official documentation."
definition_of_done: "Every conclusion has checked evidence and unresolved conflicts are disclosed."
scope:
  in_scope: ["Official API documentation and release notes"]
  out_of_scope: ["Unverified social-media claims"]
  time_boundary: "Current as of the access date"
constraints:
  - "Prefer primary sources."
  - "Do not infer undocumented behavior."
key_code_or_evidence:
  - id: E1
    source_type: web_page
    summary: "The official reference describes the request field but does not state its behavior in this edge case."
    excerpt: "Short exact passage from the reference."
attempted_work:
  - id: A1
    actor: luna
    action: "Opened the official reference and release notes for the planned query."
    result: "The reference was current but incomplete for the edge case."
    evidence_ids: [E1]
failures: []
open_question_for_sol: "Which targeted source should Luna check next to resolve the undocumented edge case?"
routing_hint: needs_research_plan
subquestions:
  - id: Q1
    question: "Is the edge-case behavior explicitly supported?"
    status: open
queries:
  - id: R1
    subquestion_id: Q1
    query: "site:official.example edge-case behavior release notes"
    status: planned
source_metadata:
  - evidence_id: E1
    title: "Official API reference"
    url: "https://official.example/reference"
    publisher: "Official organization"
    publication_date: "unknown"
    accessed_at: "YYYY-MM-DD"
    source_tier: primary
    quality_basis: "First-party reference for the API behavior."
    relevance: high
```
