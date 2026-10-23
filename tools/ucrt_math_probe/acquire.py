#!/usr/bin/env python3
"""Acquire only Microsoft's SDK redistributable; never store binaries in git."""
import hashlib, json, pathlib, urllib.request, zipfile
VERSION = '10.0.28000.2705'
URL = f'https://api.nuget.org/v3-flatcontainer/microsoft.windows.sdk.cpp/{VERSION}/microsoft.windows.sdk.cpp.{VERSION}.nupkg'
def main():
    root = pathlib.Path.home()/'.cache/olm-emu/ucrt'/VERSION
    root.mkdir(parents=True, exist_ok=True)
    archive = root/'sdk.nupkg'
    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)
    with zipfile.ZipFile(archive) as z:
        selected = [n for n in z.namelist() if n.endswith('/x64/ucrtbase.dll') or n.lower().endswith('/ucrt/x64/libucrt.lib')]
        for name in selected:
            dest = root/pathlib.Path(name).name
            dest.write_bytes(z.read(name))
            print(json.dumps(dict(source=URL, member=name, path=str(dest), sha256=hashlib.sha256(dest.read_bytes()).hexdigest())))
        print('libucrt.lib members:', [n for n in z.namelist() if n.lower().endswith('/libucrt.lib')])
if __name__ == '__main__': main()
