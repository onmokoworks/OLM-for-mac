import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/perf/run_generic_beta_smoke.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generic_perf", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_catalog_has_all_ten_lanes_and_both_geometries() -> None:
    module = load_module()
    assert len(module.LANES) == 10
    assert len(set(module.LANES)) == 10
    assert module.GEOMETRIES == {"hd": [1920, 1080], "uhd": [3840, 2160]}
    assert all(key[0] in module.LANES and key[1] in module.GEOMETRIES
               for key in module.COMMANDS)


def test_budgets_are_bounded() -> None:
    module = load_module()
    assert module.TIMEOUT_SECONDS["hd"] <= 120
    assert module.TIMEOUT_SECONDS["uhd"] <= 180
    assert module.RSS_BUDGET_BYTES["hd"] <= 2 * 1024**3
    assert module.RSS_BUDGET_BYTES["uhd"] <= 3 * 1024**3


def test_toondilate_has_exact_hd_uhd_production_drivers() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("OLMToonDilate", geometry)]
        assert command[-2:] == ["--geometry", geometry]
        assert "run_olmtoondilate_generic_production_perf.py" in command[1]
    predicate = module.SUPPORT_PREDICATES["OLMToonDilate"]
    assert "pf8_pf16_pf32" in predicate
    assert "0 <= search_radius <= 100" in predicate


def test_distancegradation_has_independent_hd_and_uhd_production_drivers() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("OLMDistanceGradation", geometry)]
        assert "test_olmdistancegradation_generic_production_beta_20260820.py" in command[-1]


def test_radialblur_has_exact_geometry_release_like_drivers() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("OLMRadialBlur", geometry)]
        assert command[1] == "tools/perf/run_olmradialblur_generic_production_perf.py"
        assert command[command.index("--geometry") + 1] == geometry


def test_colorkeep_has_hd_and_uhd_production_o2_drivers() -> None:
    module = load_module()
    for geometry in ("hd", "uhd"):
        command = module.COMMANDS[("ColorKeep", geometry)]
        assert command[1] == "tools/perf/run_colorkeep_generic_production_perf.py"
        assert command[command.index("--geometry") + 1] == geometry
    predicate = module.SUPPORT_PREDICATES["ColorKeep"]
    assert "pf8_pf16_pf32" in predicate and "1 <= count <= 100" in predicate
    assert "width <= 3840" in predicate and "height <= 2160" in predicate


def test_smoother_v1_hd_and_uhd_use_explicit_pf8_pf16_production_dimensions() -> None:
    module = load_module()
    for geometry, dimensions in module.GEOMETRIES.items():
        command = module.COMMANDS[("OLMSmoother", geometry)]
        assert "run_olmsmoother_v1_generic_production_perf.py" in command[1]
        assert command[command.index("--depth") + 1] == "both"
        assert int(command[command.index("--width") + 1]) == dimensions[0]
        assert int(command[command.index("--height") + 1]) == dimensions[1]
    predicate = module.SUPPORT_PREDICATES["OLMSmoother"]
    assert "pf8 || pf16" in predicate and "key_off" in predicate
    assert "width <= 3840" in predicate and "height <= 2160" in predicate


def test_lane_and_geometry_can_be_selected_independently(tmp_path) -> None:
    output = tmp_path / "selected.json"
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "--lane", "OLMDistanceGradation",
         "--geometry", "hd", "--output", str(output)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    import json
    rows = json.loads(output.read_text())["results"]
    assert len(rows) == 1
    assert rows[0]["lane"] == "OLMDistanceGradation"
    assert rows[0]["geometry"] == "hd"
    assert rows[0]["status"] == "passed"
