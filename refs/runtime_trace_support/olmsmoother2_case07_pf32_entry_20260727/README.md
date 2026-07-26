# OLMSmoother2 case-07 PF32 input-entry witness

This support bundle captures the `PF_PixelFloat` input world at
`OLMSmoother2.aex+0x4270` while Windows AE 26.3x87 renders the case-07
Preserve RGB effect AEP.

The CDB script rejects any descriptor other than `1920x1080` with
`rowbytes=30720`, stops the effect thread, and leaves the process stable for
read-only extraction. `read_process_memory.ps1` requires the observed PID,
data address, and exact `33177600`-byte length, rejects short reads, and hashes
the returned file.

Canonical evidence is bound by:

- `refs/conformance/olmsmoother2_case07_windows_preserve_rgb_reference_20260727.json`
- exact AEX SHA-256
  `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`
- raw entry SHA-256
  `133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b`
- same-run Windows effect SHA-256
  `404d2b5732adf9bbbc6aadab4a1f0dd075e4e0f911b29076339f6f0e17479cc0`

The raw entry is stored gzip-compressed. Verify it against the bound source
EXR with:

```bash
python3 scripts/compare_pf32_entry_to_exr.py \
  refs/conformance/fixtures/olmsmoother2_case07_pf32_entry_20260727/pf32_input_entry_argb.bin.gz \
  refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMSmootherv2/olm_bitdepth_32bpc_olmsmoother2_exr_20260710__software_32bpc__fr24__final_random10_olm_smoother_v2_07_before_effects.exr
```

This witness proves input-entry identity. It does not by itself prove AE
exactness; the no-effect and effect-on raw FLOAT32 output gates remain
mandatory.
