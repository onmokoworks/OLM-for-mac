//! OLMColorKey algorithm and separate AE adapter.
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ae;
pub mod algorithm;
mod color;
mod distance;
#[cfg(test)]
mod reference_tests;
