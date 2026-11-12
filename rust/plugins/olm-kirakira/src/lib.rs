//! OLMKiraKira CPU port. OLM-internal UCRT dependencies must not be published standalone.
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod adapter;
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ae;
pub mod algorithm;
pub mod filters;
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod params;
pub mod ramp;
pub mod trig;
mod trig_tables;

#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ae_ui;
pub mod editor;
mod presets;
