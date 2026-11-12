fn main() {
    let mut bytes = vec![1, 0, 0, 0, 0, 0, 12, 0, 0, 0];
    let props: &[(&[u8; 4], &[u8])] = &[
        (b"kind", b"TKFe"),
        (b"name", b"\x10Scaffold Capture"),
        (b"catg", b"\x08Scaffold"),
        (b"8664", b"EffectMain\0"),
        (b"ePVR", &[2, 0, 0, 0]),
        (b"eSVR", &[13, 0, 28, 0]),
        (b"eVER", &[0, 0, 0, 0]),
        (b"eINF", &[0, 0]),
        (b"eGLO", &[0x40, 0, 0, 2]),
        (b"eGL2", &[0, 0x14, 0, 8]),
        (b"eMNA", b"\x10Scaffold Capture"),
        (b"aeFL", &[0, 0, 0, 0]),
    ];
    for (key, data) in props {
        bytes.extend(b"MIB8");
        bytes.extend(key.iter().rev());
        bytes.extend(0u32.to_le_bytes());
        bytes.extend((data.len() as u32).to_le_bytes());
        bytes.extend(*data);
        bytes.extend(vec![0; (4 - data.len() % 4) % 4]);
    }
    let path = std::path::PathBuf::from(std::env::var_os("OUT_DIR").unwrap()).join("probe.pipl");
    std::fs::write(&path, bytes).unwrap();
    winres::WindowsResource::new()
        .append_rc_content(&format!(
            "16000 PiPL DISCARDABLE \"{}\"",
            path.display().to_string().replace('\\', "/")
        ))
        .compile()
        .unwrap();
}
