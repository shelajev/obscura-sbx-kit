"""Exercise native CDP child failure without a browser or Docker daemon."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class CdpTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node') and Path('node_modules/puppeteer-core').is_dir(),
                         'requires Node and npm ci')
    def test_signal_terminated_native_browser_exits_promptly(self):
        with tempfile.TemporaryDirectory() as tmp:
            browser = Path(tmp) / 'browser'
            browser.write_text('#!/bin/sh\necho "fake browser SIGTERM" >&2\nkill -TERM $$\n')
            browser.chmod(0o700)
            env = {**os.environ, 'OBSCURA_BINARY': str(browser)}
            env.pop('OBSCURA_DOCKER_IMAGE', None)
            result = subprocess.run(['node', 'tests/cdp.mjs'], env=env,
                                    capture_output=True, text=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('fake browser SIGTERM', result.stderr)
            self.assertNotIn('CDP readiness timed out', result.stderr)


if __name__ == '__main__':
    unittest.main()
