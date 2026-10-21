# All-ten current installed public routes — bounded AE-free closure

Status: `PASS_ALL10_CURRENT_INSTALLED_PUBLIC_ROUTES_AE_FREE_BOUNDED`

This is a heterogeneous, fixture-bounded hostless public-entry replay for all ten current installed plug-ins. It is not a claim over every tuple, source, depth, geometry, native After Effects execution, or native Windows host behavior.

| Plug-in | Bounded coverage | Public report |
| --- | --- | --- |
| ColorKeep | both Universal slices: all 10 source-bound legacy count5/100 paths, all 5 count9 paths, 18 legacy source mutations, and 136 count9 rejects per slice | `refs/conformance/colorkeep_current_installed_complete_union_20260814.json` |
| OLMBlur | both Universal slices: complete bounded Smart union PF8 12 + PF16 8 + PF32 20 = 40 exact cells and 1,298 negative controls per slice | `refs/conformance/olmblur_current_installed_complete_admission_union_20260813.json` |
| OLMColorKey | both slices: Classic 60 and Smart 60 bounded cells per slice; 13 callback rejects per slice | `refs/conformance/olmcolorkey_current_installed_public_closure_20260813.json` |
| OLMDirectionalBlur | current installed arm64: 33 bounded exact public cells; x86_64: 27 exact and six fail-closed pending native Windows UCRT expf counts 8/50/100; includes dual-side, Natural64 exact-source and Type3 Layer routes | `refs/conformance/olmdirectionalblur_current_installed_complete_bounded_union_20260814.json` |
| OLMDistanceGradation | both Universal slices: fixed PF32 Mode5 6 exact cells and all 8 PF32 Power cells fail closed per slice pending native UCRT powf | `refs/conformance/olmdistancegradation_current_installed_mode5_20260813.json` |
| OLMKiraKira | both Universal slices: 42 bounded public positives, 765 negatives, and 3 full-request controls per slice | `refs/conformance/olmkirakira_current_installed_public_closure_20260813.json` |
| OLMRadialBlur | both Universal slices: complete bounded public union of 106 exact-source Type1 cells plus all 45 fixed 9x7 Type3 source/Layer pairs per slice; 57 Type1 mutation rejects and 45 Type3 reject-control sets per slice | `refs/conformance/olmradialblur_current_installed_complete_public_union_20260814.json` |
| OLMSmoother | both Universal slices: complete bounded Classic admission union, 67 exact cells per slice | `refs/conformance/olmsmoother_v1_current_installed_admission_union_20260813.json` |
| OLMSmoother2 | both Universal slices: complete bounded Smart admission union, 39 exact cells; the newly installed PF8/PF16/PF32 expansion executes 94 public rows per slice in addition to the prior 25-cell union | `refs/conformance/olmsmoother2_current_installed_public_20260813.json` |
| OLMToonDilate | both Universal slices: 12 fixed same-source current installed cells per slice paired to the bounded Windows public owner | `refs/conformance/olmtoondilate_current_installed_exact12_20260813.json` |

Installed authority: `refs/conformance/olm_all10_current_source_installed_authority_20260813.json` (`8138180651e805e352fdb6ffd2e91abd426803d7395d949a545e73c421f3e6f9`).

After Effects was not launched; the observed AE-family process set was empty.
