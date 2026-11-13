//! Faithful OLMBlur CPU kernels. UCRT math artifacts are OLM-internal; do not publish standalone.
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ae;
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ae_support;
pub mod algorithm;
#[cfg(test)]
mod reference_tests;
