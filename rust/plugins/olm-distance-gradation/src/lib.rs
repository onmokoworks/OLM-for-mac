//! Rust SmartFX port of OLMDistanceGradation. OLM-internal; not for standalone publication.
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ae;
pub mod algorithm;
mod bilateral;
mod field;
mod filters;
#[cfg(test)]
mod reference_tests;

// Diagnostic ABI only; absent from default/release builds unless explicitly enabled.
#[cfg(feature = "stage-dump")]
mod stage_dump;
