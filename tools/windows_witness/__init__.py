"""Spec-driven Windows After Effects/CDB witness package compiler."""

from .compiler import compile_witness
from .core import SpecError, load_spec, validate_spec

__all__ = ["SpecError", "compile_witness", "load_spec", "validate_spec"]
