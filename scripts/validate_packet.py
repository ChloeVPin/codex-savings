#!/usr/bin/env python3
"""Validate a Codex Savings packet using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


MAX_PACKET_TOKENS = 3000
MODES = {"coding", "research", "mixed"}
ROUTING_HINTS = {
    "direct_execution_allowed",
    "needs_coding_plan",
    "needs_research_plan",
    "needs_validation",
    "resolve_contradiction",
    "escalate_to_sol",
    "stop",
}
CLAIM_STATUSES = {"supported", "partial", "unsupported", "contradicted", "unverified"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
EVIDENCE_TYPES = {"web_page", "file", "command_result", "test_result", "other"}
SOURCE_TIERS = {"primary", "secondary", "tertiary", "firsthand", "unknown"}
FORBIDDEN_OUTPUT_CHARS = {"\u2014": "U+2014"}

REQUIRED_FIELDS = (
    "protocol_version",
    "cycle",
    "mode",
    "goal",
    "definition_of_done",
    "scope",
    "constraints",
    "key_code_or_evidence",
    "attempted_work",
    "failures",
    "open_question_for_sol",
)
OPTIONAL_FIELDS = {
    "source_metadata",
    "subquestions",
    "queries",
    "claims",
    "claim_evidence_map",
    "uncertainty_log",
    "contradictions",
    "routing_hint",
    "routing_reason",
    "plan_history",
    "validation",
    "state_digest",
}
PACKET_FIELDS = set(REQUIRED_FIELDS) | OPTIONAL_FIELDS


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_object(value: Any, label: str, errors: List[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    return True


def _require_list(value: Any, label: str, errors: List[str]) -> bool:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return False
    return True


def _validate_id(value: Any, prefix: str, label: str, errors: List[str]) -> bool:
    if not isinstance(value, str) or not re.fullmatch(rf"{re.escape(prefix)}[1-9][0-9]*", value):
        errors.append(f"{label} must match {prefix}1, {prefix}2, ...")
        return False
    return True


def _unique_ids(items: Iterable[Any], prefix: str, label: str, errors: List[str]) -> Set[str]:
    identifiers: Set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        identifier = item.get("id")
        if not _validate_id(identifier, prefix, f"{label}[{index}].id", errors):
            continue
        if identifier in identifiers:
            errors.append(f"duplicate {label} id: {identifier}")
        identifiers.add(identifier)
    return identifiers


def _validate_evidence_refs(
    value: Any, label: str, evidence_ids: set[str], errors: List[str]
) -> None:
    if not _require_list(value, label, errors):
        return
    for index, evidence_id in enumerate(value):
        if not _validate_id(evidence_id, "E", f"{label}[{index}]", errors):
            continue
        if evidence_id not in evidence_ids:
            errors.append(f"{label}[{index}] references unknown evidence id {evidence_id}")


def _validate_string_array(value: Any, label: str, errors: List[str]) -> None:
    if not _require_list(value, label, errors):
        return
    for index, item in enumerate(value):
        if not _nonempty(item):
            errors.append(f"{label}[{index}] must be a non-empty string")


def _find_forbidden_output_chars(value: Any, path: str = "packet") -> List[str]:
    findings: List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(_find_forbidden_output_chars(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find_forbidden_output_chars(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for character, label in FORBIDDEN_OUTPUT_CHARS.items():
            if character in value:
                findings.append(f"{path} contains forbidden {label}")
    return findings


def validate_packet(packet: Any, max_tokens: int = MAX_PACKET_TOKENS) -> Tuple[List[str], int]:
    """Return validation errors and a rough JSON token estimate."""

    if isinstance(packet, dict):
        serialized = json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
        approximate_tokens = max(1, math.ceil(len(serialized) / 4))
    else:
        approximate_tokens = 0

    errors: List[str] = []
    if not isinstance(packet, dict):
        return ["packet must be a JSON object"], approximate_tokens

    errors.extend(_find_forbidden_output_chars(packet))

    unknown_fields = set(packet) - PACKET_FIELDS
    for field in sorted(unknown_fields):
        errors.append(f"unsupported packet field: {field}")

    for field in REQUIRED_FIELDS:
        if field not in packet:
            errors.append(f"missing required field: {field}")

    if packet.get("protocol_version") != "1.0":
        errors.append("protocol_version must be \"1.0\"")
    if not isinstance(packet.get("cycle"), int) or isinstance(packet.get("cycle"), bool) or packet.get("cycle", -1) < 0:
        errors.append("cycle must be a non-negative integer")
    if packet.get("mode") not in MODES:
        errors.append("mode must be coding, research, or mixed")
    for field in ("goal", "definition_of_done", "open_question_for_sol"):
        if not _nonempty(packet.get(field)):
            errors.append(f"{field} must be a non-empty string")

    scope = packet.get("scope")
    if _require_object(scope, "scope", errors):
        for field in ("in_scope", "out_of_scope"):
            if field not in scope:
                errors.append(f"scope.{field} is required")
            else:
                _validate_string_array(scope[field], f"scope.{field}", errors)
        if "time_boundary" in scope and not isinstance(scope["time_boundary"], str):
            errors.append("scope.time_boundary must be a string")

    _validate_string_array(packet.get("constraints"), "constraints", errors)

    evidence = packet.get("key_code_or_evidence")
    evidence_ids: Set[str] = set()
    if _require_list(evidence, "key_code_or_evidence", errors):
        evidence_ids = _unique_ids(evidence, "E", "key_code_or_evidence", errors)
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                continue
            if item.get("source_type") not in EVIDENCE_TYPES:
                errors.append(f"key_code_or_evidence[{index}].source_type is invalid")
            if not _nonempty(item.get("summary")):
                errors.append(f"key_code_or_evidence[{index}].summary must be non-empty")
            for optional in ("excerpt", "path", "url"):
                if optional in item and not isinstance(item[optional], str):
                    errors.append(f"key_code_or_evidence[{index}].{optional} must be a string")

    attempts = packet.get("attempted_work")
    if _require_list(attempts, "attempted_work", errors):
        _unique_ids(attempts, "A", "attempted_work", errors)
        for index, item in enumerate(attempts):
            if not isinstance(item, dict):
                continue
            if item.get("actor") not in {"luna", "sol", "user", "host"}:
                errors.append(f"attempted_work[{index}].actor is invalid")
            for field in ("action", "result"):
                if not _nonempty(item.get(field)):
                    errors.append(f"attempted_work[{index}].{field} must be non-empty")
            if "evidence_ids" in item:
                _validate_evidence_refs(item["evidence_ids"], f"attempted_work[{index}].evidence_ids", evidence_ids, errors)

    failures = packet.get("failures")
    if _require_list(failures, "failures", errors):
        _unique_ids(failures, "F", "failures", errors)
        for index, item in enumerate(failures):
            if not isinstance(item, dict):
                continue
            if not _nonempty(item.get("summary")):
                errors.append(f"failures[{index}].summary must be non-empty")
            if not isinstance(item.get("recoverable"), bool):
                errors.append(f"failures[{index}].recoverable must be boolean")

    if "routing_hint" in packet and packet["routing_hint"] not in ROUTING_HINTS:
        errors.append("routing_hint is invalid")
    if "routing_reason" in packet and not isinstance(packet["routing_reason"], str):
        errors.append("routing_reason must be a string")

    source_metadata = packet.get("source_metadata")
    metadata_ids: Set[str] = set()
    if source_metadata is not None and _require_list(source_metadata, "source_metadata", errors):
        for index, item in enumerate(source_metadata):
            if not isinstance(item, dict):
                continue
            evidence_id = item.get("evidence_id")
            if not _validate_id(evidence_id, "E", f"source_metadata[{index}].evidence_id", errors):
                continue
            if evidence_id in metadata_ids:
                errors.append(f"duplicate source_metadata evidence_id: {evidence_id}")
            metadata_ids.add(evidence_id)
            if evidence_id not in evidence_ids:
                errors.append(f"source_metadata[{index}] references unknown evidence id {evidence_id}")
            for field in ("title", "quality_basis"):
                if not _nonempty(item.get(field)):
                    errors.append(f"source_metadata[{index}].{field} must be non-empty")
            if item.get("source_tier") not in SOURCE_TIERS:
                errors.append(f"source_metadata[{index}].source_tier is invalid")
            if item.get("relevance") not in {"high", "medium", "low"}:
                errors.append(f"source_metadata[{index}].relevance is invalid")
            for field in ("url", "publisher", "publication_date", "accessed_at"):
                if field in item and not isinstance(item[field], str):
                    errors.append(f"source_metadata[{index}].{field} must be a string")

    subquestions = packet.get("subquestions")
    subquestion_ids: Set[str] = set()
    if subquestions is not None and _require_list(subquestions, "subquestions", errors):
        subquestion_ids = _unique_ids(subquestions, "Q", "subquestions", errors)
        for index, item in enumerate(subquestions):
            if not isinstance(item, dict):
                continue
            if not _nonempty(item.get("question")):
                errors.append(f"subquestions[{index}].question must be non-empty")
            if item.get("status") not in {"open", "answered", "blocked"}:
                errors.append(f"subquestions[{index}].status is invalid")

    queries = packet.get("queries")
    query_ids: Set[str] = set()
    if queries is not None and _require_list(queries, "queries", errors):
        query_ids = _unique_ids(queries, "R", "queries", errors)
        for index, item in enumerate(queries):
            if not isinstance(item, dict):
                continue
            subquestion_id = item.get("subquestion_id")
            if not _validate_id(subquestion_id, "Q", f"queries[{index}].subquestion_id", errors):
                continue
            if subquestion_ids and subquestion_id not in subquestion_ids:
                errors.append(f"queries[{index}] references unknown subquestion id {subquestion_id}")
            if not _nonempty(item.get("query")):
                errors.append(f"queries[{index}].query must be non-empty")
            if item.get("status") not in {"planned", "executed", "discarded"}:
                errors.append(f"queries[{index}].status is invalid")

    claims = packet.get("claims")
    claim_ids: Set[str] = set()
    if claims is not None and _require_list(claims, "claims", errors):
        claim_ids = _unique_ids(claims, "C", "claims", errors)
        for index, item in enumerate(claims):
            if not isinstance(item, dict):
                continue
            if not _nonempty(item.get("text")):
                errors.append(f"claims[{index}].text must be non-empty")
            if item.get("status") not in CLAIM_STATUSES:
                errors.append(f"claims[{index}].status is invalid")
            if item.get("confidence") not in CONFIDENCE_LEVELS:
                errors.append(f"claims[{index}].confidence is invalid")
            _validate_evidence_refs(item.get("evidence_ids"), f"claims[{index}].evidence_ids", evidence_ids, errors)
            if "uncertainty" in item and not isinstance(item["uncertainty"], str):
                errors.append(f"claims[{index}].uncertainty must be a string")

    claim_map = packet.get("claim_evidence_map")
    if claim_map is not None and _require_object(claim_map, "claim_evidence_map", errors):
        for claim_id, references in claim_map.items():
            if not _validate_id(claim_id, "C", f"claim_evidence_map key {claim_id}", errors):
                continue
            if claim_ids and claim_id not in claim_ids:
                errors.append(f"claim_evidence_map references unknown claim id {claim_id}")
            _validate_evidence_refs(references, f"claim_evidence_map[{claim_id}]", evidence_ids, errors)
        if claims is not None:
            missing_claim_map = claim_ids - set(claim_map)
            for claim_id in sorted(missing_claim_map):
                errors.append(f"claim {claim_id} is missing from claim_evidence_map")

    uncertainty = packet.get("uncertainty_log")
    uncertainty_ids: Set[str] = set()
    if uncertainty is not None and _require_list(uncertainty, "uncertainty_log", errors):
        uncertainty_ids = _unique_ids(uncertainty, "U", "uncertainty_log", errors)
        known_subject_ids = evidence_ids | claim_ids | subquestion_ids
        for index, item in enumerate(uncertainty):
            if not isinstance(item, dict):
                continue
            subject_id = item.get("subject_id")
            if not isinstance(subject_id, str) or not subject_id:
                errors.append(f"uncertainty_log[{index}].subject_id must be non-empty")
            elif known_subject_ids and subject_id not in known_subject_ids:
                errors.append(f"uncertainty_log[{index}] references unknown subject id {subject_id}")
            if item.get("level") not in CONFIDENCE_LEVELS:
                errors.append(f"uncertainty_log[{index}].level is invalid")
            if not _nonempty(item.get("reason")):
                errors.append(f"uncertainty_log[{index}].reason must be non-empty")
            if not isinstance(item.get("cycle"), int) or isinstance(item.get("cycle"), bool) or item.get("cycle", -1) < 0:
                errors.append(f"uncertainty_log[{index}].cycle must be a non-negative integer")

    contradictions = packet.get("contradictions")
    contradiction_ids: Set[str] = set()
    if contradictions is not None and _require_list(contradictions, "contradictions", errors):
        contradiction_ids = _unique_ids(contradictions, "X", "contradictions", errors)
        for index, item in enumerate(contradictions):
            if not isinstance(item, dict):
                continue
            claim_id = item.get("claim_id")
            if not _validate_id(claim_id, "C", f"contradictions[{index}].claim_id", errors):
                continue
            if claim_ids and claim_id not in claim_ids:
                errors.append(f"contradictions[{index}] references unknown claim id {claim_id}")
            _validate_evidence_refs(item.get("evidence_ids"), f"contradictions[{index}].evidence_ids", evidence_ids, errors)
            if not _nonempty(item.get("summary")):
                errors.append(f"contradictions[{index}].summary must be non-empty")
            if item.get("status") not in {"open", "resolved"}:
                errors.append(f"contradictions[{index}].status is invalid")

    plan_history = packet.get("plan_history")
    if plan_history is not None and _require_list(plan_history, "plan_history", errors):
        for index, item in enumerate(plan_history):
            if not isinstance(item, dict):
                continue
            if not isinstance(item.get("cycle"), int) or isinstance(item.get("cycle"), bool) or item.get("cycle", -1) < 0:
                errors.append(f"plan_history[{index}].cycle must be a non-negative integer")
            for field in ("summary", "outcome"):
                if not _nonempty(item.get(field)):
                    errors.append(f"plan_history[{index}].{field} must be non-empty")
            if not isinstance(item.get("changed"), bool):
                errors.append(f"plan_history[{index}].changed must be boolean")

    validation = packet.get("validation")
    if validation is not None and _require_object(validation, "validation", errors):
        if validation.get("status") not in {"not_run", "needs_review", "pass", "fail"}:
            errors.append("validation.status is invalid")
        for field in ("checked_claim_ids", "unsupported_claim_ids"):
            if field in validation:
                values = validation[field]
                if _require_list(values, f"validation.{field}", errors):
                    for index, claim_id in enumerate(values):
                        if not _validate_id(claim_id, "C", f"validation.{field}[{index}]", errors):
                            continue
                        if claim_ids and claim_id not in claim_ids:
                            errors.append(f"validation.{field}[{index}] references unknown claim id {claim_id}")
        if "notes" in validation and not isinstance(validation["notes"], str):
            errors.append("validation.notes must be a string")

    if "state_digest" in packet and not isinstance(packet["state_digest"], str):
        errors.append("state_digest must be a string")

    if max_tokens <= 0:
        errors.append("max_tokens must be positive")
    elif approximate_tokens > max_tokens:
        errors.append(
            f"packet exceeds approximate token budget: {approximate_tokens} > {max_tokens}"
        )

    return errors, approximate_tokens


def _load_packet(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path, help="JSON packet to validate")
    parser.add_argument("--max-tokens", type=int, default=MAX_PACKET_TOKENS)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    try:
        packet = _load_packet(args.packet)
    except (OSError, json.JSONDecodeError) as exc:
        result = {"valid": False, "approximate_tokens": 0, "errors": [str(exc)]}
        if args.as_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"invalid packet: {exc}", file=sys.stderr)
        return 1

    errors, approximate_tokens = validate_packet(packet, args.max_tokens)
    result = {
        "valid": not errors,
        "approximate_tokens": approximate_tokens,
        "errors": errors,
    }
    if args.as_json:
        print(json.dumps(result, indent=2))
    elif errors:
        print(f"invalid packet (approximate_tokens={approximate_tokens})", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    else:
        print(f"valid packet (approximate_tokens={approximate_tokens})")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
