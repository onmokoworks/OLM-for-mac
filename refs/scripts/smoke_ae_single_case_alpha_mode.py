#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JSX = ROOT / "scripts/ae_render_single_case.jsx"


def main() -> int:
    source = JSX.read_text(encoding="utf-8")
    required = (
        'getenv("OLM_AE_INPUT_ALPHA_MODE")',
        'getenv("OLM_AE_INPUT_FILE_OVERRIDE")',
        "var inputFilename = inputFileOverride || requestCase.before_effects_frame;",
        "referenceManifest.current_reference_capture",
        "captureInfo.input_alpha_mode || referenceManifest.input_alpha_mode",
        "if (!inputAlphaMode)",
        "summary.input_alpha_mode = inputAlphaMode",
        "referenceManifest.comp && referenceManifest.comp.bpc",
        'requestedBitsSource = "comp.bpc"',
        'getenv("OLM_AE_PAUSE_BEFORE_RENDER") === "1"',
        'getenv("OLM_AE_READY_MARKER")',
        'getenv("OLM_AE_CONTINUE_MARKER")',
        "pause handshake timed out waiting for",
    )
    missing = [item for item in required if item not in source]
    if missing:
        raise SystemExit(f"single-case alpha-mode contract missing: {missing}")
    print("[OK] AE single-case input alpha mode: env override with manifest fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
