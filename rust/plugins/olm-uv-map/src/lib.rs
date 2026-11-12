#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ae;
pub mod algorithm;
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod arbitrary;
mod derivative;
mod log_tables;
pub mod numerics;
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod params;
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ui;
