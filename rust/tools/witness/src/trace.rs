//! Patches only the explicitly loaded child's normal import table.
use crate::{
    abi::{witness_trace_entry, Call, TraceFrame},
    spec::{self, ImportSpec, Kind, TraceSpec},
    windows::*,
};
use serde_json::{json, Value};
use std::{
    fs::File,
    io::Write,
    path::Path,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Mutex, OnceLock,
    },
};

struct Hook {
    signature: ImportSpec,
    dll: String,
    target: usize,
}
struct State {
    hooks: Vec<Hook>,
    file: Mutex<File>,
    budget: usize,
    seen: AtomicUsize,
    written: AtomicUsize,
}
static STATE: OnceLock<State> = OnceLock::new();
static CALL_INDEX: AtomicUsize = AtomicUsize::new(0);
pub fn set_call(index: usize) {
    CALL_INDEX.store(index, Ordering::Relaxed);
}

pub struct Image {
    pub base: usize,
    pub size: usize,
    pub pe: usize,
}
impl Image {
    pub unsafe fn new(base: usize) -> Result<Self, String> {
        if *(base as *const u16) != 0x5a4d {
            return Err("not MZ".into());
        }
        let pe = *((base + 0x3c) as *const u32) as usize;
        if pe > 0x100000
            || *((base + pe) as *const u32) != 0x4550
            || *((base + pe + 4) as *const u16) != 0x8664
            || *((base + pe + 24) as *const u16) != 0x20b
        {
            return Err("requires PE32+ AMD64".into());
        }
        let size = *((base + pe + 24 + 56) as *const u32) as usize;
        Ok(Self { base, size, pe })
    }
    pub fn address(&self, rva: usize, n: usize) -> Result<usize, String> {
        if rva.checked_add(n).is_none_or(|e| e > self.size) {
            return Err(format!("RVA outside image: {rva:x}+{n:x}"));
        }
        Ok(self.base + rva)
    }
    pub unsafe fn u32(&self, rva: usize) -> Result<u32, String> {
        Ok(std::ptr::read_unaligned(self.address(rva, 4)? as *const u32))
    }
    pub unsafe fn u64(&self, rva: usize) -> Result<u64, String> {
        Ok(std::ptr::read_unaligned(self.address(rva, 8)? as *const u64))
    }
    pub unsafe fn string(&self, rva: usize) -> Result<String, String> {
        let start = self.address(rva, 1)?;
        let b = std::slice::from_raw_parts(start as *const u8, (self.size - rva).min(4096));
        let n = b
            .iter()
            .position(|&b| b == 0)
            .ok_or("unterminated import name")?;
        Ok(String::from_utf8_lossy(&b[..n]).into_owned())
    }
}
fn math(name: &str) -> Option<ImportSpec> {
    use Kind::*;
    let (args, returns) = match name {
        "expf" | "sinf" | "cosf" | "log2f" | "logf" | "sqrtf" | "floorf" | "ceilf" | "tanf"
        | "atanf" | "fabsf" => (vec![F32], F32),
        "powf" | "atan2f" | "fmodf" => (vec![F32, F32], F32),
        "sin" | "cos" | "exp" | "log" | "log2" | "sqrt" | "floor" | "ceil" | "tan" | "atan"
        | "fabs" => (vec![F64], F64),
        "pow" | "atan2" | "fmod" => (vec![F64, F64], F64),
        _ => return None,
    };
    Some(ImportSpec {
        name: name.into(),
        dll: None,
        args,
        returns,
    })
}
pub unsafe fn install(image: &Image, spec: &TraceSpec, path: &Path) -> Result<Value, String> {
    let mut hooks = Vec::new();
    let mut patches = Vec::new();
    let mut report = Vec::new();
    let mut matched = vec![false; spec.imports.len()];
    let directory = image.pe + 24 + 112 + 8;
    let import_rva = image.u32(directory)? as usize;
    let import_size = image.u32(directory + 4)? as usize;
    if import_rva != 0 && (spec.math || !spec.imports.is_empty()) {
        image.address(import_rva, import_size)?;
        for desc in (import_rva..import_rva + import_size).step_by(20) {
            let names = image.u32(desc)? as usize;
            let dll_rva = image.u32(desc + 12)? as usize;
            let iat = image.u32(desc + 16)? as usize;
            if dll_rva == 0 {
                break;
            }
            let dll = image.string(dll_rva)?;
            if names == 0 {
                return Err(format!(
                    "{dll}: missing OriginalFirstThunk; cannot recover bound names"
                ));
            }
            let mut index = 0;
            loop {
                let name_rva = image.u64(names + index * 8)?;
                if name_rva == 0 {
                    break;
                }
                let name = if name_rva >> 63 != 0 {
                    format!("#{}", name_rva & 0xffff)
                } else {
                    image.string(name_rva as usize + 2)?
                };
                let mut signature = if spec.math { math(&name) } else { None };
                for (i, request) in spec.imports.iter().enumerate() {
                    if request.name == name
                        && request
                            .dll
                            .as_ref()
                            .is_none_or(|s| s.eq_ignore_ascii_case(&dll))
                    {
                        matched[i] = true;
                        signature = Some(request.clone());
                    }
                }
                if let Some(signature) = signature {
                    if signature.args.len() > 32
                        || signature.args.iter().any(|k| matches!(k, Kind::Void))
                    {
                        return Err("trace signature must have 0..32 scalar arguments".into());
                    }
                    let target = image.u64(iat + index * 8)? as usize;
                    let id = hooks.len();
                    // mov r10, id; mov r11, entry; jmp r11. No argument register touched.
                    let mut code = vec![0x49, 0xba];
                    code.extend_from_slice(&(id as u64).to_le_bytes());
                    code.extend_from_slice(&[0x49, 0xbb]);
                    code.extend_from_slice(&(witness_trace_entry as usize as u64).to_le_bytes());
                    code.extend_from_slice(&[0x41, 0xff, 0xe3]);
                    patches.push((image.address(iat + index * 8, 8)?, executable(&code)?));
                    let (provider, provider_fma) = provider(target)?;
                    report.push(json!({"dll":dll,"name":name,"iat_rva":format!("0x{:x}",iat+index*8),"target":format!("0x{target:x}"),"provider":provider,"provider_fma":provider_fma}));
                    hooks.push(Hook {
                        signature,
                        dll: dll.clone(),
                        target,
                    });
                }
                index += 1;
            }
        }
    }
    for (i, found) in matched.iter().enumerate() {
        if !found {
            return Err(format!(
                "requested normal import not found: {}",
                spec.imports[i].name
            ));
        }
    }
    let file = File::create(path).map_err(|e| e.to_string())?;
    STATE
        .set(State {
            hooks,
            file: Mutex::new(file),
            budget: spec.budget,
            seen: AtomicUsize::new(0),
            written: AtomicUsize::new(0),
        })
        .map_err(|_| "trace already installed")?;
    for (slot, target) in patches {
        let mut old = 0;
        if VirtualProtect(slot as Handle, 8, 4, &mut old) == 0 {
            return Err(error());
        }
        std::ptr::write_volatile(slot as *mut usize, target);
        let mut ignored = 0;
        if VirtualProtect(slot as Handle, 8, old, &mut ignored) == 0 {
            return Err(error());
        }
    }
    Ok(json!(report))
}
#[no_mangle]
pub unsafe extern "C" fn witness_trace_dispatch(id: usize, frame: &mut TraceFrame) {
    let entry_error = GetLastError();
    let state = STATE.get().unwrap();
    let hook = &state.hooks[id];
    let sequence = state.seen.fetch_add(1, Ordering::Relaxed);
    let call_index = CALL_INDEX.load(Ordering::Relaxed);
    let mut call = Call::new(hook.target);
    for (i, kind) in hook.signature.args.iter().enumerate() {
        call.slots[i] = if i >= 4 {
            *frame.stack.add(i - 4)
        } else if kind.float() {
            frame.xmm[i]
        } else {
            frame.gp[i]
        };
    }
    SetLastError(entry_error);
    frame.result = call.run();
    let exit_error = GetLastError();
    if sequence < state.budget {
        let args: Vec<_> = hook
            .signature
            .args
            .iter()
            .enumerate()
            .map(|(i, k)| spec::hex(&call.slots[i].to_le_bytes()[..k.width()]))
            .collect();
        let row = json!({"sequence":sequence,"call_index":call_index,"thread_id":GetCurrentThreadId(),"dll":hook.dll,"name":hook.signature.name,"args_bits_le":args,"result":spec::result(frame.result,hook.signature.returns)});
        // Lock only after forwarding: nested callbacks cannot deadlock on this writer.
        let mut file = state.file.lock().unwrap();
        writeln!(file, "{row}").expect("trace write failed");
        file.flush().expect("trace flush failed");
        state.written.fetch_add(1, Ordering::Relaxed);
    }
    SetLastError(exit_error);
}
pub fn summary() -> Value {
    let s = STATE.get().unwrap();
    let seen = s.seen.load(Ordering::Relaxed);
    json!({"seen":seen,"recorded":s.written.load(Ordering::Relaxed),"budget":s.budget,"dropped":seen.saturating_sub(s.budget)})
}
