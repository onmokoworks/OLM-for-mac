use std::path::PathBuf;
fn main() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
    let mut b = cc::Build::new();
    // The reference uses GNU C extensions (including unsigned __int128).
    if std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("msvc") {
        let installed = PathBuf::from("C:/Program Files/LLVM/bin/clang-cl.exe");
        b.compiler(std::env::var("CC").unwrap_or_else(|_| {
            if installed.exists() {
                installed.display().to_string()
            } else {
                "clang-cl".into()
            }
        }));
        b.flag("/clang:-ffp-contract=off")
            .flag("/clang:-fno-fast-math");
    } else {
        b.flag("-ffp-contract=off").flag("-fno-fast-math");
    }
    b.include(root.join("ucrtmath/include"));
    for file in [
        "src/expf.c",
        "src/powf.c",
        "src/atan2f.c",
        "src/tables.c",
        "ms/float.c",
        "ms/double.c",
        "ms/pow.c",
    ] {
        b.file(root.join("ucrtmath").join(file));
    }
    println!("cargo:rerun-if-changed={}", root.join("ucrtmath").display());
    b.compile("olm_ucrtmath");
    let mut r = cc::Build::new();
    r.cpp(true).include(&root).file("reference.cpp");
    if std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("msvc") {
        r.compiler(b.get_compiler().path())
            .flag("/std:c++17")
            .flag("/clang:-ffp-contract=off")
            .flag("/clang:-fno-fast-math");
    } else {
        r.flag("-std=c++17")
            .flag("-ffp-contract=off")
            .flag("-fno-fast-math");
    }
    println!("cargo:rerun-if-changed=reference.cpp");
    println!(
        "cargo:rerun-if-changed={}",
        root.join("core/olm_exact_math.h").display()
    );
    println!(
        "cargo:rerun-if-changed={}",
        root.join("core/x86_float.h").display()
    );
    r.compile("olm_cpp_probe");
}
