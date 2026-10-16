#!/usr/bin/env python3
"""Build the static browser game: python3 tools/build_web.py.

Optional deployment hook (Claude may enable before existing publish steps):
    python3 tools/build_web.py
Then publish dist/web/ under /tuipet/; index.html must revalidate on navigation.
No deploy script is executed or modified here.
"""
import gzip
import struct
import zlib
import hashlib
import json
from pathlib import Path
import shutil
import tomllib
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def catalog_icon(size):
    # Scale the first catalog egg's first frame without changing its pixels.
    eggs = json.loads(gzip.decompress((ROOT / 'src/tuipet/data/eggs.json.gz').read_bytes()))
    frame = eggs[0]['frames'][0]
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))
    pixels = bytearray()
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            ink = frame[y * len(frame) // size][x * len(frame[0]) // size] == '1'
            pixels.extend((220, 220, 220) if ink else (0, 0, 0))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes(pixels))) + chunk(b'IEND', b''))


def build():
    version = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    out = ROOT / 'dist/web'
    out.mkdir(parents=True, exist_ok=True)
    cache = ROOT / 'build/web-vendor'
    cache.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / 'tools/web/vendor-lock.json').read_text(encoding='utf-8'))
    for name, spec in lock.items():
        dest = cache / name
        spike = ROOT / '_astra/spike_web/vendor' / name
        if not dest.exists() and spike.exists():
            shutil.copyfile(spike, dest)
        if not dest.exists():
            url = spec['url']
            if name.endswith('.whl'):
                with urllib.request.urlopen(url, timeout=60) as response:
                    metadata = json.load(response)
                url = next(x['url'] for x in metadata['urls'] if x['filename'] == name)
            with urllib.request.urlopen(url, timeout=60) as response:
                dest.write_bytes(response.read())
        if digest(dest.read_bytes()) != spec['sha256']:
            raise ValueError(f'Artifact hash mismatch: {name}')
    archive = ROOT / 'build/web-game.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted((ROOT / 'src/tuipet').rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                info = zipfile.ZipInfo(str(path.relative_to(ROOT / 'src')), (2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo(f'tuipet-{version}.dist-info/METADATA', (2020, 1, 1, 0, 0, 0))
        z.writestr(info, f'Metadata-Version: 2.1\nName: tuipet\nVersion: {version}\n')
    loader = (ROOT / 'tools/web/loader.js').read_bytes()
    identity = digest(archive.read_bytes()+loader+json.dumps(lock, sort_keys=True).encode())[:16]
    assets = f'assets/{version}-{identity}/'
    target = out / assets
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive, target / 'game.zip')
    (target / 'vendor').mkdir(exist_ok=True)
    for name in lock:
        shutil.copyfile(cache / name, target / 'vendor' / name)
    (target / 'loader.js').write_bytes(loader)
    manifest = {'version':version, 'build':identity, 'pyodide':'0.27.7',
                'wheels':sorted(n for n in lock if n.endswith('.whl')),
                'service_worker':None, 'files':{'game.zip':digest(archive.read_bytes()), 'loader.js':digest(loader),
                         **{'vendor/'+name:spec['sha256'] for name,spec in lock.items()}}}
    encoded = json.dumps(manifest, indent=2)+'\n'
    (target / 'manifest.json').write_text(encoded, encoding='utf-8')
    pwa = {'name':'tuipet', 'short_name':'tuipet', 'start_url':'./', 'scope':'./',
           'display':'fullscreen', 'background_color':'#121212', 'theme_color':'#121212',
           'icons':[{'src':f'icon-{size}.png', 'sizes':f'{size}x{size}', 'type':'image/png'} for size in (192, 512)]}
    pwa.update(manifest)
    (out / 'manifest.json').write_text(json.dumps(pwa, indent=2)+'\n', encoding='utf-8')
    for size in (192, 512):
        (out / f'icon-{size}.png').write_bytes(catalog_icon(size))
    html = (ROOT / 'tools/web/index.html').read_text(encoding='utf-8').replace('@ASSETS@', assets)
    (out / 'index.html').write_text(html, encoding='utf-8')
    for old in (out / 'assets').iterdir():
        if old != target:
            shutil.rmtree(old)
    print(f'tuipet {version}: {out} ({identity})')


if __name__ == '__main__':
    build()
