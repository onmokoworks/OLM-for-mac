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
// Exact translated operations/ABI and regeneration fidelity are intentional.
#[allow(clippy::eq_op, clippy::never_loop, clippy::overly_complex_bool_expr,
    clippy::double_parens, clippy::let_unit_value, clippy::unnecessary_cast,
    clippy::assign_op_pattern, clippy::ptr_eq, clippy::unused_unit,
    clippy::too_many_arguments, clippy::cmp_null, clippy::nonminimal_bool,
    clippy::needless_return)]
#[cfg(all(test, feature = "generated-reference"))]
#[rustfmt::skip]
mod generated;
// Exact translated operations/ABI and regeneration fidelity are intentional.
#[allow(clippy::eq_op, clippy::never_loop, clippy::overly_complex_bool_expr,
    clippy::double_parens, clippy::let_unit_value, clippy::unnecessary_cast,
    clippy::assign_op_pattern, clippy::ptr_eq, clippy::unused_unit,
    clippy::too_many_arguments, clippy::cmp_null, clippy::nonminimal_bool,
    clippy::needless_return)]
#[rustfmt::skip]
mod kernels;
mod ae;
pub mod algorithm;
mod byte_boundary;
#[cfg(all(test, feature = "generated-reference"))]
mod differential;
mod hot;
#[cfg(test)]
mod reference_tests;

// Exact translated operations/ABI and regeneration fidelity are intentional.
#[allow(clippy::eq_op, clippy::never_loop, clippy::overly_complex_bool_expr,
    clippy::double_parens, clippy::let_unit_value, clippy::unnecessary_cast,
    clippy::assign_op_pattern, clippy::ptr_eq, clippy::unused_unit,
    clippy::too_many_arguments, clippy::cmp_null, clippy::nonminimal_bool,
    clippy::needless_return)]
#[rustfmt::skip]
mod structured;
