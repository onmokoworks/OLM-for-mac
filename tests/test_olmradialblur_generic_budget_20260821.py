import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def test_generic_radial_budget_bounds_memory_work_and_smart_staging() -> None:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_budget_") as name:
        temp = Path(name)
        cpp, exe = temp / "probe.cpp", temp / "probe"
        cpp.write_text(f'''#include "{source}"
#include <cstdio>
static OLMRadialBlurInfo profile(int w,int h,int strength){{
 OLMRadialBlurInfo q{{}};q.blur_type=1;q.center_x=w/2.0;q.center_y=h/2.0;
 q.outer_strength=strength;q.outer_offset_mode=1;q.inner_offset_mode=1;
 q.repeat_border=TRUE;q.ratio=1;q.quality=5;q.brightness_gain=1;
 q.noise_type=1;q.seed=1;q.thickness=10;q.comp_width=w;q.comp_height=h;return q;
}}
int main(){{size_t classic=0,smart=0;uint64_t work=0;
 auto q=profile(4096,2160,4);
 if(!CheckedRadialGenericBudget(4096,2160,32,q,false,&classic,&work))return 1;
 if(!CheckedRadialGenericBudget(4096,2160,32,q,true,&smart,nullptr))return 2;
 if(!(classic<smart&&smart<=(UINT64_C(1)<<30)&&work<=UINT64_C(350000000)))return 3;
 q.outer_strength=64;q.inner_strength=64;if(CheckedRadialGenericBudget(4096,2160,32,q,true))return 4;
 q=profile(3840,2160,4);if(!CheckedRadialGenericBudget(3840,2160,32,q,true))return 5;
 q=profile(1920,1080,17);if(!CheckedRadialGenericBudget(1920,1080,16,q,true))return 6;
 q=profile(4097,1080,4);if(CheckedRadialGenericBudget(4097,1080,8,q,false))return 7;
 q=profile(4096,2161,4);if(CheckedRadialGenericBudget(4096,2161,8,q,false))return 8;
 q=profile(17,11,4);q.blur_type=2;if(!CheckedRadialGenericBudget(17,11,8,q,true))return 9;
 // The small Quality50 owner is covered by the typed public replay.  At
 // 1024x1024 its Rotation spans cost about ten times the raw UI Strength.
 q=profile(23,13,4);q.blur_type=2;q.quality=50;
 if(!CheckedRadialGenericBudget(23,13,32,q,true))return 10;
 q=profile(1024,1024,4);q.blur_type=2;q.quality=50;
 size_t quality_bytes=0;uint64_t quality_work=0;
 if(CheckedRadialGenericBudget(1024,1024,32,q,true,&quality_bytes,&quality_work))return 11;
 if(!(quality_bytes<(UINT64_C(1)<<30)&&quality_work>UINT64_C(350000000)))return 12;
 std::printf("dci_classic=%zu dci_smart=%zu work=%llu\\n",classic,smart,(unsigned long long)work);
 return 0;}}
''')
        sdk = subprocess.run(
            ["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True
        ).stdout.strip()
        build = subprocess.run([
            "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe),
        ], cwd=ROOT, text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, f"budget probe returned {run.returncode}: {run.stdout} {run.stderr}"
        assert "dci_classic=" in run.stdout and "dci_smart=" in run.stdout
