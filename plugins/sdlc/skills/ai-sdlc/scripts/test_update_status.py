#!/usr/bin/env python3
from __future__ import annotations

import errno
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("update_status.py")
spec = importlib.util.spec_from_file_location("update_status", SCRIPT)
update_status = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(update_status)


class UpdateStatusTests(unittest.TestCase):
    def test_specification_completion_advances_to_design(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status = update_status.default_status(Path(tmp) / ".features" / "demo")

            self.assertEqual(update_status.NEXT_PHASE["spec"], "design")
            self.assertEqual(status["phases"]["research"]["artifact"], "SPEC.md")

    def test_atomic_save_preserves_previous_status_when_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "feature"
            folder.mkdir()
            path = update_status.status_path(folder)
            path.write_text('{"previous": true}\n', encoding="utf-8")

            with patch.object(update_status.os, "replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    update_status.save_status(folder, {"new": True})

            self.assertEqual(path.read_text(encoding="utf-8"), '{"previous": true}\n')
            self.assertEqual(sorted(p.name for p in folder.iterdir()), ["status.json"])

    def test_windows_replace_retries_transient_native_errors(self) -> None:
        real_replace = os.replace
        for code in (5, 32, 33):
            with self.subTest(winerror=code), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                path = update_status.status_path(folder)
                previous = b'{"previous": true}\n'
                path.write_bytes(previous)
                error = PermissionError(errno.EACCES, "synthetic Windows sharing error")
                error.winerror = code
                attempts = []

                def replace(source, destination):
                    attempts.append((source, destination))
                    if len(attempts) <= 2:
                        self.assertEqual(path.read_bytes(), previous)
                        raise error
                    return real_replace(source, destination)

                with patch.object(update_status.os, "replace", side_effect=replace), patch.object(update_status.time, "sleep") as sleep:
                    update_status.save_status(folder, {"new": True})
                self.assertEqual(len(attempts), 3)
                self.assertTrue(all(pair == attempts[0] for pair in attempts))
                self.assertEqual(sleep.call_count, 2)
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"new": True})
                self.assertEqual(sorted(p.name for p in folder.iterdir()), ["status.json"])

    def test_persistent_windows_replace_error_is_bounded_and_preserves_status(self) -> None:
        for code in (5, 32, 33):
            with self.subTest(winerror=code), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                path = update_status.status_path(folder)
                previous = b'{"previous": true}\n'
                path.write_bytes(previous)
                error = PermissionError(errno.EACCES, "persistent synthetic Windows error")
                error.winerror = code
                with patch.object(update_status.os, "replace", side_effect=error) as replace, patch.object(update_status.time, "sleep") as sleep:
                    with self.assertRaises(PermissionError) as caught:
                        update_status.save_status(folder, {"new": True})
                self.assertIs(caught.exception, error)
                self.assertEqual(replace.call_count, 10)
                self.assertEqual(sleep.call_count, 9)
                self.assertTrue(all(call.args == (0.05,) for call in sleep.call_args_list))
                self.assertEqual(path.read_bytes(), previous)
                self.assertEqual(sorted(p.name for p in folder.iterdir()), ["status.json"])

    def test_unrelated_replace_errors_are_not_retried(self) -> None:
        plain_permission = PermissionError(errno.EACCES, "plain permission failure")
        other_native = OSError(errno.ENOENT, "synthetic missing file")
        other_native.winerror = 2
        for error in (plain_permission, other_native, OSError(errno.ENOSPC, "synthetic full disk")):
            with self.subTest(error=repr(error)), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                path = update_status.status_path(folder)
                previous = b'{"previous": true}\n'
                path.write_bytes(previous)
                with patch.object(update_status.os, "replace", side_effect=error) as replace, patch.object(update_status.time, "sleep") as sleep:
                    with self.assertRaises(OSError) as caught:
                        update_status.save_status(folder, {"new": True})
                self.assertIs(caught.exception, error)
                replace.assert_called_once()
                sleep.assert_not_called()
                self.assertEqual(path.read_bytes(), previous)
                self.assertEqual(sorted(p.name for p in folder.iterdir()), ["status.json"])

    @unittest.skipUnless(os.name == "nt", "Windows read-handle sharing semantics")
    def test_windows_status_save_recovers_after_reader_closes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = update_status.status_path(folder)
            path.write_text('{"previous": true}\n', encoding="utf-8")
            with path.open("rb") as reader, update_status.status_lock(folder):
                with patch.object(update_status.time, "sleep", side_effect=lambda delay: reader.close()) as sleep:
                    update_status.save_status(folder, {"new": True})
                sleep.assert_called_once_with(0.05)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"new": True})

    def test_concurrent_status_updates_preserve_each_history_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "feature"
            commands = [
                [sys.executable, str(SCRIPT), "start-phase", str(folder), "spec", "--summary", str(index)]
                for index in range(8)
            ]

            def run(command: list[str]) -> subprocess.CompletedProcess[str]:
                return subprocess.run(command, capture_output=True, text=True, check=False, timeout=20)

            with ThreadPoolExecutor(max_workers=len(commands)) as executor:
                results = list(executor.map(run, commands))

            self.assertTrue(all(result.returncode == 0 for result in results), [result.stderr for result in results])
            status = json.loads(update_status.status_path(folder).read_text(encoding="utf-8"))
            self.assertEqual(len(status["history"]), 9)
            self.assertEqual(len([entry for entry in status["history"] if entry.get("summary", "").isdigit()]), 8)


if __name__ == "__main__":
    unittest.main()
