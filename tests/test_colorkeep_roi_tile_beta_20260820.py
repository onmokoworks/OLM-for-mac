from __future__ import annotations

import importlib.util
import inspect
import hashlib
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
    expected_active = {}
    for depth in harness.EXPECTED:
        if depth == "PF8":
            pack = bytes
        elif depth == "PF16":
            pack = lambda value: struct.pack("<4H", *((x * 32768 + 127) // 255 for x in value))
        else:
            pack = lambda value: struct.pack("<4f", *(x / 255 for x in value))
        active = b"".join(pack(pixel) for pixel in pixels)
        expected = b"".join(pack(pixel if pixel in harness.PALETTE8 else (0, *pixel[1:]))
                            for pixel in pixels)
        # Bind the flag-mutation comparison below to the retained actual-AEX
        # input/output hashes, independently of the current Mac worker.
        assert hashlib.sha256(active).hexdigest() == harness.EXPECTED[depth]["input_active"]
        assert hashlib.sha256(expected).hexdigest() == harness.EXPECTED[depth]["output_active"]
        expected_active[depth] = expected
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
    # P02a delegates Smart geometry to the host. The historical closure probe
    # used a fixed 4x3 iterator and counted only refusals, silently accepting
    # unexamined successful mutations. Check every scenario explicitly instead.
    source = source.replace("const PF_Rect*,void*r,F f", "const PF_Rect*area,void*r,F f")
    source = source.replace(
        "if(a!=0||b!=3)phase_bad=1;",
        "if(gsmart?(a!=0||b!=o->extent_hint.bottom-o->extent_hint.top||!area||"
        "std::memcmp(area,&o->extent_hint,sizeof(*area))):(a!=0||b!=o->height||area))phase_bad=1;",
    ).replace("for(int y=0;y<3;y++)for(int x=0;x<4;x++)",
              "for(int y=0;y<i->height&&y<o->height;y++)for(int x=0;x<i->width&&x<o->width;x++)")
    source = source.replace("co!=101||ci", "co!=gcount+1||ci")
    source = source.replace(
        "if(co!=101||cc!=100)phase_bad=1;",
        "if(co!=(fmt_mut?1:fail_checkout?51:gcount+1)||"
        "cc!=(fmt_mut||fail_checkout?0:fail_color?51:gcount))phase_bad=1;",
    )
    # Validate padding against the negotiated world, including changed strides.
    begin = source.index("bool pads=true;")
    end = source.index("bool unchanged=", begin)
    source = source[:begin] + (
        "bool pads=true;for(int n=0;n<osz+32;n++){bool active=false;"
        "for(int y=0;y<ow.height;y++)active|=n>=y*ow.rowbytes&&n<y*ow.rowbytes+ow.width*(int)sizeof(P);"
        "if(!active)pads&=dst[n]==0xee;}"
    ) + source[end:]
    source = source.replace(
        'array("raw32", inputs["PF32"])',
        'array("raw32", inputs["PF32"]) + array("expected8", expected_active["PF8"])'
        ' + array("expected16", expected_active["PF16"]) + array("expected32", expected_active["PF32"])',
    )
    begin = source.index("if(mutation){bool noout=true;")
    end = source.index("bool life=smart?", begin)
    source = source[:begin] + r'''if(mutation){
        const bool overlap=mutation==27||mutation==28;
        const bool format=mutation==35||mutation==36;
        const bool classic_bad=!smart&&(mutation==19||mutation==20||mutation==25||mutation==37);
        const bool callback_bad=(smart&&mutation>=29&&mutation<=31)||mutation==32;
        const bool refused=overlap||format||classic_bad||callback_bad;
        int expected_co=0,expected_cc=0,expected_ci=0;
        if(smart&&!overlap){expected_co=format?1:mutation==29?51:gcount+1;
            expected_cc=format||mutation==29?0:mutation==30?51:gcount;
            expected_ci=expected_co-(mutation==29?1:0);}
        if(!smart&&(!refused||mutation==32))expected_cc=gcount;
        bool life=co==expected_co&&cc==expected_cc&&ci==expected_ci&&
            li==(smart?1:0)&&lh==(smart?1:0)&&oh==(smart?1:0)&&ph==(smart?1:0);
        bool noout=true;for(int n=0;n<osz+32;n++)noout&=dst[n]==0xee;
        int expected_rc=!refused?0:callback_bad?mutation==29?77:mutation==30?79:mutation==31?78:81:PF_Err_BAD_CALLBACK_PARAM;
        bool good=rc==expected_rc&&life&&pads&&unchanged&&request_unchanged&&!phase_bad&&
            ih==((!refused||mutation==32)&&(smart||mutation!=21)?1:0)&&(!refused||noout);
        if(!refused&&!(mutation>=3&&mutation<=5)&&mutation!=22&&mutation!=23){
            const unsigned char* expected=depth==8?expected8:depth==16?expected16:expected32;
            for(int y=0;y<iw.height&&y<ow.height;y++)for(int x=0;x<iw.width&&x<ow.width;x++){
                unsigned char pixel[sizeof(P)];std::memcpy(pixel,expected+(y*W+x)*sizeof(P),sizeof(P));
                if(mutation==1&&(y*W+x)%6==4)std::memset(pixel,0,sizeof(P)/4);
                good&=std::memcmp(dst+y*ow.rowbytes+x*sizeof(P),pixel,sizeof(P))==0;
            }
        }
        if(!good)std::fprintf(stderr,"mutation=%d smart=%d depth=%d rc=%d expected=%d life=%d pads=%d phase=%d ih=%d co=%d cc=%d ci=%d li=%d\n",mutation,smart,depth,rc,expected_rc,life,pads,phase_bad,ih,co,cc,ci,li);
        return good;
    }''' + source[end:]
    source = source.replace("return ok==49?0:3;", "return ok==141?0:3;")
    # Smart now calls iterate once; Classic retains the direct mapped loop.
    source = source.replace("||ih!=0)", "||ih!=(smart?1:0))")
    namespace = dict(harness.__dict__, expected_active=expected_active)
    exec(source, namespace)
    observed, _ = namespace["roi_probe"](binary, inputs)
    # This host mock iterates the overlapping local world dimensions. Classic
    # maps the source origin itself. Assert each route against retained AEX
    # typed pixel bytes, rather than assuming these different requests coincide.
    offset = 0
    for smart, depth in ((False, "PF8"), (False, "PF16"), (True, "PF8"),
                         (True, "PF16"), (True, "PF32")):
        size = {"PF8": 4, "PF16": 8, "PF32": 16}[depth]
        expected = bytearray(b"\xee" * (12 * size))
        for y in range(2):
            for x in range(3):
                src = ((y if smart else y + 1) * 4 + (x if smart else x + 1)) * size
                dst = (y * 4 + x) * size
                expected[dst:dst + size] = expected_active[depth][src:src + size]
        assert observed[offset:offset + len(expected)] == expected, (smart, depth)
        offset += len(expected)
    assert offset == len(observed)
