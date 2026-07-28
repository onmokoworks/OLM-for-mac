from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/emulation/olmradialblur_pf8_writer_oracle_20260728.py"
SPEC = importlib.util.spec_from_file_location("radial_pf8_writer_oracle", MODULE_PATH)
assert SPEC and SPEC.loader
oracle = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = oracle
SPEC.loader.exec_module(oracle)


def bits(value: float) -> int:
    return oracle.float32_bits(value)


def evaluate(**changes):
    arguments = dict(
        cell_raw_rgba=(bits(0.25), bits(0.6), bits(0.75), bits(0.5)),
        gain_raw=bits(2.0),
        scale_raw=bits(255.0),
        internal_base=0x100000,
        data_pointer=0x200000,
        rowbytes=32,
        width=6,
        height=10,
        x=3,
        y=4,
    )
    arguments.update(changes)
    return oracle.evaluate_pf8_writer(**arguments)


def test_models_shared_internal_relation_and_independent_pf8_destination():
    result = evaluate(
        observed_sampler_destination=0x100000 + 16 * (4 * 6 + 3),
        observed_writer_cell=0x100000 + 16 * (4 * 6 + 3),
        observed_destination=0x200000 + 4 * 32 + 3 * 4,
    )
    assert result.internal_address == 0x1001B0
    assert result.destination_address == 0x20008C
    assert result.internal_address != result.destination_address


def test_float32_gain_upper_clamp_alpha_bypass_truncation_and_argb_order():
    result = evaluate()
    assert result.call_raw_xmm0123 == (
        bits(0.5),
        bits(1.0),
        bits(1.0),
        bits(0.5),
    )
    assert result.stored_argb == (127, 127, 255, 255)
    assert result.cell_raw_rgba[3] == result.call_raw_xmm0123[3]


def test_raw_alpha_bits_are_preserved_at_call_boundary():
    negative_zero = 0x80000000
    result = evaluate(cell_raw_rgba=(bits(0.0), bits(0.0), bits(0.0), negative_zero))
    assert result.call_raw_xmm0123[3] == negative_zero
    assert result.stored_argb == (0, 0, 0, 0)


def test_counterexample_to_direct_sampler_as_final_pf8_store():
    result = evaluate()
    direct_rgba_scaled = (63, 153, 191, 127)
    assert result.stored_argb != direct_rgba_scaled
    assert result.stored_argb == (127, 127, 255, 255)


def test_pointer_witnesses_fail_closed_on_any_relation_mismatch():
    with pytest.raises(ValueError, match="writer cell relation failed"):
        evaluate(observed_writer_cell=0xDEADBEEF)
    with pytest.raises(ValueError, match="destination relation failed"):
        evaluate(observed_destination=0xDEADBEEF)


@pytest.mark.parametrize(
    "changes",
    [
        {"cell_raw_rgba": (bits(-0.01), bits(0.0), bits(0.0), bits(1.0))},
        {"cell_raw_rgba": (bits(math.nan), bits(0.0), bits(0.0), bits(1.0))},
        {"gain_raw": bits(math.inf)},
        {"scale_raw": bits(-255.0)},
        {"cell_raw_rgba": (bits(0.0), bits(0.0), bits(0.0), bits(2.0))},
    ],
)
def test_ungrounded_lower_nan_and_byte_overflow_cases_are_unsupported(changes):
    with pytest.raises(oracle.UnsupportedSemantics):
        evaluate(**changes)


def test_export_causality_is_explicitly_out_of_scope():
    with pytest.raises(oracle.UnsupportedSemantics, match="not host/export"):
        oracle.export_oracle(b"PF8")
