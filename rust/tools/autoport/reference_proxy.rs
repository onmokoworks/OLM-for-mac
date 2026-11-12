//! Diagnostic host-contract adapter, never a replacement oracle identity.
//! Calls the original in place. Arithmetic, worlds and parameters are untouched.
#![allow(non_upper_case_globals)]
use after_effects_sys::*;
use std::{cell::RefCell,ffi::{c_void,CString},sync::OnceLock};
type Entry=unsafe extern "C" fn(PF_Cmd,*mut PF_InData,*mut PF_OutData,PF_ParamList,*mut PF_LayerDef,*mut c_void)->PF_Err;
#[link(name="kernel32")]
extern "system" { fn LoadLibraryW(p:*const u16)->*mut c_void; fn GetProcAddress(m:*mut c_void,n:*const i8)->*mut c_void; }
static ENTRY:OnceLock<Entry>=OnceLock::new();
#[derive(Default)]
struct State {
    old:Option<PF_InteractCallbacks>,live:usize,last_slot:i32,
    suppressed:usize,events:Vec<serde_json::Value>,
}
thread_local! {static STATE:RefCell<State>=RefCell::new(State::default());}
unsafe extern "C" fn checkout(r:PF_ProgPtr,n:i32,t:i32,s:i32,scale:u32,p:*mut PF_ParamDef)->PF_Err {
    let f=STATE.with(|x|x.borrow().old.unwrap().checkout_param.unwrap());
    let e=f(r,n,t,s,scale,p);
    STATE.with(|x|{let mut x=x.borrow_mut();if e==0{x.live+=1;x.last_slot=n;}x.events.push(serde_json::json!({"checkout":n,"result":e,"ptr":p as usize}));});e
}
unsafe extern "C" fn checkin(r:PF_ProgPtr,p:*mut PF_ParamDef)->PF_Err {
    let (f,suppress)=STATE.with(|x|{let x=x.borrow();(x.old.unwrap().checkin_param.unwrap(),x.live==0&&x.last_slot==2&&x.suppressed==0&&std::env::var_os("OLM_REFERENCE_REDUNDANT_CHECKIN").as_deref()==Some(std::ffi::OsStr::new("1")))});
    let e=if suppress {0}else{f(r,p)};
    STATE.with(|x|{let mut x=x.borrow_mut();if suppress{x.suppressed+=1}else if e==0{x.live=x.live.saturating_sub(1)};x.events.push(serde_json::json!({"checkin":true,"result":e,"ptr":p as usize,"suppressed":suppress}));});e
}
unsafe fn invoke(cmd:PF_Cmd,i:*mut PF_InData,o:*mut PF_OutData,p:PF_ParamList,w:*mut PF_LayerDef,e:*mut c_void)->PF_Err {
    let f=*ENTRY.get_or_init(||{
        let path=std::env::var("OLM_REFERENCE_ORIGINAL").expect("original path required");
        let wide:Vec<_>=path.encode_utf16().chain(Some(0)).collect();let m=LoadLibraryW(wide.as_ptr());assert!(!m.is_null());
        let n=CString::new("entryPointFunc").unwrap();let raw=GetProcAddress(m,n.as_ptr());assert!(!raw.is_null());std::mem::transmute(raw)
    });
    if cmd!=PF_Cmd_SMART_RENDER{return f(cmd,i,o,p,w,e)}
    let old=(*i).inter;
    STATE.with(|x|*x.borrow_mut()=State{old:Some(old),..State::default()});
    (*i).inter.checkout_param=Some(checkout);(*i).inter.checkin_param=Some(checkin);
    let result=f(cmd,i,o,p,w,e);(*i).inter=old;
    if let Some(path)=std::env::var_os("OLM_REFERENCE_TRACE") {
        STATE.with(|x|{let x=x.borrow();let v=serde_json::json!({"selector_result":result,"live":x.live,"suppressed":x.suppressed,"events":x.events});std::fs::write(path,serde_json::to_vec_pretty(&v).unwrap()).unwrap();});
    }
    result
}
#[no_mangle]
pub unsafe extern "C" fn entryPointFunc(cmd:PF_Cmd,i:*mut PF_InData,o:*mut PF_OutData,p:PF_ParamList,w:*mut PF_LayerDef,e:*mut c_void)->PF_Err {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(||invoke(cmd,i,o,p,w,e))).unwrap_or(512)
}
