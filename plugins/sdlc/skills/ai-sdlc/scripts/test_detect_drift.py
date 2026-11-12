#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("detect_drift.py")
spec = importlib.util.spec_from_file_location("detect_drift", SCRIPT)
detect_drift = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(detect_drift)


class DetectDriftTests(unittest.TestCase):
    def test_missing_living_documents_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / ".features" / "demo"
            feature.mkdir(parents=True)
            (feature / "SPEC.md").write_text("# Demo\n", encoding="utf-8")

            result = detect_drift.detect(feature)

            self.assertEqual(result["overall"], "yellow")
            self.assertEqual(result["nextRecommendedPhase"], "plan")
            self.assertTrue(any(item["artifact"] == "tasks/PLAN.md" for item in result["items"]))

    def test_missing_design_artifact_is_reported_when_the_spec_references_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / ".features" / "demo"
            feature.mkdir(parents=True)
            (feature / "SPEC.md").write_text("# Demo\n\n## Design\n\nSee [the design](DESIGN.md).\n", encoding="utf-8")

            result = detect_drift.detect(feature)

            design_items = [item for item in result["items"] if item.get("artifact") == "DESIGN.md"]
            self.assertEqual(len(design_items), 1)
            self.assertEqual(design_items[0]["route"], "design")

    def test_design_artifact_is_optional_but_hashed_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / ".features" / "demo"
            (feature / "tasks").mkdir(parents=True)
            (feature / "SPEC.md").write_text("# Demo\n\n## Design\n\nSee DESIGN.md.\n", encoding="utf-8")
            (feature / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
            (feature / "tasks" / "PLAN.md").write_text("# Plan\n", encoding="utf-8")
            (feature / "tasks" / "TODO.md").write_text("# Todo\n", encoding="utf-8")

            result = detect_drift.detect(feature)

            self.assertEqual(result["overall"], "green")
            self.assertIsNotNone(result["artifacts"]["DESIGN.md"])

    def test_scope_drift_is_red_when_changed_file_is_outside_expected_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
            feature = root / ".features" / "demo"
            (feature / "tasks").mkdir(parents=True)
            (feature / "tasks" / "PLAN.md").write_text("## Expected File Scope\n\n- `src/auth/**`\n", encoding="utf-8")
            (feature / "SPEC.md").write_text("# Demo\n", encoding="utf-8")
            (feature / "tasks" / "TODO.md").write_text("# Todo\n", encoding="utf-8")
            (root / "README.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "chore: base"], cwd=root, check=True, capture_output=True)
            (root / "src" / "billing").mkdir(parents=True)
            (root / "src" / "billing" / "invoice.txt").write_text("oops\n", encoding="utf-8")

            result = detect_drift.detect(feature)

            self.assertEqual(result["overall"], "red")
            self.assertEqual(result["nextRecommendedPhase"], "refine")
            scope_items = [item for item in result["items"] if item["type"] == "scope-drift"]
            self.assertEqual(len(scope_items), 1)
            self.assertIn("src/billing/invoice.txt", scope_items[0]["details"]["outsideScopeFiles"])

    def test_update_status_writes_drift_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / ".features" / "demo"
            feature.mkdir(parents=True)
            status_path = feature / "status.json"
            status_path.write_text(json.dumps({"schemaVersion": 1, "git": {}}), encoding="utf-8")
            result = {"overall": "green", "checkedAt": "2026-07-11T00:00:00Z", "nextRecommendedPhase": None, "items": [], "summary": {"total": 0}}

            detect_drift.update_status(feature, result)

            status = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(status["drift"]["overall"], "green")
            self.assertEqual(status["drift"]["summary"]["total"], 0)

    def test_update_status_creates_full_status_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / ".features" / "demo"
            feature.mkdir(parents=True)
            result = {"overall": "yellow", "checkedAt": "2026-07-11T00:00:00Z", "nextRecommendedPhase": "review", "items": [], "summary": {"total": 0}}

            detect_drift.update_status(feature, result)

            status = json.loads((feature / "status.json").read_text(encoding="utf-8"))
            self.assertIn("phases", status)
            self.assertEqual(status["drift"]["overall"], "yellow")
            self.assertEqual(status["nextRecommendedPhase"], "review")


if __name__ == "__main__":
    unittest.main()
