# OLMDistanceGradation 8bpc Mac Typed Boundary

Date: 2026-07-12

## Scope

Mac AE 26.3x87, 8bpc, working space `None`, linear blending off. The current
Debug plug-in (`sha256 c4949d03ce7e74fef3d1f34b7346dcb880b3d8849bf210a0aeba0d6d77a7defb`)
rendered the three cases from the pending Windows typed-boundary request at
`(397,281)`. These are Mac-side comparison facts, not Windows conformance.

## Typed Values

| Case | field_x | d_alpha | compose RGBA | PF8 store ARGB | final PNG RGBA |
| --- | ---: | ---: | --- | --- | --- |
| `case_0001` | `0` | `0` | `(0,1,0,0)` | `(0,255,0,0)` | `(0,0,0,0)` |
| `case_0015` | `0` | `0` | `(0,0,0,0)` | `(0,0,0,0)` | `(0,0,0,0)` |
| `case_0029` | `0` | `0` | `(0,0.109804153,0,0.933333397)` | `(0,28,0,238)` | `(0,0,0,0)` |

`case_0001` and `case_0029` deliberately expose the host boundary: the
plug-in stores hidden RGB under zero alpha, while the exported PNG is all zero.
The Windows return must therefore be compared stage by stage; final PNG alone
cannot identify compose versus host ownership.

## Whole-Image Results

| Case | max_diff | differing pixels | mean absolute channel diff |
| --- | ---: | ---: | ---: |
| `case_0001` | `2` | `195682` | `0.0474320023` |
| `case_0015` | `64` | `366796` | `1.5161243731` |
| `case_0029` | `23` | `226475` | `0.2793293065` |

The witness pixel itself is transparent zero in both Mac and reference for all
three cases. Its value is in the typed internal split, not as a residual pixel.

## Artifact Hashes

| Case | rendered PNG | field log | shade/store log |
| --- | --- | --- | --- |
| `case_0001` | `4e38e5fd4d4be8c8cee366a4ffebe7499832635ffed3f426f13a08417ce66185` | `1686d15fe4be7e06ab94c93e41e5717e2a01ce6e0c5602c91489cfbfb068a63c` | `117392f08ef2aaf83e62f508925857ca93603a9908fac7c2fcce4cf9918b63a5` |
| `case_0015` | `393f60193b5536d9c79a17fa23964cfdaceb91b54c0f262463ff3b2eb262c8fb` | `406a54581947c0fedc447e090caaf738f5d3c901589d374e40c20f176fe87e5c` | `ef8a36e38b77ea2da207faa8d70ee778823382cd6d4d1e9edcb6334a6b689608` |
| `case_0029` | `812ff8bec3bac86d1f87804ef3ae52756dfbfd941b61206ff684754eecef56b1` | `c98ebffee12610ccdc748c3e5565d2d3f840170b58013f761084b246a3c3e3c0` | `8d284ea36aae90aab6319231f64b01c7334cb1459bf08d8b2b8f9e43f55e8797` |

Runtime artifacts are under `/tmp/olmdg_8bpc_typed_mac_20260712`; this report
preserves the values and hashes needed to compare the pending Windows return.
