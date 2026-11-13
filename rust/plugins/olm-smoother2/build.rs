mod pipl_build;
use std::{env, fs, path::PathBuf};

fn main() {
    pipl_build::embed();
    let crate_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let root = crate_dir.join("../../..");
    let source = root.join("mac/OLMSmoother2/Mac");
    let out = PathBuf::from(env::var_os("OUT_DIR").unwrap());
    // Extract unchanged gamma stages and the complete per-pixel orchestrator.
    // Boundary markers fail closed on source drift.
    let gamma_path = source.join("OLMSmoother2_gamma_composite.inc");
    let gamma = fs::read_to_string(&gamma_path).unwrap();
    let prefix = gamma
        .split_once("// Output-path sRGB encoder — LITERAL PORT")
        .unwrap()
        .0;
    let literal = gamma
        .split_once("static inline double win_FUN_180004d70_literal(double v)\n{")
        .or_else(|| {
            gamma.split_once("static inline double win_FUN_180004d70_literal(double v)\r\n{")
        })
        .unwrap()
        .1;
    let literal = literal.split_once('}').unwrap().0;
    fs::write(
        out.join("gamma_reference.inc"),
        format!(
            "{prefix}\nstatic inline double win_FUN_180004d70_literal(double v) {{{literal}}}\n"
        ),
    )
    .unwrap();
    println!("cargo:rerun-if-changed={}", gamma_path.display());
    let port_path = source.join("OLMSmoother2_port.cpp");
    let port = fs::read_to_string(&port_path).unwrap();
    let metric = port
        .split_once("const float WIN_LUMA_R")
        .unwrap()
        .1
        .split_once("// Class-plane threshold =")
        .unwrap()
        .0;
    let class_loop = port
        .split_once("std::vector<uint8_t> class_plane((size_t)w * (size_t)h * 4, 0);")
        .unwrap()
        .1;
    let class_loop = class_loop
        .split_once("if (g_olmsmoother2_trace_x >= 0 && g_olmsmoother2_trace_y >= 0)")
        .unwrap()
        .0;
    // Explicit 2026-11-12 delta, grounded at new AEX c110. The surrounding
    // C++ geometry is unchanged; original-only tests are no longer the authority.
    assert!(class_loop.contains("x + 1 < w - 1"));
    let class_loop = class_loop.replace("x + 1 < w - 1", "x + 1 < w");
    fs::write(out.join("class_reference.inc"),format!(
        "extern \"C\" void sm2_ref_class_plane(const FPix *class_base, int w, int h, int range, uint8_t *out) {{\nconst float WIN_LUMA_R{metric}\nconst float threshold=(float)range*0.01f+WIN_THRESH_BIAS;\nstd::vector<uint8_t> class_plane((size_t)w*h*4,0);\n{class_loop}\nstd::memcpy(out,class_plane.data(),class_plane.size());\n}}\n"
    )).unwrap();
    println!("cargo:rerun-if-changed={}", port_path.display());
    for (name, header) in [
        ("decode", "OLMSmoother2_decode_lut_10000.h"),
        ("encode", "OLMSmoother2_encode_lut_10000.h"),
    ] {
        let path = source.join(header);
        println!("cargo:rerun-if-changed={}", path.display());
        let text = fs::read_to_string(path).unwrap();
        let body = text.split_once('{').unwrap().1.split_once('}').unwrap().0;
        let bytes: Vec<u8> = body
            .split(',')
            .filter_map(|s| {
                let s = s.trim();
                if s.is_empty() {
                    None
                } else {
                    Some(u8::from_str_radix(s.strip_prefix("0x").unwrap(), 16).unwrap())
                }
            })
            .collect();
        assert_eq!(bytes.len(), 40000);
        fs::write(out.join(format!("{name}.bin")), bytes).unwrap();
    }
    // Compile unchanged source text for test-only calls, as in the pilot.
    // No reference symbol is called by the production library.
    let mut reference = cc::Build::new();
    reference
        .cpp(true)
        .define("_CRT_SECURE_NO_WARNINGS", None)
        .include(&root)
        .include(&source)
        .include(&out)
        .file(crate_dir.join("tests/reference.cpp"));
    if env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("msvc") {
        let clang = PathBuf::from("C:/Program Files/LLVM/bin/clang-cl.exe");
        reference.compiler(env::var("CXX").unwrap_or_else(|_| {
            if clang.exists() {
                clang.display().to_string()
            } else {
                "clang-cl".into()
            }
        }));
        reference
            .flag("/std:c++17")
            .flag("/clang:-ffp-contract=off")
            .flag("/clang:-fno-fast-math");
    } else {
        reference
            .flag("-std=c++17")
            .flag("-ffp-contract=off")
            .flag("-fno-fast-math");
    }
    reference
        .flag_if_supported("-Wno-unused-function")
        .flag_if_supported("-Wno-unused-variable");
    reference.compile("olm_smoother2_cpp_reference");
    println!(
        "cargo:rerun-if-changed={}",
        crate_dir.join("tests/reference.cpp").display()
    );
    println!(
        "cargo:rerun-if-changed={}",
        root.join("cli/OLMSmoother2/shim/OLMSmoother2.h").display()
    );
    for f in [
        "constants",
        "frame_setup",
        "classification",
        "polygon_scan",
        "polygon_weights",
        "cardinal_leaves",
        "corner_samples",
        "polygon_dispatch",
    ] {
        println!(
            "cargo:rerun-if-changed={}",
            source.join(format!("OLMSmoother2_{f}.inc")).display()
        );
    }
    println!(
        "cargo:rerun-if-changed={}",
        crate_dir.join("tests/leaf_reference.inc").display()
    );
}
