#[test]
fn all_original_verified_hashes() {
    for exe in [
        env!("CARGO_BIN_EXE_golden-color-keep"),
        env!("CARGO_BIN_EXE_golden-olm-blur"),
        env!("CARGO_BIN_EXE_golden-olm-color-key"),
        env!("CARGO_BIN_EXE_golden-olm-directional-blur"),
        env!("CARGO_BIN_EXE_golden-olm-distance-gradation"),
        env!("CARGO_BIN_EXE_golden-olm-kirakira"),
        env!("CARGO_BIN_EXE_golden-olm-radial-blur"),
        env!("CARGO_BIN_EXE_golden-olm-smoother"),
        env!("CARGO_BIN_EXE_golden-olm-smoother2"),
        env!("CARGO_BIN_EXE_golden-olm-toon-dilate"),
    ] {
        assert!(
            std::process::Command::new(exe).status().unwrap().success(),
            "{exe}"
        );
    }
}
