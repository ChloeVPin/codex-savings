#!/usr/bin/env python3
"""Classify a task for Codex Savings without selecting a model or executing work."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Dict, List, Optional, Sequence


RESEARCH_PATTERNS = (
    r"\bresearch\b",
    r"\bliterature\b",
    r"\bcitations?\b",
    r"\bsources?\b",
    r"\bcompare\b",
    r"\bbenchmark\b",
    r"\bcurrent(?:ly)?\b",
    r"\blatest\b",
    r"\blook\s+up\b",
    r"\binvestigat(?:e|ion)\b",
    r"\bverify\b.*\b(?:claim|source|fact)\b",
)

CODING_PATTERNS = (
    r"\b(?:implement|fix|debug|refactor|rewrite|edit|modify|build|add)\b",
    r"\b(?:code|repo(?:sitory)?|file|function|class|module|test|bug|patch)\b",
    r"\b(?:compile|lint|run|execute)\b.*\b(?:test|build|suite|command)\b",
    r"(?:\.py|\.js|\.ts|\.tsx|\.go|\.rs|\.java|\.rb|\.sh)\b",
)

COMPLEXITY_PATTERNS = (
    r"\barchitect(?:ure|ural)?\b",
    r"\bmigrat(?:e|ion)\b",
    r"\bsecurity\b",
    r"\bproduction\b",
    r"\bintermittent\b",
    r"\bambiguous\b",
    r"\bcross[- ]file\b",
    r"\bliterature\s+review\b",
    r"\bsystematic\s+review\b",
    r"\bhigh[- ]impact\b",
)

NARROW_PATTERNS = (
    r"\bfix\s+(?:a\s+)?typo\b",
    r"\brename\s+(?:a\s+)?(?:variable|function|file|skill)\b",
    r"\bformat\s+(?:a\s+)?(?:file|document)\b",
    r"\bone[- ]line\b",
    r"\bsingle[- ]file\b",
    r"\bupdate\s+(?:one|a single)\s+(?:line|field)\b",
)


def _hits(text: str, patterns: Sequence[str]) -> List[str]:
    return [pattern for pattern in patterns if re.search(pattern, text, re.IGNORECASE)]


def classify(prompt: str) -> Dict[str, object]:
    """Return an advisory route for a user prompt."""

    text = " ".join(prompt.split())
    if not text:
        raise ValueError("prompt must not be empty")

    research_hits = _hits(text, RESEARCH_PATTERNS)
    coding_hits = _hits(text, CODING_PATTERNS)
    complexity_hits = _hits(text, COMPLEXITY_PATTERNS)
    narrow_hits = _hits(text, NARROW_PATTERNS)

    explicit_mode = re.search(r"\bmode\s*[:=]\s*(coding|research|mixed)\b", text, re.I)
    if explicit_mode:
        mode = explicit_mode.group(1).lower()
    elif research_hits and coding_hits:
        mode = "mixed"
    elif research_hits:
        mode = "research"
    else:
        mode = "coding"

    if complexity_hits:
        complexity = "complex"
    elif narrow_hits and mode == "coding":
        complexity = "simple"
    else:
        complexity = "routine"

    if mode == "research":
        routing_hint = "needs_research_plan"
    elif mode == "mixed":
        routing_hint = "needs_research_plan"
    elif complexity == "simple":
        routing_hint = "direct_execution_allowed"
    else:
        routing_hint = "needs_coding_plan"

    reasons: List[str] = []
    if explicit_mode:
        reasons.append("explicit mode marker")
    if research_hits:
        reasons.append("research signals detected")
    if coding_hits:
        reasons.append("coding signals detected")
    if complexity_hits:
        reasons.append("complexity or risk signals detected")
    if narrow_hits:
        reasons.append("narrow-task signals detected")
    if not reasons:
        reasons.append("no specialized signals; coding is the compatible default")

    return {
        "advisory": True,
        "mode": mode,
        "complexity": complexity,
        "routing_hint": routing_hint,
        "reason": "; ".join(reasons),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="*", help="Task text; read stdin when omitted")
    args = parser.parse_args(argv)
    prompt = " ".join(args.prompt).strip()
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    if not prompt:
        parser.error("provide a prompt argument or pipe prompt text on stdin")

    print(json.dumps(classify(prompt), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
