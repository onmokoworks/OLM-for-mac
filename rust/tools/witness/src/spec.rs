use serde::Deserialize;
use serde_json::Value;
use std::{collections::BTreeMap, path::PathBuf};

#[derive(Clone, Copy, Debug, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Kind {
    U8,
    U16,
    U32,
    U64,
    I8,
    I16,
    I32,
    I64,
    F32,
    F64,
    Ptr,
    Void,
}
impl Kind {
    pub fn float(self) -> bool {
        matches!(self, Self::F32 | Self::F64)
    }
    pub fn width(self) -> usize {
        match self {
            Self::U8 | Self::I8 => 1,
            Self::U16 | Self::I16 => 2,
            Self::U32 | Self::I32 | Self::F32 => 4,
            Self::Void => 0,
            _ => 8,
        }
    }
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Spec {
    pub schema_version: u32,
    pub module: PathBuf,
    #[serde(default)]
    pub buffers: BTreeMap<String, BufferSpec>,
    pub calls: Vec<CallSpec>,
    #[serde(default)]
    pub trace: TraceSpec,
    #[serde(default = "auto")]
    pub fma: String,
}
fn auto() -> String {
    "auto".into()
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BufferSpec {
    pub size: usize,
    pub file: Option<PathBuf>,
    pub hex: Option<String>,
    #[serde(default)]
    pub fill: u8,
    #[serde(default)]
    pub pointers: Vec<Relocation>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Relocation {
    pub offset: usize,
    pub buffer: String,
    #[serde(default)]
    pub addend: usize,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CallSpec {
    pub label: Option<String>,
    pub rva: Value,
    #[serde(default)]
    pub args: Vec<Argument>,
    #[serde(rename = "return")]
    pub returns: Kind,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Argument {
    #[serde(rename = "type")]
    pub kind: Kind,
    pub value: Option<Value>,
    pub bits: Option<String>,
    pub buffer: Option<String>,
    #[serde(default)]
    pub offset: usize,
}
#[derive(Default, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TraceSpec {
    #[serde(default)]
    pub math: bool,
    #[serde(default = "budget")]
    pub budget: usize,
    #[serde(default)]
    pub imports: Vec<ImportSpec>,
}
fn budget() -> usize {
    10000
}
#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ImportSpec {
    pub name: String,
    pub dll: Option<String>,
    pub args: Vec<Kind>,
    #[serde(rename = "return")]
    pub returns: Kind,
}
pub fn word(v: &Value) -> Result<u64, String> {
    if let Some(u) = v.as_u64() {
        return Ok(u);
    }
    if let Some(i) = v.as_i64() {
        return Ok(i as u64);
    }
    if let Some(s) = v.as_str() {
        if let Some(s) = s.strip_prefix("0x") {
            return u64::from_str_radix(s, 16).map_err(|e| e.to_string());
        }
        if let Ok(i) = s.parse::<i64>() {
            return Ok(i as u64);
        }
        return s.parse::<u64>().map_err(|e| e.to_string());
    }
    Err("expected integer or integer string".into())
}
pub fn unhex(s: &str) -> Result<Vec<u8>, String> {
    if s.len() % 2 != 0 || !s.is_ascii() {
        return Err("hex needs pairs of ASCII digits".into());
    }
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).map_err(|e| e.to_string()))
        .collect()
}
pub fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}
pub fn result(r: crate::abi::Return, kind: Kind) -> Value {
    let raw = if kind.float() {
        r.xmm0[..kind.width()].to_vec()
    } else {
        r.rax.to_le_bytes()[..kind.width()].to_vec()
    };
    serde_json::json!({"bits_le":hex(&raw), "rax":format!("0x{:016x}",r.rax), "xmm0":hex(&r.xmm0)})
}
