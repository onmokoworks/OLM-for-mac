# OLMDistanceGradation PF16 Smart pre-render parameter probe

The hash-pinned AEX `FUN_181174060` now executes naturally with probe-local checkout/checkin and ParamUtils suite callbacks. For parameter index 3 and depth boolean 1, it writes and forwards depth word `0x20`, checks the parameter back in, returns zero, and retains the full raw 0xb0-byte parameter block and callback order.

This closes only the Smart pre-render parameter/depth helper ABI. Result/max rectangles, sequence/pre-render data lifetime, checked-out PF16 worlds, padding, and final bytes require the outer `FUN_1811741a0 -> FUN_1811743b0 -> FUN_181170280` suite graph and remain unclaimed. No classic fixture is used as a Smart oracle.
