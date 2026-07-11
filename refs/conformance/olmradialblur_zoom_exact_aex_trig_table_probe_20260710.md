# OLMRadialBlur Zoom Exact AEX Trig-Table Probe

Date: 2026-07-10  
Case: `case_0009`, 8bpc Zoom

## Scope

This is a bounded local diagnostic. The Mac plugin was not modified, and no
fix or promotion claim is made.

The exporter calls `plugins_2025/OLMRadialBlur.aex` at
`FUN_18001d060` (`0x18001d060`) through `AexLoader`. For each actual Zoom
angle-grid index it passes the scalar-float angle
`f32(f32(angle_index) * f32(step_rad))` and records the returned low/high
`XMM0` lanes as sine/cosine.

The case manifest was checked before export:

| Parameter | Value |
| --- | ---: |
| `Quality` | `5` |
| `Center` | `[960, 540]` |
| `Ratio` | `1` |
| `Angle` | `0` |
| `step_rad` f32 bits | `0x3b64c388` |
| angular count | `360 * Quality = 1800` |

## Deterministic Table Contract

`tools/emulation/export_radialblur_trig_table.py` writes a versioned
little-endian table with an 8-byte magic, version, angular count, f32 step
bits, `1800 * 8 = 14400` payload bytes, and a SHA-256 digest over the header
and payload. The generated artifact measured `14452` bytes total:

```text
angular_count=1800
payload_bytes=14400
sha256=9ebda7e177f6082bd31b414c40e2f877c3761ee4b3c104e77613019be87fc382
```

That value is the digest stored in the table footer over header+payload. The
SHA-256 of the complete file including its digest footer is
`ce33ec965eec6e4311380751502e6e189ad520feda3d064c5fe141201a6aab68`.

The CLI `--zoom-aex-trig-table` path checks magic, version, exact file length,
case-derived count, case-derived f32 step bits, and SHA-256 before indexing
`table[angle_index]`. A one-byte-truncated copy was rejected with
`Zoom AEX trig table length mismatch` and exit status `1`.

## Probe

Commands:

```sh
python3 tools/emulation/export_radialblur_trig_table.py \
  --output /tmp/olmradialblur_zoom_case0009_aex_trig.bin

refs/scripts/build_olmradialblur_cli.sh /tmp/olmradialblur_exact_trig_cli

python3 refs/scripts/run_reference_test.py \
  refs/win_references/20260604_olm/OLMRadialBlur \
  --run-dir /tmp/olmradialblur_exact_aex_table_probe_20260710 \
  --case-id case_0009 --expected-effect 'OLM RadialBlur' \
  --command '"/tmp/olmradialblur_exact_trig_cli" --input "{input}" \
    --params "{params}" --output "{output}" \
    --zoom-aex-trig-table /tmp/olmradialblur_zoom_case0009_aex_trig.bin \
    --zoom-inverse-float'
```

Exporter wall time was `0.31s`. The full-frame harness run was `2.84s` wall
time. The candidate comparison was `max=1`, `mean=0.0046`, and
`31025/2073600` pixels with a nonzero RGBA difference.

## Five Witnesses

| Pixel | Windows reference | Exact-table + inverse-float candidate |
| --- | --- | --- |
| `(6,0)` target | `(20,3,3,254)` | `(20,3,3,255)` |
| `(7,0)` target | `(21,3,3,254)` | `(21,3,3,255)` |
| `(12,0)` target | `(21,4,4,254)` | `(21,4,4,255)` |
| `(8,0)` control | `(21,3,3,255)` | `(21,3,3,255)` |
| `(24,0)` control | `(21,4,4,255)` | `(21,4,4,255)` |

## Result

The exact AEX helper output is now reproducibly exportable and consumed by
the forward Zoom diagnostic, with table indexing and integrity checks tied to
the real case grid. This probe still misses all three alpha-254 targets and
preserves both alpha-255 controls. It therefore provides no evidence for a
fix claim or for changing default behavior. Exact AEX trig plus the recovered
float inverse sequence is not sufficient; the remaining Zoom boundary is
later in polar-plane population, inverse sampling/collapse, or alpha ownership.
