use pipl::*;
fn main() {
    let root = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
    let mut reference = cc::Build::new();
    reference
        .cpp(true)
        .include(&root)
        .file("tests/reference.cpp");
    if std::env::var("CARGO_CFG_TARGET_ENV").as_deref() == Ok("msvc") {
        let installed = std::path::PathBuf::from("C:/Program Files/LLVM/bin/clang-cl.exe");
        reference.compiler(std::env::var("CXX").unwrap_or_else(|_| {
            if installed.exists() {
                installed.display().to_string()
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
    reference.flag_if_supported("-Wno-unused-function");
    reference.compile("olm_colorkey_cpp_reference");
    println!("cargo:rerun-if-changed=tests/reference.cpp");
    for f in ["ColorMath.inc", "Distance.inc"] {
        println!(
            "cargo:rerun-if-changed={}",
            root.join("mac/OLMColorKey").join(f).display()
        );
    }
    let target = std::env::var("CARGO_CFG_TARGET_OS").unwrap();
    let mut props = vec![
        Property::Kind(PIPLType::AEEffect),
        Property::Name("OLM Color Key"),
        Property::Category("OLM Plug-ins"),
        Property::AE_PiPL_Version { major: 2, minor: 0 },
        Property::AE_Effect_Spec_Version {
            major: 13,
            minor: 28,
        },
        Property::AE_Effect_Version {
            version: 2,
            subversion: 3,
            bugversion: 3,
            stage: Stage::Develop,
            build: 0,
        },
        Property::AE_Effect_Info_Flags(0),
        Property::AE_Effect_Global_OutFlags(OutFlags::from_bits_retain(0x02000440)),
        Property::AE_Effect_Global_OutFlags_2(OutFlags2::from_bits_retain(0x08001400)),
        Property::AE_Effect_Match_Name("OLM Color Key"),
        Property::AE_Reserved_Info(0),
    ];
    if target == "windows" {
        props.insert(3, Property::CodeWin64X86("entry_point"));
    }
    if target == "macos" {
        props.insert(3, Property::CodeMacIntel64("EffectMain"));
        props.insert(4, Property::CodeMacARM64("EffectMain"));
        props.push(Property::AE_Effect_Support_URL("https://olm.co.jp/"));
    }
    if target == "windows" {
        // The pinned pipl RC string emitter is code-page sensitive on Japanese
        // Windows (e.g. version byte 0x88 becomes two bytes). Embed binary bytes.
        let mut bytes = pipl::build_pipl(props).unwrap();
        // Original Windows PiPL declares eINF as a 2-byte short plus alignment.
        // The pinned serializer declares four bytes; correct only its size field.
        let mut at = 10;
        while at < bytes.len() {
            let len = u32::from_le_bytes(bytes[at + 12..at + 16].try_into().unwrap()) as usize;
            if &bytes[at + 4..at + 8] == b"FNIe" {
                bytes[at + 12..at + 16].copy_from_slice(&2u32.to_le_bytes());
            }
            at += 16 + (len + 3) / 4 * 4;
        }
        let path =
            std::path::PathBuf::from(std::env::var_os("OUT_DIR").unwrap()).join("effect.pipl");
        std::fs::write(&path, bytes).unwrap();
        winres::WindowsResource::new()
            .append_rc_content(&format!(
                "16000 PiPL DISCARDABLE \"{}\"",
                path.display().to_string().replace('\\', "/")
            ))
            .compile()
            .unwrap();
    } else {
        pipl::plugin_build(props);
    }
}
