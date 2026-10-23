"""Resolve read-only fixture inputs without relocating worktree source or outputs.

Call only for inputs: returned MAIN paths must never be used as write targets.
A missing input stays worktree-relative so diagnostics retain the requested path.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=None)
def main_assets(root: Path = ROOT) -> Path:
    override = os.environ.get("OLM_MAIN_ASSETS")
    if override:
        return Path(override).expanduser().absolute()
    common = subprocess.check_output(
        ["git", "rev-parse", "--git-common-dir"], cwd=root, text=True,
    ).strip()
    path = Path(common)
    if not path.is_absolute():
        path = root / path
    return path.resolve().parent


def resolve_asset(path: str | Path, root: Path = ROOT) -> Path:
    """Prefer the worktree input, then the same relative input in MAIN.

    Absolute paths outside the worktree are explicit caller choices and are
    preserved. No directory is created, copied, linked, or written here.
    """
    root = Path(root).absolute()
    requested = Path(path)
    local = Path(os.path.abspath(requested if requested.is_absolute() else root / requested))
    try:
        relative = local.relative_to(root)
    except ValueError:
        return local
    if local.exists():
        return local
    fallback = main_assets(root) / relative
    return fallback if fallback.exists() else local


def asset_relative(path: str | Path, root: Path = ROOT) -> Path:
    """Keep evidence path labels repository-relative after input resolution."""
    path = Path(path)
    try:
        return path.relative_to(root)
    except ValueError:
        return path.relative_to(main_assets(root))
