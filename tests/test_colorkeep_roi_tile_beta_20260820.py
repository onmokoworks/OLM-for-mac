from __future__ import annotations

import importlib.util
import inspect
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
GENERIC_TEST = ROOT / "tests/test_colorkeep_generic_beta_20260820.py"
EFFECTMAIN_HARNESS = ROOT / "tools/emulation/test_colorkeep_nine_color_public_closure_20260813.py"


def load_generic_test():
    spec = importlib.util.spec_from_file_location("colorkeep_generic_test", GENERIC_TEST)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_roi_tile_admission_contract_is_one_to_one() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "output->origin_x < input->origin_x" in source
    assert "output->origin_x + output->width" in source
    assert "input->extent_hint.left != output->extent_hint.left" not in source
    assert "ColorKeepIsOneToOne(in_data, output)" in source
    assert "downsample_x.num == 1 && in_data->downsample_x.den == 1" in source
    assert "in_data->output_origin_x == output->origin_x" in source


def test_production_typed_roi_tile_matrix() -> None:
    # The shared production-source probe compiles ColorKeep.cpp with the real SDK,
    # then exercises nonzero positive/negative origins at PF8/PF16/PF32, distinct
    # strides, padding canaries, malformed coordinate pairs, and 1:1 admission.
    load_generic_test().test_generic_worlds_counts_and_typed_workers()


def test_exported_effectmain_nonzero_origin_classic_and_smart() -> None:
    spec = importlib.util.spec_from_file_location("ck_effectmain_harness", EFFECTMAIN_HARNESS)
    assert spec and spec.loader
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    selected = (0, 3, 4, 7, 8)
    argb = tuple(harness.PALETTE8[i] for i in selected) + ((32, 222, 32, 96),)
    pixels = (argb * 2)[:12]
    inputs = {}
    for depth in harness.EXPECTED:
        if depth == "PF8":
            pack = bytes
        elif depth == "PF16":
            pack = lambda value: struct.pack("<4H", *((x * 32768 + 127) // 255 for x in value))
        else:
            pack = lambda value: struct.pack("<4f", *(x / 255 for x in value))
        active = b"".join(pack(pixel) for pixel in pixels)
        pixel_size = len(active) // 12
        inputs[depth] = b"".join(
            active[y * 4 * pixel_size:(y + 1) * 4 * pixel_size] + b"\xcc" * 8
            for y in range(3)
        )
    binary, _ = harness.build_candidate()

    source = inspect.getsource(harness.probe).replace("def probe(", "def roi_probe(", 1)
    source = source.replace(
        "const int rb=W*sizeof(P)+PAD,sz=rb*H;alignas(P)unsigned char src[sz+32],dst[sz+32];",
        "const int rb=W*sizeof(P)+PAD,orb=rb+16,sz=rb*H,osz=orb*H;"
        "alignas(P)unsigned char src[sz+32],dst[osz+32];",
    ).replace(
        "ow.rowbytes=rb;ow.width=W;",
        "ow.rowbytes=orb;ow.width=W;",
    ).replace(
        "bool pads=true;for(int y=0;y<H;y++)for(int x=W*sizeof(P);x<rb;x++)pads&=src[y*rb+x]==raw[y*rb+x]&&dst[y*rb+x]==0xee;",
        "bool pads=true;for(int y=0;y<H;y++){for(int x=W*sizeof(P);x<rb;x++)"
        "pads&=src[y*rb+x]==raw[y*rb+x];for(int x=W*sizeof(P);x<orb;x++)"
        "pads&=dst[y*orb+x]==0xee;}",
    ).replace(
        "for(int i=0;i<sz;i++)noout&=dst[i]==0xee;",
        "for(int i=0;i<osz;i++)noout&=dst[i]==0xee;",
    ).replace(
        "std::fwrite(dst,1,sz,stdout);",
        "for(int y=0;y<H;y++)std::fwrite(dst+y*orb,1,W*sizeof(P),stdout);",
    ).replace(
        "iw.extent_hint={0,0,W,H};ow.data",
        "iw.origin_x=ow.origin_x=-17;iw.origin_y=ow.origin_y=23;"
        "iw.extent_hint={-17,23,-17+W,23+H};ow.data",
    ).replace(
        "ow.extent_hint={0,0,W,H};if(depth!=8)",
        "ow.extent_hint={-17,23,-17+W,23+H};if(depth!=8)",
    ).replace(
        "PF_InData in{};PF_OutData out{};",
        "PF_InData in{};in.output_origin_x=mutation?-17:-16;in.output_origin_y=mutation?23:24;"
        "in.downsample_x={1,1};in.downsample_y={1,1};"
        "if(mutation==19)in.downsample_x.num=2;PF_OutData out{};",
    ).replace(
        "gcount=mutation==1?8:mutation==2?10:9;",
        "gcount=mutation==1?8:mutation==2?10:100;",
    ).replace(
        "if(mutation==28)ow.data=(PF_PixelPtr)(src+1);std::memcpy(before,src,sz);",
        "if(mutation==28)ow.data=(PF_PixelPtr)(src+1);"
        "if(!mutation){ow.width=3;ow.height=2;ow.origin_x=-16;ow.origin_y=24;"
        "ow.extent_hint={700,800,701,801};}std::memcpy(before,src,sz);",
    ).replace(
        '"(co==0&&cc==9&&ci==0&&lh==0&&oh==0)"',
        '"(co==0&&cc==100&&ci==0&&lh==0&&oh==0)"',
    ).replace(
        "ci==101):(co==0&&cc==100",
        "ci==101&&li==1):(co==0&&cc==100",
    ).replace(
        "ph==1&&lh==1&&oh==1&&li==0&&co==101",
        "ph==1&&lh==1&&oh==1&&li==1&&co==101",
    ).replace(
        "return ok==136?0:3;",
        "return ok==49?0:3;",
    ).replace(
        "m==9||m==19)",
        "m==9)",
    ).replace(
        "18,20,21,22",
        "18,19,20,21,22",
    ).replace(
        "if(rc||!life||phase_bad||!pads||!unchanged||!request_unchanged||ih!=1)return false;",
        "if(rc||!life||phase_bad||!pads||!unchanged||!request_unchanged||ih!=0){"
        "std::fprintf(stderr,\"fail smart=%d depth=%d rc=%d life=%d phase=%d pads=%d unchanged=%d req=%d ih=%d co=%d cc=%d ci=%d li=%d\\n\","
        "smart,depth,rc,life,phase_bad,pads,unchanged,request_unchanged,ih,co,cc,ci,li);return false;}",
    )
    namespace = dict(harness.__dict__)
    exec(source, namespace)
    observed, _ = namespace["roi_probe"](binary, inputs)
    # Classic PF8/PF16 and Smart PF8/PF16/PF32 must agree at active pixels.
    pf8_classic = observed[0:48]
    pf16_classic = observed[48:144]
    pf8_smart = observed[144:192]
    pf16_smart = observed[192:288]
    pf32_smart = observed[288:480]
    assert len(pf32_smart) == 192
    assert pf8_classic == pf8_smart
    assert pf16_classic == pf16_smart
