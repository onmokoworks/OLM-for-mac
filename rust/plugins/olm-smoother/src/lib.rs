//! OLMSmoother v1: Classic 8/16-bit CPU effect. No SmartFX or float path.
#![allow(non_snake_case,non_upper_case_globals,unused_parens,unused_mut,unused_variables,unused_assignments,dead_code)]
mod support;
// Mechanical instruction translation: retain TEST/XOR operands, dispatch loops,
// and disabled trace predicates verbatim for reference parity.
#[allow(clippy::eq_op, clippy::never_loop, clippy::overly_complex_bool_expr)]
mod generated;
pub mod algorithm;
mod ae;
#[cfg(test)]
mod reference_tests;
