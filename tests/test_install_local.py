from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install-local"
PLUGIN_ID = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))["id"]


class InstallLocalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plugins = self.root / "config" / "plugins"
        self.shell_json = self.root / "config" / "shell.json"

    def run_installer(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--plugins-dir", str(self.plugins), "--shell-json", str(self.shell_json), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_config(self, config: dict) -> None:
        self.shell_json.parent.mkdir(parents=True, exist_ok=True)
        self.shell_json.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_preview_has_no_side_effects(self) -> None:
        self.write_config({"version": 1, "bar": {"layout": {"right": []}}, "custom": {"keep": True}})
        before = self.shell_json.read_bytes()
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.plugins.exists())
        self.assertEqual(self.shell_json.read_bytes(), before)

    def test_apply_backs_up_and_preserves_existing_config(self) -> None:
        config = {
            "version": 1,
            "idle": {"lock": 300},
            "bar": {"position": "top", "layout": {"left": [{"id": "example.keep"}], "right": []}},
            "plugins": [{"id": "example.service", "settings": {"x": 1}}],
        }
        self.write_config(config)
        original = self.shell_json.read_bytes()
        result = self.run_installer("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        link = self.plugins / PLUGIN_ID
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), ROOT)
        updated = json.loads(self.shell_json.read_text(encoding="utf-8"))
        self.assertEqual(updated["idle"], config["idle"])
        self.assertEqual(updated["bar"]["position"], "top")
        self.assertEqual(updated["bar"]["layout"]["left"], config["bar"]["layout"]["left"])
        self.assertEqual(updated["plugins"], config["plugins"])
        self.assertEqual(updated["bar"]["layout"]["right"], [{"id": PLUGIN_ID}])
        self.assertEqual((self.shell_json.with_name("shell.json.bak")).read_bytes(), original)

    def test_repeat_apply_is_idempotent_and_preserves_custom_widget_settings(self) -> None:
        self.write_config({"bar": {"layout": {"right": [{"id": PLUGIN_ID, "settings": {"folder": "Ideas"}}]}}})
        for _ in range(2):
            result = self.run_installer("--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
        updated = json.loads(self.shell_json.read_text(encoding="utf-8"))
        self.assertEqual(updated["bar"]["layout"]["right"], [{"id": PLUGIN_ID, "settings": {"folder": "Ideas"}}])
        self.assertEqual(len(list(self.shell_json.parent.glob("shell.json.bak*"))), 0)

    def test_refuses_unrelated_plugin_path(self) -> None:
        collision = self.plugins / PLUGIN_ID
        collision.mkdir(parents=True)
        marker = collision / "keep"
        marker.write_text("untouched", encoding="utf-8")
        result = self.run_installer("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(marker.read_text(encoding="utf-8"), "untouched")

    def test_missing_shell_config_does_not_create_partial_config(self) -> None:
        result = self.run_installer("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.plugins / PLUGIN_ID).is_symlink())
        self.assertFalse(self.shell_json.exists())


if __name__ == "__main__":
    unittest.main()
