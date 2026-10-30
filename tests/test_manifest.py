"""Check the published plugin's entry points and settings remain usable."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def test_widget_entry_point_and_settings(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['id'], 'io.github.chivopic.obsidian-capture')
        self.assertIn('bar-widget', manifest['kinds'])
        self.assertTrue((ROOT / manifest['entryPoints']['barWidget']).is_file())
        widget = manifest['barWidget']
        schema = {entry['key']: entry for entry in widget['schema']}
        for key in ('vaultPath', 'folder'):
            self.assertEqual(schema[key]['type'], 'string')
            self.assertEqual(schema[key]['defaultValue'], widget['defaults'][key])
        self.assertTrue((ROOT / 'scripts' / 'obsidian-capture').is_file())


if __name__ == '__main__':
    unittest.main()
