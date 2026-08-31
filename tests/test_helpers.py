import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def packet(**overrides):
    value = {
        "protocol_version": "1.0",
        "cycle": 0,
        "mode": "coding",
        "goal": "Fix the targeted behavior.",
        "definition_of_done": "The focused regression test passes.",
        "scope": {"in_scope": ["src/example.py"], "out_of_scope": []},
        "constraints": ["Keep the public API unchanged."],
        "key_code_or_evidence": [],
        "attempted_work": [],
        "failures": [],
        "open_question_for_sol": "Which minimal implementation path should Luna use?",
    }
    value.update(overrides)
    return value


def write_packet(value):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle:
        json.dump(value, handle)
    return Path(handle.name)


class RoutingTests(unittest.TestCase):
    def test_research_prompt_routes_to_research_plan(self):
        result = run_script("route_task.py", "Research current API documentation and cite primary sources")
        self.assertEqual(result.returncode, 0, result.stderr)
        route = json.loads(result.stdout)
        self.assertEqual(route["mode"], "research")
        self.assertEqual(route["routing_hint"], "needs_research_plan")
        self.assertTrue(route["advisory"])

    def test_narrow_coding_prompt_can_skip_sol(self):
        result = run_script("route_task.py", "Fix a typo in README.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        route = json.loads(result.stdout)
        self.assertEqual(route["mode"], "coding")
        self.assertEqual(route["complexity"], "simple")
        self.assertEqual(route["routing_hint"], "direct_execution_allowed")

    def test_mixed_prompt_keeps_research_plan_first(self):
        result = run_script(
            "route_task.py",
            "Use current API documentation to implement the parser in src/parser.py",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        route = json.loads(result.stdout)
        self.assertEqual(route["mode"], "mixed")
        self.assertEqual(route["routing_hint"], "needs_research_plan")


class PacketValidationTests(unittest.TestCase):
    def test_valid_coding_packet(self):
        path = write_packet(packet())
        try:
            result = run_script("validate_packet.py", str(path), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["valid"])
        finally:
            path.unlink(missing_ok=True)

    def test_missing_open_question_is_rejected(self):
        value = packet()
        del value["open_question_for_sol"]
        path = write_packet(value)
        try:
            result = run_script("validate_packet.py", str(path), "--json")
            self.assertNotEqual(result.returncode, 0)
            errors = json.loads(result.stdout)["errors"]
            self.assertTrue(any("open_question_for_sol" in error for error in errors))
        finally:
            path.unlink(missing_ok=True)

    def test_forbidden_em_dash_is_rejected(self):
        path = write_packet(packet(goal="Reject this \u2014 character."))
        try:
            result = run_script("validate_packet.py", str(path), "--json")
            self.assertNotEqual(result.returncode, 0)
            errors = json.loads(result.stdout)["errors"]
            self.assertTrue(any("U+2014" in error for error in errors))
        finally:
            path.unlink(missing_ok=True)


class ResearchValidationTests(unittest.TestCase):
    def test_supported_claim_passes_final_validation(self):
        value = packet(
            mode="research",
            key_code_or_evidence=[
                {
                    "id": "E1",
                    "source_type": "web_page",
                    "summary": "The first-party reference states the behavior.",
                    "excerpt": "Short supporting passage.",
                }
            ],
            source_metadata=[
                {
                    "evidence_id": "E1",
                    "title": "First-party reference",
                    "url": "https://official.example/reference",
                    "publisher": "Official organization",
                    "publication_date": "2026-01-01",
                    "accessed_at": "2026-08-31",
                    "source_tier": "primary",
                    "quality_basis": "First-party documentation.",
                    "relevance": "high",
                }
            ],
            claims=[
                {
                    "id": "C1",
                    "text": "The behavior is supported.",
                    "status": "supported",
                    "confidence": "high",
                    "evidence_ids": ["E1"],
                }
            ],
            claim_evidence_map={"C1": ["E1"]},
            validation={
                "status": "pass",
                "checked_claim_ids": ["C1"],
                "unsupported_claim_ids": [],
                "notes": "Reviewed against the passage.",
            },
        )
        path = write_packet(value)
        try:
            result = run_script("validate_research.py", str(path), "--final", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertTrue(output["valid"])
            self.assertEqual(output["statement_support_rate"], 1.0)
        finally:
            path.unlink(missing_ok=True)

    def test_partial_claim_fails_require_supported(self):
        value = packet(
            mode="research",
            claims=[
                {
                    "id": "C1",
                    "text": "The behavior may be supported.",
                    "status": "partial",
                    "confidence": "medium",
                    "evidence_ids": [],
                }
            ],
            claim_evidence_map={"C1": []},
        )
        path = write_packet(value)
        try:
            result = run_script("validate_research.py", str(path), "--require-supported", "--json")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(result.stdout)["valid"])
        finally:
            path.unlink(missing_ok=True)


class SchemaTests(unittest.TestCase):
    def test_packet_schema_is_valid_json(self):
        schema_path = ROOT / "references" / "task-packet.schema.json"
        with schema_path.open(encoding="utf-8") as stream:
            schema = json.load(stream)
        self.assertEqual(schema["$id"], "https://codex-savings.local/schemas/task-packet-1.0.json")
        self.assertIn("claim_evidence_map", schema["properties"])


class DocumentationTests(unittest.TestCase):
    def test_readme_uses_npx_skills_installation(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("npx skills add ChloeVPin/codex-savings", readme)
        self.assertFalse(any(path.suffix == ".sh" for path in SCRIPTS.iterdir()))

    def test_output_punctuation_policy_is_propagated(self):
        paths = [
            ROOT / "SKILL.md",
            ROOT / "README.md",
            ROOT / "references" / "coding-mode-prompt.md",
            ROOT / "references" / "research-mode-prompt.md",
            ROOT / "references" / "loop-prompt.md",
            ROOT / "references" / "task-packet.md",
            ROOT / "references" / "task-packet.schema.json",
            ROOT / "references" / "evaluation.md",
        ]
        for path in paths:
            self.assertIn("U+2014", path.read_text(encoding="utf-8"), str(path))

        result = run_script("check_no_em_dashes.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_text_check_rejects_em_dash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.md"
            path.write_text("Forbidden \u2014 character.", encoding="utf-8")
            result = run_script("check_no_em_dashes.py", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("U+2014", result.stdout)


if __name__ == "__main__":
    unittest.main()
