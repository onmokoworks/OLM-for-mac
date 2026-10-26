#!/usr/bin/env python3
"""Confirm packaging changes only project.path in the historical references."""
import io
import json
from pathlib import Path
import sys
import zipfile

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'scripts'))
from package_ae_pixel_validation_request import find_png

reference_root = Path(sys.argv[2]) / 'refs/win_references'
images = 0
manifests = 0
with zipfile.ZipFile(sys.argv[1]) as package:
    for name in package.namelist():
        if not name.endswith('_request.zip'):
            continue
        with zipfile.ZipFile(io.BytesIO(package.read(name))) as request:
            filename = next(x for x in request.namelist() if x.endswith('/reference_manifest.json'))
            plugin = ('OLMDistanceGradation' if 'olmdistancegradation' in name else
                      {'olmblur_request.zip': 'OLMBlur', 'olmcolorkey_request.zip': 'OLMColorKey',
                       'olmtoondilate_request.zip': 'OLMToonDilate'}[Path(name).name])
            reference = reference_root / ('20260605_extra' if plugin == 'OLMDistanceGradation' else '20260604_olm') / plugin
            original = json.loads((reference / 'reference_manifest.json').read_text())
            original['project']['path'] = original['project']['path'].replace('\\', '/').rsplit('/', 1)[-1]
            assert original == json.loads(request.read(filename))
            manifests += 1
            for item in request.namelist():
                if item.endswith('.png'):
                    assert request.read(item) == find_png(reference, Path(item).name).read_bytes(), item
                    images += 1
print(f'PASS: {manifests} reference manifests differ only by portable project.path; {images} PNG payloads unchanged')
