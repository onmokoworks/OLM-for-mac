#!/usr/bin/env python3
"""Original PARAMS_SETUP and raw Angle getter, without changing saved records."""
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'tools/emulation'))
from aex_loader import AexLoader
from aex_witness import leaf_check
import test_olmkirakira_ui_setup_actual_aex_20260806 as setup
from t16_probe import MAIN, sha


def main():
    setup.AEX = MAIN/'plugins_2025/OLMKiraKira.aex'
    assert sha(setup.AEX.read_bytes()) == setup.SHA
    _, rows = setup.run_actual()
    rotation = rows[-1]
    assert (rotation['disk_id'], rotation['param_type']) == (1, 3)
    loader = AexLoader(str(setup.AEX), verbose=False, fast=True)
    param, output = loader.host_alloc(176), loader.host_alloc(4)
    observations = []
    for degrees in (0, 1/65536, -1/65536, 17, -17, 17.25, 360):
        word = round(degrees*65536)
        loader.write_bytes(param, bytes(176))
        loader.write_bytes(param+0x38, struct.pack('<i', word))
        loader.write_bytes(output, bytes.fromhex('cdcdcdcd'))
        leaf_check(loader, 0x181232670, [param, output], max_instructions=100)
        actual = struct.unpack('<i', loader.read_bytes(output, 4))[0]
        assert actual == word
        observations.append(dict(ui_degrees=degrees, fixed_word=word, owner_rotation=actual))
    print(json.dumps(dict(aex_sha256=setup.SHA, rotation_setup=rotation,
                         getter='181232670', observations=observations), indent=2))


if __name__ == '__main__':
    main()
