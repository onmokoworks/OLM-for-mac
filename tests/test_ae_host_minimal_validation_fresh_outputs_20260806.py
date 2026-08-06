from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts/ae_host_minimal_validation.jsx").read_text(encoding="utf-8")


def test_each_render_removes_stale_png_before_save() -> None:
    remove = 'if (png.exists && !png.remove())'
    render = 'comp.saveFrameToPng(0.0, png);'
    wait = 'if (waitForFile(png, 20, 250))'

    assert SCRIPT.count(remove) == 1
    assert SCRIPT.index(remove) < SCRIPT.index(render) < SCRIPT.index(wait)
    assert "could not remove stale PNG before render" in SCRIPT
