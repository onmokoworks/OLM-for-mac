# OLMKiraKira ramp event contract

The actual AEX `PF_Cmd_EVENT` path is `entry_point` command 15 → MyEffect
vslot `+0x38` (`FUN_181151800`). It accepts only `PF_EA_CONTROL`, resolves the
parameter index at `PF_EventExtra+0x50`, and verifies arbitrary type `0x0b`.
Draw dispatch uses `RampDataHandler+0x68`; click and drag use `+0x70`. The
actual path marks handled/update-now at `extra+0xcc`, marks the parameter value
changed, and invalidates the control.

The advanced boundary closed here is stop deletion. In the actual AEX,
`FUN_181235bb0` receives internal event 5 for the final drag. When the pointer is
at least `0x15` pixels below the ramp origin, it shifts all later 20-byte stop
records left, decrements the active count, and sets the selected index to `-1`.
An exported-entrypoint probe reproduces this with marker click `(10,65)` followed by
final drag `(30,80)`: the count changes `3 -> 2`, selection changes `0 -> -1`,
the later records shift, and two invalidations are issued.

Stop addition is also closed through the exported entrypoint. A true
single-click (click count 1) at `(100,40)` is inside the actual ramp rectangle
`[10,5,202,55]` and outside its marker strip. The AEX changes the count `3 -> 4`,
inserts the sampled stop
`[0.46875, 1, 1, 0.39122599363327026, 0]`, preserves the later records in sorted
order, clears selection to `-1`, and invalidates the control. The click-count
field matters: values other than 1 are translated to the double-click/color
picker event rather than insertion.

Color editing is closed at the host-suite boundary. After selecting the first
marker, double-click at `(10,65)` dispatches internal event 3 and calls
`PF AE App Suite` v1 `PF_AppColorPickerDialog` (suite slot `+0x38`) with title
`Color select`, the selected stop's `[alpha, red, green, blue]`, and the
working-space-to-monitor flag enabled. The probe returns
`[0.25, 0.125, 0.5, 0.875]`; the AEX preserves position and count, changes only
those four record floats, retains selection 0, and invalidates the control. The
Mac implementation uses the same public suite call. The focused test covers
marker hit testing and the bounded four-field record replacement separately
from the modal host UI.

Picker return handling is also grounded through the exported entrypoint. A
`PF_Interrupt_CANCEL` (`0x205`) response leaves every stop byte unchanged and
clears selection `0 -> -1`. A non-cancel error (`13`) with no output write leaves
both the record and selection unchanged. Success, cancel, and error all leave
the entrypoint return at zero, set `evt_out_flags` to 9, set the parameter change
flag to 1, and invalidate after the double-click. The Mac path shares a focused
return-policy helper with the synthetic test and preserves these distinctions.

The Mac handler draws the ramp and stop markers through Drawbot. Click chooses
the nearest stop and stores it in `continue_refcon[0]`; ordinary drag clamps its
position between adjacent stops. A final drag below the ramp erases the selected
stop and clears `continue_refcon`. Clicking inside the gradient adds an alpha-1
stop whose RGB is sampled from the existing ramp, sorts it by position, and
clears `continue_refcon`. These paths mark the value changed and invalidate the
frame. The focused synthetic test covers selection, drag, both neighbor clamps,
deletion with record shifting, and addition with sampled color and sorting.
It also covers marker hit testing and color replacement. Live interaction with
AE's modal color-picker window remains a host gate; no synthetic picker is
shipped in production.

The remaining gate is live AE validation of Drawbot context acquisition and
continuous mouse delivery. No real-host interaction parity is claimed yet.
