#!/usr/bin/env python3
"""Exercise the real widget and writer with a temporary vault on Wayland."""
import os
from pathlib import Path
import subprocess
import tempfile

project = Path(__file__).resolve().parents[1]
shell = Path('/usr/share/omarchy/shell')
if not (shell / 'Ui' / 'KeyboardPanel.qml').exists():
    raise SystemExit('Omarchy shell UI kit is required for this check')

with tempfile.TemporaryDirectory(prefix='obsidian-capture-qml-') as tmp:
    base = Path(tmp)
    config = base / 'shell'
    config.mkdir()
    vault = base / 'vault'
    vault.mkdir()
    (config / 'shell.qml').write_text((project / 'tests/qml-smoke.qml').read_text())
    for name in ('Commons', 'Ui'):
        (config / name).symlink_to(shell / name, target_is_directory=True)
    env = {**os.environ, 'CAPTURE_PROJECT': project.as_uri(), 'CAPTURE_VAULT': str(vault),
           'QT_QPA_PLATFORM': 'wayland', 'QT_QUICK_BACKEND': 'software'}
    if not env.get('WAYLAND_DISPLAY'):
        sockets = [p for p in Path(env.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')).glob('wayland-*') if p.is_socket()]
        if len(sockets) != 1:
            raise SystemExit('Set WAYLAND_DISPLAY to run the QML capture check')
        env['WAYLAND_DISPLAY'] = sockets[0].name
    result = subprocess.run(['quickshell', '-p', str(config), '--no-color'], env=env,
                            capture_output=True, text=True, timeout=12)
    output = result.stdout + result.stderr
    print(output)
    if result.returncode or 'CAPTURE_QML_PASSED' not in output or 'CAPTURE_QML_FAILED' in output:
        raise SystemExit('QML capture check failed')
    notes = list((vault / 'Inbox').glob('*.md'))
    if len(notes) != 1 or 'First line\nOriginal body' not in notes[0].read_text():
        raise SystemExit('QML capture did not save the submitted text')
    print('QML capture wrote the submitted text and preserved the newer draft.')
