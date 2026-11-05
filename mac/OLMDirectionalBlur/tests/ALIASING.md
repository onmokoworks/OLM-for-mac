# T21: read-only input / Noise Layer aliasing

## Original AEX facts

Source: MAIN `decomp/OLMDirectionalBlur.aex.c.txt` and
`disasm/OLMDirectionalBlur.aex.asm.txt`; original AEX SHA-256
`d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.

* SmartPreRender's sole layer checkout is at `0x180008666`, with input and
  checkout IDs zero (`0x18000865a..65d`). It unions the input rectangles.
* SmartRender `0x180007bd0` checks out input pixels at `0x180007c36`, then
  output through callback +0x10. It does not check out Noise Layer pixels.
* Parameter builder `0x180006c50` skips slot 17. At
  `0x180007158..7176`, positive Noise Variation selects internal mode 2 only
  for popup value 3; popup values 1/2 select generated-noise mode 3.
* The depth workers request parameter 17 only in internal mode 2:
  PF8 call `0x180004efb`, PF16 `0x18000416b`, PF32 `0x180005c8b`.
  These branches follow the workers' early no-op/copy path.
* The layer is read to construct private float fields. For example, PF8
  `0x180004f90..4fda` allocates/locks fields at context +0x80a8/+0x80b0;
  `0x1800050d3..5117` loads checked-out layer bytes, and `0x180005177`
  writes the private field. The input populate callbacks are
  `0x180006980` / `0x1800068e0` / `0x180006a20`; output callbacks are
  `0x180006b30` / `0x180006a90` / `0x180006bd0`.

`aliasing.py` executes the original workers and original Iterate callbacks
under Python Unicorn, without rotate or rowdriver replacements. It redirects
only the host-provided layer world payload pointer, using either the input
pointer or input + one typed pixel. The backing allocation includes the extra
pixel. The original's parameter callback observes zero slot-17 checkouts for
Types 1/2 and one for Type 3. Source-memory write hooks and before/after
snapshots detect no writes in the exercised alias cases. This is bounded
CPU-emulator evidence, not a real-AE or general Windows-math claim.

The legacy fixture's rowdriver diagnostic reads y=73 even on small images;
it faulted on the 8x8 PF16 probe before output. The new harness omits that
observer only. It does not omit or replace AEX processing instructions.

## Mac write-path audit and change

`CopyWorld` stores only to output. `RenderExact8` reads input into a private
source vector, passes Noise Layer as const bytes, and writes only output from
a private destination vector. `StageDirectionalWorld` copies from const world
bytes into a vector; `UnstageDirectionalWorld` writes the output. Deep feature
rendering stages input and layer independently. The field kernel reads const
layer pixels and builds private fields. No input or layer padding is scratch.
SmartRender's workspace/staged output allocations own their storage; final
publication copies active rows only, after cleanup succeeds.

Inference from this audit and the dynamic evidence: input/layer disjointness
is unnecessary. The two deep/retained admission checks now allow their overlap.
Output disjointness is retained, and the Smart output/layer check now covers
all three depths before staging can hide the real destination's address.

The host follows the original checkout mechanism: input-only pre-render and
pixel checkout, and parameter-17 checkout only for positive-variation Type 3.
It uses that checked parameter's world and checks it in through the existing
exception-safe parameter cleanup. Types 1/2 cannot be rejected because an
unused selected layer shares input footage.

## Verification and remaining gate boundary

From this worktree, run using MAIN's existing emulation venv:

```sh
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' mac/OLMDirectionalBlur/tests/aliasing.py
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' mac/OLMDirectionalBlur/tests/replay_aliasing.py
```

The alias test passes 39 checks: 27 exact AEX/Mac comparisons (3 depths ×
3 types × independent/same/partial input-layer payloads), plus 12 output
alias refusals. Inputs include mixed alpha; both source storage and output
padding remain intact. The public Mac path also checks balanced cleanup and
absence of Noise Layer pre-render/pixel checkout.

The replay includes T17's three retained fixtures from commit
`8bb478938cf7fd968cd3fdb8dcc92b97665e37be` and all older retained corpora:
309 cases. All 309 have unchanged render statuses, output hashes and difference
records. However, **strict saved-object matches are 0/309**: each differs only
at `/routes/smart/metadata/COUNTS`, because parameter checkout/checkin counts
change from `21 21 1 1 1` to `20 20 1 1 1`. The replay intentionally exits 1;
it does not rewrite saved results or hide that change. Thus the ticket's literal
zero-changed-saved-outcomes condition is not met, despite zero pixel or route
regressions. The orchestrator must resolve this metadata-contract change.

The release gate is run separately with scratch/report paths under T21.
Its logs include missing historical workers and untracked fixtures in this
worktree, plus lifecycle assertions expecting the former checkout counts.
The run was stopped after 156 completed commands (32 passed, 124 failed);
no final full-gate report was produced. Do not infer a green gate or change its fixtures/identities to pass.
Full results and the exact command are in the uncommitted T21 report. Real-AE
T18 rendering and Windows comparison remain the orchestrator's post-merge check.
