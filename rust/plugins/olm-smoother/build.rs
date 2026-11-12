use pipl::*;
fn main() {
    reference();
    let target = std::env::var("CARGO_CFG_TARGET_OS").unwrap();
    let mut props = vec![
        Property::Kind(PIPLType::AEEffect),
        Property::Name("OLM Smoother"),
        Property::Category("OLM Plug-ins"),
        Property::AE_PiPL_Version { major: 2, minor: 0 },
        Property::AE_Effect_Spec_Version {
            major: 13,
            minor: 28,
        },
        Property::AE_Effect_Version {
            version: 1,
            subversion: 2,
            bugversion: 1,
            stage: Stage::Develop,
            build: 0,
        },
        Property::AE_Effect_Info_Flags(0),
        Property::AE_Effect_Global_OutFlags(OutFlags::from_bits_retain(0x02000040)),
        Property::AE_Effect_Global_OutFlags_2(OutFlags2::from_bits_retain(0x08000000)),
        Property::AE_Effect_Match_Name("OLM Smoother"),
        Property::AE_Reserved_Info(0),
    ];
    if target == "windows" {
        props.insert(3, Property::CodeWin64X86("entryPointFunc"));
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

// Like the pilots, compile an archive whose symbols are referenced only by
// cfg(test). Production code calls exclusively the translated Rust kernels.
fn reference() {
    use std::{fs,path::PathBuf};
    let root=PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..");
    let src=root.join("mac/OLMSmoother/Mac");
    let out=PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
    let port=fs::read_to_string(src.join("OLMSmoother_port.cpp")).unwrap().replace("\r\n","\n");
    let constants=&port[port.find("static const float DAT_").unwrap()..port.find("// ============================================================================\n// Plugin lifecycle").unwrap()];
    fs::write(out.join("reference_constants.hpp"),constants).unwrap();
    let render=fs::read_to_string(src.join("OLMSmoother_render.inc")).unwrap();
    fs::write(out.join("reference_render.hpp"),&render[..render.find("// 32-bit float").unwrap()]).unwrap();
    let mut b=cc::Build::new();
    b.cpp(true).include(&src).include(&out).file("tests/reference.cpp");
    if std::env::var("CARGO_CFG_TARGET_ENV").as_deref()==Ok("msvc") {
        b.compiler(std::env::var("CXX").unwrap_or_else(|_|"C:/Program Files/LLVM/bin/clang-cl.exe".into()));
        b.flag("/std:c++17").flag("/clang:-ffp-contract=off").flag("/clang:-fno-fast-math");
    } else {b.flag("-std=c++17").flag("-ffp-contract=off").flag("-fno-fast-math");}
    b.warnings(false).compile("olm_smoother_cpp_reference");
    println!("cargo:rerun-if-changed=tests/reference.cpp");
    for file in fs::read_dir(src).unwrap(){let p=file.unwrap().path();if matches!(p.extension().and_then(|s|s.to_str()),Some("inc"|"cpp")){println!("cargo:rerun-if-changed={}",p.display());}}
}
