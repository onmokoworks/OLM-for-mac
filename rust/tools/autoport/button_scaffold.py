"""Scoped button extension until the scaffold owner adds PF_Param_BUTTON.

Build inputs are derived in an owned run, never edited in the sibling tool.
Exact anchors fail closed if upstream changes. All ordinary capture validation
remains active; missing button labels are never inferred from the public name.
"""
from pathlib import Path
import types

TOOLS = Path(__file__).resolve().parent.parent


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("scaffold extension anchor changed")
    return source.replace(old, new, 1)


def load_scaffold():
    path = TOOLS / 'scaffold/olm_scaffold.py'
    source = path.read_text(encoding='utf-8')
    source = replace_once(source, '14:"group_end"}', '14:"group_end", 15:"button"}')
    source = replace_once(source, '("u.bd.u.nameptr", "u.pd.u.namesptr")',
                          '("u.bd.u.nameptr", "u.pd.u.namesptr", "u.button_d.u.namesptr")')
    module = types.ModuleType('autoport_button_scaffold')
    module.__file__ = str(path)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module


def prepare_probe(destination):
    """Prepare a new standalone capture-proxy source tree, with provenance."""
    import hashlib
    import json
    src = TOOLS / 'scaffold/probe'
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'src').mkdir()
    hashes = {}
    for name in ['Cargo.toml', 'Cargo.lock', 'build.rs', 'src/lib.rs']:
        data = (src / name).read_bytes()
        hashes[name] = hashlib.sha256(data).hexdigest()
        if name == 'src/lib.rs':
            text = data.decode('utf-8')
            text = replace_once(text, '        PF_Param_POPUP => {', '''        PF_Param_BUTTON => {
            fields!(u.button_d.value);
            label = Some(("u.button_d.u.namesptr", text(p0.u.button_d.u.namesptr)));
        }
        PF_Param_POPUP => {''')
            data = text.encode('utf-8')
        (destination / name).write_bytes(data)
    (destination / 'source-provenance.json').write_text(json.dumps(hashes, indent=2))


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination', type=Path)
    prepare_probe(p.parse_args().destination)
