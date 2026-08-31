#!/usr/bin/env python3
"""Check research claim/evidence consistency; semantic entailment still needs review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from validate_packet import validate_packet


SUPPORTED_STATUS = "supported"
NON_FINAL_STATUSES = {"partial", "unsupported", "contradicted", "unverified"}


def _is_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_research(
    packet: Any, require_supported: bool = False, final: bool = False
) -> Tuple[List[str], Dict[str, Any]]:
    """Return structural/consistency errors and derived research metrics."""

    packet_errors, approximate_tokens = validate_packet(packet)
    errors = list(packet_errors)
    metrics: Dict[str, Any] = {
        "approximate_tokens": approximate_tokens,
        "claim_count": 0,
        "supported_claims": 0,
        "statement_support_rate": None,
        "response_support": False,
    }
    if not isinstance(packet, dict):
        return errors, metrics

    if packet.get("mode") not in {"research", "mixed"}:
        errors.append("research validation requires mode research or mixed")

    evidence_items = packet.get("key_code_or_evidence", [])
    evidence_by_id = {
        item.get("id"): item
        for item in evidence_items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    metadata_items = packet.get("source_metadata", []) or []
    metadata_by_id = {
        item.get("evidence_id"): item
        for item in metadata_items
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }
    claims = packet.get("claims", []) or []
    claim_map = packet.get("claim_evidence_map", {}) or {}
    metrics["claim_count"] = len(claims)

    if final and not claims:
        errors.append("final research validation requires at least one claim")
    if claims and not isinstance(claim_map, dict):
        errors.append("claim_evidence_map is required when claims are present")

    unsupported_claim_ids: List[str] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        status = claim.get("status")
        claim_refs = set(claim.get("evidence_ids", []) or [])
        mapped_refs = set(claim_map.get(claim_id, []) or []) if isinstance(claim_map, dict) else set()

        if claim_id and claim_id not in claim_map:
            errors.append(f"claim {claim_id} is missing from claim_evidence_map")
        if claim_refs != mapped_refs:
            errors.append(f"claim {claim_id} evidence_ids do not match claim_evidence_map")
        if status == SUPPORTED_STATUS and not claim_refs:
            errors.append(f"supported claim {claim_id} has no evidence")
        if status in NON_FINAL_STATUSES:
            unsupported_claim_ids.append(claim_id or f"claim[{index}]")
            if require_supported or final:
                errors.append(f"claim {claim_id} is not final: status={status}")

        for evidence_id in claim_refs:
            evidence = evidence_by_id.get(evidence_id, {})
            metadata = metadata_by_id.get(evidence_id, {})
            source_type = evidence.get("source_type")
            url = evidence.get("url") or metadata.get("url")
            if source_type == "web_page" and not _is_url(url):
                errors.append(f"web evidence {evidence_id} needs an http(s) URL")

    supported_count = sum(
        1 for claim in claims if isinstance(claim, dict) and claim.get("status") == SUPPORTED_STATUS
    )
    metrics["supported_claims"] = supported_count
    if claims:
        metrics["statement_support_rate"] = round(supported_count / len(claims), 4)
    metrics["response_support"] = bool(claims) and supported_count == len(claims)

    validation = packet.get("validation")
    if isinstance(validation, dict):
        declared_unsupported = set(validation.get("unsupported_claim_ids", []) or [])
        actual_unsupported = set(unsupported_claim_ids)
        if declared_unsupported != actual_unsupported:
            errors.append("validation.unsupported_claim_ids does not match claim statuses")
        if final and validation.get("status") != "pass":
            errors.append("final research validation requires validation.status=pass")
    elif final:
        errors.append("final research validation requires a validation object")

    return errors, metrics


def _load_packet(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path, help="JSON packet to validate")
    parser.add_argument("--require-supported", action="store_true")
    parser.add_argument("--final", action="store_true", help="Apply final-answer gates")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    try:
        packet = _load_packet(args.packet)
    except (OSError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [str(exc)]}
        if args.as_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"invalid research packet: {exc}", file=sys.stderr)
        return 1

    errors, metrics = validate_research(
        packet, require_supported=args.require_supported, final=args.final
    )
    result = {"valid": not errors, "errors": errors, **metrics}
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif errors:
        print("invalid research packet", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
    else:
        rate = metrics["statement_support_rate"]
        print(f"valid research packet (statement_support_rate={rate})")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
