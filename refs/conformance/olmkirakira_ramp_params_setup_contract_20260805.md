# OLMKiraKira ramp parameter setup contract

Status: **exact registration; actual AEX 41 parameters, Mac 41**

The actual AEX registers each ramp family as four rows: `PF_Param_GROUP_START`,
`Use Ramp` checkbox, `PF_Param_ARBITRARY_DATA`, and `PF_Param_GROUP_END`.
The arbitrary rows use disk IDs `19`, `21`, `23`, `36`, and `25`.

The Mac implementation registers all four rows per family. Its native handle
stores the pointer-free `0x144` ramp payload and its canonical `0x145` wire
form zero-fills the unused tail accepted by actual AEX UNFLATTEN.
