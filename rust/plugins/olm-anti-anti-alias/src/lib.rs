#[cfg(any(windows, target_os = "macos"))]
mod ae;
pub mod algorithm;
mod generated;
pub mod palette;
#[cfg(any(windows, target_os = "macos"))]
mod params;
#[cfg(any(windows, target_os = "macos"))]
mod ui;
#[cfg(feature = "witness")]
mod witness;
