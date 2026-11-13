//! Diagnostic subset of the shared golden runner; no shared manifest writes.
#[path = "../../tools/golden/src/lib.rs"]
mod olm_golden;
include!("../../tools/golden/src/bin/golden-color-keep.rs");
