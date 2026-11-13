#![cfg_attr(not(all(windows, target_arch = "x86_64")), allow(unused))]
#[cfg(not(all(windows, target_arch = "x86_64")))]
compile_error!("witness-host requires Windows x64; use tools/emulation on other platforms");
mod abi;
mod spec;
mod trace;
mod windows;
use serde_json::{json, Value};
use spec::{Kind, Spec};
use std::{
    collections::BTreeMap,
    fs,
    io::Write,
    path::{Path, PathBuf},
};

struct Buffer {
    words: Vec<u128>,
    size: usize,
}
impl Buffer {
    fn new(size: usize, fill: u8) -> Self {
        let mut b = Self {
            words: vec![u128::from_le_bytes([0xcd; 16]); size.div_ceil(16) + 8],
            size,
        };
        b.bytes_mut().fill(fill);
        b
    }
    fn pointer(&self) -> usize {
        self.words.as_ptr() as usize + 64
    }
    fn bytes(&self) -> &[u8] {
        unsafe { std::slice::from_raw_parts(self.pointer() as *const u8, self.size) }
    }
    fn bytes_mut(&mut self) -> &mut [u8] {
        unsafe { std::slice::from_raw_parts_mut(self.pointer() as *mut u8, self.size) }
    }
    fn intact(&self) -> bool {
        let all = unsafe {
            std::slice::from_raw_parts(self.words.as_ptr().cast::<u8>(), self.words.len() * 16)
        };
        all[..64]
            .iter()
            .chain(all[64 + self.size..].iter())
            .all(|&b| b == 0xcd)
    }
}
fn ptr(buffers: &BTreeMap<String, Buffer>, name: &str, offset: usize) -> Result<u64, String> {
    let b = buffers
        .get(name)
        .ok_or_else(|| format!("unknown buffer {name}"))?;
    if offset > b.size {
        return Err("buffer offset beyond end".into());
    }
    Ok((b.pointer() + offset) as u64)
}
fn argument(a: &spec::Argument, buffers: &BTreeMap<String, Buffer>) -> Result<u64, String> {
    if [a.value.is_some(), a.bits.is_some(), a.buffer.is_some()]
        .iter()
        .filter(|&&b| b)
        .count()
        != 1
    {
        return Err("argument requires exactly one of value, bits, buffer".into());
    }
    if matches!(a.kind, Kind::Void) {
        return Err("void argument".into());
    }
    if let Some(name) = &a.buffer {
        if !matches!(a.kind, Kind::Ptr) {
            return Err("buffer requires ptr type".into());
        }
        return ptr(buffers, name, a.offset);
    }
    if let Some(bits) = &a.bits {
        let word = spec::word(&Value::String(bits.clone()))?;
        if a.kind.width() < 8 && word >> (a.kind.width() * 8) != 0 {
            return Err("argument bits exceed type width".into());
        }
        return Ok(word);
    }
    let value = a.value.as_ref().unwrap();
    Ok(match a.kind {
        Kind::F32 => (value
            .as_f64()
            .ok_or("f32 value must be numeric; use bits for NaN")? as f32)
            .to_bits() as u64,
        Kind::F64 => value
            .as_f64()
            .ok_or("f64 value must be numeric; use bits for NaN")?
            .to_bits(),
        _ => spec::word(value)?,
    })
}
unsafe fn fma(mode: &str) -> Result<Value, String> {
    let system = PathBuf::from(std::env::var_os("SystemRoot").ok_or("missing SystemRoot")?)
        .join("System32/ucrtbase.dll");
    let module = windows::load(&system)?;
    let get: unsafe extern "C" fn() -> i32 =
        std::mem::transmute(windows::proc(module, "_get_FMA3_enable")?);
    let before = get();
    if mode != "auto" {
        let desired = match mode {
            "fma" => 1,
            "no-fma" => 0,
            _ => return Err("fma must be auto, fma, or no-fma".into()),
        };
        let set: unsafe extern "C" fn(i32) -> i32 =
            std::mem::transmute(windows::proc(module, "_set_FMA3_enable")?);
        set(desired);
        if get() != desired {
            return Err("requested UCRT FMA lane unavailable".into());
        }
    }
    let mut mxcsr = 0u32;
    std::arch::asm!("stmxcsr [{0}]",in(reg) &mut mxcsr,options(nostack,preserves_flags));
    Ok(
        json!({"ucrt_path":windows::module_path(module),"before":before,"effective":get(),"requested":mode,
        "cpu_fma":std::is_x86_feature_detected!("fma"),"mxcsr":format!("0x{mxcsr:08x}")}),
    )
}
fn execute(spec_path: &Path, out: &Path) -> Result<(), String> {
    let s: Spec = serde_json::from_slice(&fs::read(spec_path).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    if s.schema_version != 1 || s.calls.is_empty() || s.calls.len() > 100000 {
        return Err("requires schema_version 1 and 1..100000 calls".into());
    }
    if !s.module.is_absolute() {
        return Err("module path must be absolute".into());
    }
    let mut buffers = BTreeMap::new();
    let mut total = 0usize;
    for (name, b) in &s.buffers {
        if name.is_empty()
            || !name
                .bytes()
                .all(|c| c.is_ascii_alphanumeric() || c == b'_' || c == b'-')
        {
            return Err("buffer name requires ASCII alphanumeric, underscore or hyphen".into());
        }
        total = total.checked_add(b.size).ok_or("buffer size overflow")?;
        if total > 256 * 1024 * 1024 {
            return Err("buffer budget exceeds 256 MiB".into());
        }
        let mut buffer = Buffer::new(b.size, b.fill);
        if b.file.is_some() && b.hex.is_some() {
            return Err("choose buffer file or hex".into());
        }
        let data = if let Some(p) = &b.file {
            fs::read(p).map_err(|e| e.to_string())?
        } else if let Some(h) = &b.hex {
            spec::unhex(h)?
        } else {
            Vec::new()
        };
        if data.len() > b.size {
            return Err(format!("{name}: initial bytes exceed size"));
        }
        buffer.bytes_mut()[..data.len()].copy_from_slice(&data);
        buffers.insert(name.clone(), buffer);
    }
    for (name, b) in &s.buffers {
        for reloc in &b.pointers {
            let address = ptr(&buffers, &reloc.buffer, reloc.addend)?;
            let dest = buffers.get_mut(name).unwrap().bytes_mut();
            let end = reloc.offset.checked_add(8).ok_or("relocation overflow")?;
            dest.get_mut(reloc.offset..end)
                .ok_or("relocation outside struct")?
                .copy_from_slice(&address.to_le_bytes());
        }
    }
    let module = unsafe { windows::load(&s.module)? };
    let image = unsafe { trace::Image::new(module)? };
    let lane = unsafe { fma(&s.fma)? };
    let installed = unsafe { trace::install(&image, &s.trace, &out.join("trace.jsonl"))? };
    let mut results = Vec::new();
    let mut journal = fs::File::create(out.join("calls.jsonl")).map_err(|e| e.to_string())?;
    for (index, c) in s.calls.iter().enumerate() {
        if c.args.len() > 32 {
            return Err("maximum 32 scalar args".into());
        }
        let rva = spec::word(&c.rva)? as usize;
        let target = image.address(rva, 1)?;
        let mut call = abi::Call::new(target);
        for (i, a) in c.args.iter().enumerate() {
            call.slots[i] = argument(a, &buffers)?;
        }
        trace::set_call(index);
        let result = unsafe { call.run() };
        let mut dumps = BTreeMap::new();
        for (name, b) in &buffers {
            if !b.intact() {
                return Err(format!("call {index} overwrote {name} redzone"));
            }
            let filename = format!("call-{index:06}-{name}.bin");
            fs::write(out.join(&filename), b.bytes()).map_err(|e| e.to_string())?;
            dumps.insert(name, filename);
        }
        let row = json!({"index":index,"label":c.label,"rva":format!("0x{rva:x}"),"return":spec::result(result,c.returns),"buffers":dumps});
        writeln!(journal, "{row}").map_err(|e| e.to_string())?;
        journal.flush().map_err(|e| e.to_string())?;
        results.push(row);
    }
    let report = json!({"schema_version":1,"module":s.module,"loaded_base":format!("0x{module:x}"),
        "fma":lane,"imports_patched":installed,"trace":trace::summary(),"calls":results});
    fs::write(
        out.join("result.json"),
        serde_json::to_vec_pretty(&report).unwrap(),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}
fn main() {
    let a: Vec<_> = std::env::args_os().collect();
    unsafe {
        windows::SetErrorMode(0x1 | 0x2 | 0x8000);
    }
    let result = (|| {
        if a.len() != 4 || a[1] != "--child" || std::env::var_os("AEX_WITNESS_CHILD").is_none() {
            return Err(
                "Use witness.py; witness-host --child SPEC OUTPUT is an isolated worker".into(),
            );
        }
        let mut in_job = 0;
        if unsafe {
            windows::IsProcessInJob(
                windows::GetCurrentProcess(),
                std::ptr::null_mut(),
                &mut in_job,
            )
        } == 0
            || in_job == 0
        {
            return Err("worker must be in the front-end's private Job Object".into());
        }
        execute(Path::new(&a[2]), Path::new(&a[3]))
    })();
    if let Err(e) = result {
        eprintln!("{e}");
        std::process::exit(2);
    }
}
