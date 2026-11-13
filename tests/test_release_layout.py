"""Regressions for direct image manifests and digest-preserving OCI indexes."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('release', 'scripts/release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class LayoutTests(unittest.TestCase):
    def layout(self, root, layer='application/vnd.oci.image.layer.v1.tar+gzip',
               index_type=release.OCI_INDEX, child_type=release.OCI_MANIFEST):
        blobs = root / 'blobs/sha256'
        blobs.mkdir(parents=True)

        def blob(value):
            raw = json.dumps(value).encode()
            digest = hashlib.sha256(raw).hexdigest()
            (blobs / digest).write_bytes(raw)
            return {'digest': 'sha256:' + digest, 'size': len(raw),
                    'mediaType': value['mediaType']}

        child = blob({'schemaVersion': 2, 'mediaType': child_type,
                      'layers': [{'mediaType': layer}]})
        tagged = blob({'schemaVersion': 2, 'mediaType': index_type,
                       'manifests': [child]})
        tagged['annotations'] = {'org.opencontainers.image.ref.name': '0.1.1'}
        (root / 'index.json').write_text(json.dumps({
            'schemaVersion': 2, 'mediaType': release.OCI_INDEX, 'manifests': [tagged]}))
        return tagged

    def test_gzip_oci_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.layout(Path(tmp))
            release.check_layout(tmp, '0.1.1')

    def single_layout(self, root, layer_type='application/vnd.oci.image.layer.v1.tar+gzip',
                      manifest_type=release.OCI_MANIFEST):
        # Buildx single-platform/no-provenance shape: wrapper -> image manifest,
        # config and layer descriptors, with no intermediate index or attestation.
        blobs = root / 'blobs/sha256'
        blobs.mkdir(parents=True)

        def blob(raw, media_type):
            digest = hashlib.sha256(raw).hexdigest()
            (blobs / digest).write_bytes(raw)
            return {'mediaType': media_type, 'digest': 'sha256:' + digest,
                    'size': len(raw)}

        layer = blob(gzip.compress(b'fixture layer'), layer_type)
        config = blob(json.dumps({'architecture': 'arm64', 'os': 'linux',
                                 'rootfs': {'type': 'layers', 'diff_ids': [
                                     'sha256:' + hashlib.sha256(b'fixture layer').hexdigest()]}}
                                ).encode(), 'application/vnd.oci.image.config.v1+json')
        tagged = blob(json.dumps({'schemaVersion': 2, 'mediaType': manifest_type,
                                 'config': config, 'layers': [layer]}).encode(), manifest_type)
        tagged['annotations'] = {'org.opencontainers.image.ref.name': '0.1.1'}
        (root / 'oci-layout').write_text(json.dumps({'imageLayoutVersion': '1.0.0'}))
        (root / 'index.json').write_text(json.dumps({
            'schemaVersion': 2, 'mediaType': release.OCI_INDEX, 'manifests': [tagged]}))
        return tagged

    def test_single_platform_manifest_without_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.single_layout(Path(tmp))
            release.check_layout(tmp, '0.1.1')

    def test_single_platform_rejections(self):
        for kwargs, error in [
            ({'layer_type': 'application/vnd.oci.image.layer.v1.tar+zstd'}, 'gzip'),
            ({'layer_type': 'application/vnd.in-toto+json'}, 'gzip'),
            ({'manifest_type': 'application/vnd.docker.distribution.manifest.v2+json'}, 'OCI index'),
        ]:
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as tmp:
                self.single_layout(Path(tmp), **kwargs)
                with self.assertRaisesRegex(ValueError, error):
                    release.check_layout(tmp, '0.1.1')

    def test_single_platform_digest_and_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tagged = self.single_layout(root)
            with self.assertRaisesRegex(ValueError, 'matching version'):
                release.check_layout(root, '0.1.2')
            (root / 'blobs/sha256' / tagged['digest'][7:]).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                release.check_layout(root, '0.1.1')

    def test_index_attestation_layers_remain_distinct_from_images(self):
        for layer, accepted in [('application/vnd.in-toto+json', True),
                                ('application/vnd.oci.image.layer.v1.tar+gzip', False)]:
            with self.subTest(layer=layer), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                tagged = self.layout(root, layer=layer)
                path = root / 'blobs/sha256' / tagged['digest'][7:]
                index = json.loads(path.read_text())
                index['manifests'][0]['annotations'] = {
                    'vnd.docker.reference.type': 'attestation-manifest'}
                raw = json.dumps(index).encode()
                digest = hashlib.sha256(raw).hexdigest()
                (root / 'blobs/sha256' / digest).write_bytes(raw)
                tagged.update(digest='sha256:' + digest, size=len(raw))
                (root / 'index.json').write_text(json.dumps({'manifests': [tagged]}))
                if accepted:
                    release.check_layout(root, '0.1.1')
                else:
                    with self.assertRaisesRegex(ValueError, 'gzip'):
                        release.check_layout(root, '0.1.1')

    def test_actual_tagged_graph_not_outer_wrapper(self):
        for kwargs, error in [
            ({'layer': 'application/vnd.oci.image.layer.v1.tar+zstd'}, 'gzip'),
            ({'index_type': 'application/vnd.docker.distribution.manifest.list.v2+json'}, 'OCI index'),
            ({'child_type': 'application/vnd.docker.distribution.manifest.v2+json'}, 'OCI manifests'),
        ]:
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as tmp:
                self.layout(Path(tmp), **kwargs)
                with self.assertRaisesRegex(ValueError, error):
                    release.check_layout(tmp, '0.1.1')

    def test_digest_and_tag_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tagged = self.layout(root)
            with self.assertRaisesRegex(ValueError, 'matching version'):
                release.check_layout(root, '0.1.2')
            (root / 'blobs/sha256' / tagged['digest'][7:]).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                release.check_layout(root, '0.1.1')

    def test_index_child_digest_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tagged = self.layout(root)
            index = json.loads((root / 'blobs/sha256' / tagged['digest'][7:]).read_text())
            child = index['manifests'][0]
            (root / 'blobs/sha256' / child['digest'][7:]).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                release.check_layout(root, '0.1.1')


if __name__ == '__main__':
    unittest.main()
