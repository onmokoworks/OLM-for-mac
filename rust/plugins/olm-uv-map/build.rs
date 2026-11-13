// Raw resources avoid the code-page-sensitive PiPL string serializer.
fn main() {
    println!("cargo:rerun-if-changed=resources");
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows") {
        winres::WindowsResource::new()
            .append_rc_content(RC)
            .compile()
            .unwrap();
    } else if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("macos") {
        use pipl::*;
        pipl::plugin_build(vec![
            Property::Kind(PIPLType::AEEffect),
            Property::Name("OLM UV Map"),
            Property::Category("OLM Plug-ins"),
            Property::CodeMacIntel64("EffectMain"),
            Property::CodeMacARM64("EffectMain"),
            Property::AE_PiPL_Version { major: 2, minor: 0 },
            Property::AE_Effect_Spec_Version {
                major: 13,
                minor: 28,
            },
            Property::AE_Effect_Version {
                version: 1,
                subversion: 1,
                bugversion: 1,
                stage: Stage::Develop,
                build: 0,
            },
            Property::AE_Effect_Info_Flags(0),
            Property::AE_Effect_Global_OutFlags(OutFlags::from_bits_retain(0x02000040)),
            Property::AE_Effect_Global_OutFlags_2(OutFlags2::from_bits_retain(0x18001400)),
            Property::AE_Effect_Match_Name("OLM UV Map"),
            Property::AE_Reserved_Info(0),
        ]);
    }
}
const RC: &str = "LANGUAGE 9, 1\n16000 PIPL DISCARDABLE \"resources/pipl-0.bin\"";
