# OLMKiraKira installed FP-contract seam (2026-08-13)

Status: `PASS_OLMKIRAKIRA_INSTALLED_FP_CONTRACT_SEAM_OLD37_NEW42_NO_AE`

The retained predecessor is oracle-exact in 37/42 bounded public cells. The current installed correction is exact in 42/42. Both binaries retain Classic=Smart internally; the five old mismatches are PF32 only:

| tuple | old word differences | old max ULP | old SHA | current/oracle SHA |
|---|---:|---:|---|---|
| m1_h7_r0 | 3 | 2 | `ce8b0cfdabcc3960fc2d79a4a268d2115ade1f0c7595fd07e21b4d2e03788b46` | `0d50d86e40f9dd25daef5683e78bc3c066501477ccc36c8c4c7eab0c274b2cb6` |
| m1_h7_r1 | 9 | 2 | `792d84bbe657e78d503f875980aa9cd6b600d1abb5ec167a87413451e5af2995` | `4a221600eb32528a6b186712f1dc9a3d5f97b2f61add1ae8662e8c52e2dd58bb` |
| m3_h50_r0 | 5 | 1 | `5cb3df6263dd05b83e29b246b3e70cd57d36d58ca113162138521945fd28ca76` | `36a6eebfb764e075667cf1d0f40cba6d7e8ef7fb65fbc95b66721e7ae44a1518` |
| m3_h50_r1 | 6 | 1 | `d1eb63633ff66aa3ca6ea4aef922ebb7aa8225e1be5fc7505b0eec77a1b1e37f` | `3d7f63c1ff88a3a4f00205af6a553a6f7a0927f5ae68bd4e93a2d901f55749f5` |
| m4_multiray | 5 | 1 | `33a66a7e7e38bf19a10b715f7a3a30fd016961536c07f7619ae991049c53c709` | `4b82d09706892d87e42088a909dc5884a158e711947cf86181444a7e3108f858` |

Boundary: same real-SDK AE-free harness and retained installed binaries only. No native-AE or unlisted-product claim.
