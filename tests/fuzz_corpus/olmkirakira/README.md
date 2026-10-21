The original seed-1, 300-case campaign produced no comparable Mac outputs: both
public routes refused every generated case. Its AEX counts are 287 successes and
13 rejections (not 13 pixel mismatches).

T06 adds eight refusal replay fixtures, selected from that original campaign to
cover every observed (route, guard, depth) combination with a successful AEX
reference. Their saved result objects and provenance are from the pre-tracing
`reports/fuzz/olmkirakira_20261021.json`; inputs are regenerated from seed 1 and
checked against the original input hashes. They are not manufactured pixel
counterexamples. Tracing must preserve every `matches_saved` result.

Scratch gate-off pixel witnesses live separately in
`tests/fuzz_corpus/olmkirakira_gate_off_T06` and require the T06 experiment driver.
