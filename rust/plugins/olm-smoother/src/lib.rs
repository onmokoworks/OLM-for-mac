//! OLMSmoother v1: Classic 8/16-bit CPU effect. No SmartFX or float path.
#![allow(
    non_snake_case,
    non_upper_case_globals,
    unused_parens,
    unused_mut,
    unused_variables,
    unused_assignments,
    dead_code
)]
mod support;
// Mechanical instruction translation: retain TEST/XOR operands, dispatch loops,
// and disabled trace predicates verbatim for reference parity.
#[allow(clippy::eq_op, clippy::never_loop, clippy::overly_complex_bool_expr)]
#[cfg(all(test, feature = "generated-reference"))]
#[rustfmt::skip]
mod generated;
#[allow(clippy::eq_op, clippy::never_loop, clippy::overly_complex_bool_expr)]
#[rustfmt::skip]
mod kernels;
mod ae;
pub mod algorithm;
#[cfg(all(test, feature = "generated-reference"))]
mod differential;
mod hot;
#[cfg(test)]
mod reference_tests;

#[allow(clippy::eq_op, clippy::never_loop, clippy::overly_complex_bool_expr)]
#[rustfmt::skip]
mod structured;
