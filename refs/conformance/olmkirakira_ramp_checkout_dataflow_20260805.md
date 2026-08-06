# OLMKiraKira ramp checkout dataflow

Status: **pointer chain and Mac connection grounded**

With `Use Ramp` off, `FUN_18114e860` skips checkout. With it on, the AEX finds
the arbitrary row by disk ID in the effect-owned ID array, acquires PF Handle
Suite v2, checks out and locks the host handle, copies exactly `0x144` bytes
from `locked_object + 0x10`, unlocks it, releases the temporary checkout, and
releases the suite. The copied block remains owned by render state.

The payload does not come from sequence/global data, a static table, or the
checkbox bytes. Mac now locks/copies/unlocks the native arbitrary handles in
both standard and Smart Render and passes the copied ramps to Mode2.
