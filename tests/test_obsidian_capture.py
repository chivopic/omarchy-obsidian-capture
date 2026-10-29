from __future__ import annotations

import concurrent.futures
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "obsidian-capture"
LOADER = importlib.machinery.SourceFileLoader("obsidian_capture", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
capture = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(capture)


class CreateNoteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / "My Vault"
        self.vault.mkdir()
        self.moment = datetime(2026, 10, 29, 14, 32, tzinfo=timezone.utc)

    def test_note_preserves_body_and_escapes_yaml_title(self) -> None:
        source = '  # A: "quoted" idea  \n\nline one\n  indented line\n'
        result = capture.create_note(source, str(self.vault), now=self.moment)

        self.assertEqual(result.parent, self.vault / "Inbox")
        self.assertEqual(result.name, "2026-10-29 1432 A-quoted-idea.md")
        self.assertIn('title: "A: \\\"quoted\\\" idea"\n', result.read_text(encoding="utf-8"))
        self.assertTrue(result.read_text(encoding="utf-8").endswith(f"# A: \"quoted\" idea\n\n{source}"))

    def test_adds_newline_when_body_has_none(self) -> None:
        result = capture.create_note("idea", str(self.vault), now=self.moment)
        self.assertTrue(result.read_bytes().endswith(b"idea\n"))

    def test_filename_stays_within_filesystem_byte_limit_for_long_unicode_titles(self) -> None:
        # Supplementary CJK characters occupy four UTF-8 bytes each.
        title = "𠀀" * 120
        first = capture.create_note(title, str(self.vault), now=self.moment)
        second = capture.create_note(title, str(self.vault), now=self.moment)
        self.assertLessEqual(len(first.name.encode("utf-8")), 255)
        self.assertLessEqual(len(second.name.encode("utf-8")), 255)
        self.assertTrue(second.name.endswith(" (2).md"))

    def test_existing_notes_are_never_overwritten(self) -> None:
        first = capture.create_note("same", str(self.vault), now=self.moment)
        original = first.read_bytes()
        second = capture.create_note("same", str(self.vault), now=self.moment)
        self.assertEqual(second.name, "2026-10-29 1432 same (2).md")
        self.assertEqual(first.read_bytes(), original)

    def test_rejects_empty_content_and_invalid_vault(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能为空"):
            capture.create_note(" \n", str(self.vault), now=self.moment)
        with self.assertRaisesRegex(ValueError, "不存在"):
            capture.create_note("idea", str(self.root / "missing"), now=self.moment)

    def test_rejects_parent_and_symlink_escape(self) -> None:
        with self.assertRaisesRegex(ValueError, "相对路径"):
            capture.create_note("idea", str(self.vault), "../outside", now=self.moment)
        outside = self.root / "outside"
        outside.mkdir()
        (self.vault / "escape").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "库之外"):
            capture.create_note("idea", str(self.vault), "escape/child", now=self.moment)
        self.assertEqual(list(outside.iterdir()), [])


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.vault = Path(self.temp.name) / "vault"
        self.vault.mkdir()

    def run_cli(self, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_json_capture_contract(self) -> None:
        result = self.run_cli("--capture", "from cli", "--vault", str(self.vault), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(Path(payload["path"]).read_text(encoding="utf-8").splitlines()[-1], "from cli")

    def test_json_failure_contract_and_stdin(self) -> None:
        failed = self.run_cli("--capture", "idea", "--vault", str(self.vault / "missing"), "--json")
        self.assertEqual(failed.returncode, 1)
        failure_payload = json.loads(failed.stdout)
        self.assertFalse(failure_payload["ok"])
        self.assertIn("不存在", failure_payload["error"])

        saved = self.run_cli("--stdin", "--vault", str(self.vault), "--folder", "Clips", "--json", input_text="from stdin")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        self.assertTrue(Path(json.loads(saved.stdout)["path"]).is_file())

    def test_stdin_json_reads_one_line_and_decodes_multiline_text(self) -> None:
        text = 'first line\n\n  indented "quote"\n'
        process = subprocess.Popen(
            [sys.executable, str(SCRIPT), "--stdin-json", "--vault", str(self.vault), "--json"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdin is not None
        process.stdin.write(json.dumps(text, ensure_ascii=False) + "\n")
        process.stdin.flush()
        try:
            code = process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            self.fail("--stdin-json waited for EOF after receiving its newline frame")
        process.stdin.close()
        assert process.stdout is not None and process.stderr is not None
        stdout, stderr = process.stdout.read(), process.stderr.read()
        process.stdout.close()
        process.stderr.close()
        self.assertEqual(code, 0, stderr)
        note = Path(json.loads(stdout)["path"]).read_text(encoding="utf-8")
        self.assertTrue(note.endswith(f"# first line\n\n{text}"))

    def test_stdin_json_rejects_non_string_frame(self) -> None:
        result = self.run_cli("--stdin-json", "--vault", str(self.vault), "--json", input_text='{"text":"idea"}\n')
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("JSON 字符串", payload["error"])

    def test_concurrent_writers_get_distinct_files(self) -> None:
        def save(_: int) -> str:
            result = self.run_cli("--capture", "simultaneous", "--vault", str(self.vault), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)["path"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            paths = list(pool.map(save, range(8)))
        self.assertEqual(len(set(paths)), 8)
        self.assertEqual(len(list((self.vault / "Inbox").glob("*.md"))), 8)
        self.assertEqual({Path(path).read_text(encoding="utf-8").count("# simultaneous") for path in paths}, {1})


if __name__ == "__main__":
    unittest.main()
