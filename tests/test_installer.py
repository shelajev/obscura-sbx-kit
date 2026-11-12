import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('installer', 'mixin/scripts/install-browser.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def bundle(self, path, symlink=False):
        with tarfile.open(path, 'w:gz') as archive:
            for name in ('obscura', 'obscura-worker', '../../unwanted'):
                member = tarfile.TarInfo(name)
                body = b'test executable'
                member.size = len(body)
                if symlink and name == 'obscura':
                    member.type = tarfile.SYMTYPE
                    member.linkname = '/etc/passwd'
                archive.addfile(member, io.BytesIO(body))
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_hash_and_selected_regular_members_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'release.tar.gz'
            digest = self.bundle(archive)
            with self.assertRaises(ValueError):
                installer.extract_verified(archive, '0' * 64, root / 'out')
            self.assertFalse((root / 'out').exists())
            installer.extract_verified(archive, digest, root / 'out')
            self.assertEqual({p.name for p in (root / 'out').iterdir()}, {'obscura', 'obscura-worker'})
            self.assertEqual((root / 'out/obscura').stat().st_mode & 0o777, 0o755)
            self.assertFalse((root.parent / 'unwanted').exists())

    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'release.tar.gz'
            digest = self.bundle(archive, symlink=True)
            with self.assertRaises(ValueError):
                installer.extract_verified(archive, digest, root / 'out')

    def test_http_redirect_refused(self):
        with self.assertRaises(ValueError):
            installer.HTTPSOnlyRedirect().redirect_request(None, None, 302, '', {}, 'http://bad')

    def test_distribution_notices_and_metadata(self):
        for kit in ('mixin', 'standalone'):
            self.assertEqual(Path(kit, 'LICENSE').read_bytes(), Path('LICENSE').read_bytes())
            self.assertEqual(Path(kit, 'NOTICE').read_bytes(), Path('NOTICE').read_bytes())
            self.assertTrue(Path(kit, 'licenses/V8.txt').is_file())
            descriptor = next(Path(kit).glob('*.yaml')).read_text()
            self.assertIn('sourceUrl: https://github.com/shelajev/obscura-sbx-kit', descriptor)
            self.assertIn('io.github.shelajev/obscura@0.2.6', descriptor)

    def test_shared_sources_match(self):
        for name in ('obscura.py', 'install-browser.py'):
            self.assertEqual(Path('mixin/scripts', name).read_bytes(), Path('standalone/scripts', name).read_bytes())

    def test_recipes_share_download_stage(self):
        mixin = Path('mixin/obscura-mixin.dockerfile').read_text().split('FROM scratch')[0]
        self.assertTrue(Path('standalone/obscura.dockerfile').read_text().startswith(mixin))


if __name__ == '__main__':
    unittest.main()
