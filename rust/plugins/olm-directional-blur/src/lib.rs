mod admission;
mod ae;
pub mod algorithm;
mod host;
mod noise;
mod rotate;
mod rowdriver;
mod sha256;
mod ui;

// Diagnostic ABI only; absent from default/release builds unless explicitly enabled.
#[cfg(feature = "stage-dump")]
mod stage_dump;
