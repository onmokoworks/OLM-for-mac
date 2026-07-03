# OLMKiraKira Live Hotspot Probe

- Case: `kk_vertical_len50_brightness1_strength100`
- AE version: `26.3x87`
- Center: `(934, 118)` radius `3`
- Status: `current-live-host-drift-from-historical-kirakira-witness`

## Center

- Exported PNG: `[91, 91, 91, 255]`
- Reference PNG: `[131, 131, 131, 255]`
- Debug out_u8: `[45, 45, 45, 128]`
- Debug out_u8 * 2 RGB: `[90, 90, 90, 128]`
- Delta export-reference: `[-40, -40, -40, 0]`

## Binary identity

- Installed/built hashes match: `True`
- Installed SHA256: `b03e74624c20891098cd48419d4ae36b16cb0b1363ab9315c4b089f2bf08f9ff`
- Built SHA256: `b03e74624c20891098cd48419d4ae36b16cb0b1363ab9315c4b089f2bf08f9ff`

## Reading

- The current live Mac AE output at the hotspot does not reproduce the older 144-valued traced/mapped witness family. The exported PNG center is 91 versus the Windows reference 131, and the row above is 186 versus 191.
- This is not explained by a stale installed plug-in: the currently installed MediaCore binary hash matches the freshly built OLMKiraKira binary exactly. So the dark live output is a real current-implementation or current-host-path fact.
- Next: Do not keep assuming the historical 144 hotspot witness describes the present live host. Reconcile the old compose-boundary witness path with the current AE-host export path before more provenance-only reasoning.

## Rows (R channel)

| y | export | reference |
| --- | --- | --- |
| `115` | `[255, 255, 255, 255, 255, 255, 255]` | `[250, 250, 250, 251, 251, 251, 251]` |
| `116` | `[255, 255, 255, 255, 255, 255, 255]` | `[250, 250, 250, 251, 251, 251, 251]` |
| `117` | `[172, 172, 179, 186, 186, 186, 186]` | `[180, 180, 186, 191, 191, 191, 191]` |
| `118` | `[71, 71, 81, 91, 91, 91, 91]` | `[109, 109, 121, 131, 131, 131, 131]` |
| `119` | `[70, 70, 80, 91, 91, 91, 91]` | `[108, 108, 121, 131, 131, 131, 131]` |
| `120` | `[69, 69, 80, 90, 90, 90, 90]` | `[107, 107, 120, 131, 131, 131, 131]` |
| `121` | `[68, 68, 79, 90, 90, 90, 90]` | `[106, 106, 119, 131, 131, 131, 131]` |
