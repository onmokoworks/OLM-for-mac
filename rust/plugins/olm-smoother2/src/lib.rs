//! Staged, pure Rust port of OLMSmoother2. See VALIDATION.md for implemented scope.
//! AE entry points call the pure pipeline after checked admission.
mod admission;
mod ae;
pub mod algorithm;
pub mod class_plane;
pub mod frame;
pub mod gamma;
mod geometry;
pub mod lut;
pub mod oklab;
pub mod polygon;
pub mod scan;
mod sha256;
pub mod types;
pub mod weights;

#[cfg(test)]
mod reference_tests;

mod rows;
