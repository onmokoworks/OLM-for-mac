# OLM all-10 current source → installed authority (2026-08-13)

Status: `pass_all10_current_source_candidate_installed_exact_ae_deferred`

Each current production source is bound by its plug-in-specific build/install authority to the exact candidate executable named by the accepted identity manifest. Candidate and installed full bundle inventories are identical for all ten plug-ins; every installed executable is arm64+x86_64 and passes strict/deep code-sign verification.

| Plug-in | source SHA-256 | installed executable SHA-256 |
|---|---|---|
| ColorKeep | `d1c443042998e466b021d6fd2351537a2be63fe95d3e79a2089d82f78217bac3` | `dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d` |
| OLMBlur | `22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7` | `ecdf3d93b4b38fe71f4b66f717079aa86b961205d0a3f1b5b7edbd29e353284d` |
| OLMColorKey | `7c66240d5813e240663d06fe342d45b73b9b2ce2f2d8b0852ffe7f73351e4001` | `701ae9192e19d3e97dd33450e37ae97d90d9be5803ab663405507ed5e3659ca7` |
| OLMDirectionalBlur | `494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845` | `856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de` |
| OLMDistanceGradation | `06ffc5b7a2af5cf54a2503d3bf03f9baf2269acbf1277f034937ac79c4a7aba5` | `231421e4a0c1607a70947778d99d748baefe07078b7e1145f4a4700268116605` |
| OLMKiraKira | `f251b19150a0b490d58cf6bece4c40fe9403f9bd36849cfe8c89ffbd14fc96c2` | `edd6953ff0a86efa550ffd8a5be050cb200342ad68427519c092bcac578596a7` |
| OLMRadialBlur | `b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1` | `9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5` |
| OLMSmoother | `c8c7b7728553ee4ccaadc7ef802be40e607d7e7a7b829958d4b8dfab80f633dc` | `f416579eeb61b73da683437d382f786781e6ecdf27d9c4fc52f3ad1d55577162` |
| OLMSmoother2 | `c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168` | `c8ea1f0e7dbe7398006578b91e01adfcea975a8c8a3244657ea934eda587c53f` |
| OLMToonDilate | `ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b` | `5bbe693106072ceff14a1c1ae5a0d64815cddde58356c57575d29e516479036e` |

Boundary: this is a hostless identity/provenance audit. It launches no After Effects process, adds no numerical claim, and does not claim Developer ID signing or notarization. The current-identity AE checkpoint remains deliberately deferred for a later batched run.
