import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release', 'scripts/release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def fixture(self, root, version='2.3.4'):
        for name in ('mixin/obscura-mixin.yaml', 'standalone/obscura.yaml'):
            file = root / name
            file.parent.mkdir(parents=True)
            file.write_text(f'version: "{version}"\n')
        (root / 'package.json').write_text(json.dumps({'version': version}))
        (root / 'package-lock.json').write_text(json.dumps(
            {'version': version, 'packages': {'': {'version': version}}}))

    def test_workflow_initializes_private_authfile_before_login(self):
        # Execute the actual setup shell, stopping where real registry login begins.
        workflow = Path('.github/workflows/release.yml').read_text()
        setup = workflow.split('          authfile=$(mktemp)\n', 1)[1]
        setup = setup.split("          printf '%s' \"$GHCR_TOKEN\"", 1)[0]
        script = 'set -euo pipefail\nauthfile=$(mktemp)\n' + setup
        with tempfile.TemporaryDirectory() as tmp:
            authfile = Path(tmp) / 'auth.json'
            bindir = Path(tmp) / 'bin'
            bindir.mkdir()
            mktemp = bindir / 'mktemp'
            mktemp.write_text('#!/bin/sh\n(umask 077; : > "$TEST_AUTHFILE")\nprintf "%s\\n" "$TEST_AUTHFILE"\n')
            mktemp.chmod(0o700)
            probe = ("python3 -c 'import json,os,stat,sys; "
                     'p=sys.argv[1]; assert json.load(open(p)) == {}; '
                     "assert stat.S_IMODE(os.stat(p).st_mode) == 0o600' \"$authfile\"\n")
            env = {**os.environ, 'PATH': str(bindir) + os.pathsep + os.environ['PATH'],
                   'TEST_AUTHFILE': str(authfile)}
            for ending in ('', 'exit 7\n'):
                result = subprocess.run(['bash', '-c', script + probe + ending],
                                        env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 7 if ending else 0, result.stderr)
                self.assertFalse(authfile.exists(), 'EXIT trap must remove authfile')

    def test_current_version_and_future_version(self):
        current = json.loads(Path('package.json').read_text())['version']
        self.assertEqual(release.version_for('v' + current), current)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            self.assertEqual(release.version_for('v2.3.4', root), '2.3.4')
            for bad in ('v0.1.0', 'v02.3.4', '-v2.3.4', 'v2.3.4-rc1',
                        'v2.3.4\n', 'v2.3.4;echo bad', 'v$(id)'):
                with self.subTest(tag=bad), self.assertRaises(ValueError):
                    release.version_for(bad, root)

    def test_every_manifest_must_match(self):
        for name in ('mixin/obscura-mixin.yaml', 'standalone/obscura.yaml',
                     'package.json', 'package-lock.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.fixture(root)
                file = root / name
                file.write_text(file.read_text().replace('2.3.4', '2.3.5'))
                with self.assertRaises(ValueError):
                    release.version_for('v2.3.4', root)

    def test_both_new_destinations_required(self):
        missing = subprocess.CompletedProcess([], 1, '', 'reading manifest: manifest unknown')
        with patch.object(release.subprocess, 'run', return_value=missing) as run:
            release.require_absent('0.1.0', '/private/auth')
        self.assertEqual(run.call_count, 2)
        self.assertIn('obscura-sbx-kit-mixin:0.1.0', run.call_args_list[0].args[0][-1])
        self.assertIn('obscura-sbx-kit:0.1.0', run.call_args_list[1].args[0][-1])
        existing = subprocess.CompletedProcess([], 0, '{"schemaVersion": 2}', '')
        for results in ([existing], [missing, existing]):
            with patch.object(release.subprocess, 'run', side_effect=results):
                with self.assertRaisesRegex(ValueError, 'overwrite refused'):
                    release.require_absent('0.1.0', '/private/auth')

    def test_registry_errors_do_not_mean_absent(self):
        for message in ('unauthorized', 'denied', 'TLS failure', 'timeout',
                        '429 rate limited', 'unknown error', ''):
            with self.subTest(message=message), patch.object(release.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 1, '', message)):
                with self.assertRaisesRegex(ValueError, 'absence not established'):
                    release.require_absent('0.1.0', '/private/auth')
        with patch.object(release.subprocess, 'run', side_effect=subprocess.TimeoutExpired('skopeo', 60)):
            with self.assertRaises(subprocess.TimeoutExpired):
                release.require_absent('0.1.0', '/private/auth')


if __name__ == '__main__':
    unittest.main()
