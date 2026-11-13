//! Retained source/parameter fixtures take precedence over generic beta admission.
use olm_ae::{Value,sys::PF_EffectWorld,BAD};
use olm_core::Depth;
pub(crate) unsafe fn retained(v:&[Value],world:&PF_EffectWorld,depth:Depth)->olm_ae::Result<bool>{
    if world.width!=1920 || world.height!=1080 || world.rowbytes!=1920*depth.pixel_bytes() as i32{return Ok(false);}
    let at=|s:usize|v[s-1].number;
    let color=|s:usize,c:[u8;4]|v[s-1].color8==c;
    let hash=if depth==Depth::U8 {
        if !color(2,[255;4]){return Ok(false);}
        let tuples:[(i32,i32,i32,i32,i32,i32,i32,i32,f64,i32);12]=[
            (0,0,100,2,0,2,1,1,2.40000009536743,0),(1,1,100,2,0,2,1,1,2.40000009536743,0),
            (1,0,0,2,0,2,1,1,2.40000009536743,0),(1,0,100,2,100,2,1,1,2.40000009536743,0),
            (1,0,100,100,100,2,1,1,2.40000009536743,0),(1,0,100,0,100,2,1,1,2.40000009536743,0),
            (1,0,100,26,40,2,1,1,2.40000009536743,0),(1,0,29,26,40,2,1,1,2.40000009536743,0),
            (1,0,100,26,40,1,1,1,2.40000009536743,0),(1,0,100,22,40,2,2,3,1.36872434616089,0),
            (1,0,100,22,40,2,2,5,2.16954731941223,1),(1,0,100,88,40,2,2,5,2.16954731941223,2)];
        let yes=tuples.iter().any(|&(key,inv,smooth,range,extra,ver,mode,count,gamma,palette)|{
            [(1,key),(3,inv),(4,smooth),(6,range),(5,extra),(7,ver),(8,mode),(10,count)].iter().all(|&(s,n)|at(s)==n as f64)
            && at(9)==gamma && (0..5).all(|i|color(11+i,[255,if palette==2 && i==0{255}else{0},0,if palette!=0 && i==4{255}else{0}]))
        });
        if !yes{return Ok(false);}
        "1c15f67a9d0818a0a0266971720e855acac70a89e2690ccbedf5e142fc1c64f3"
    }else{
        if ![(1,0),(3,0),(4,10),(6,99),(5,1),(7,2),(8,2),(10,2)].iter().all(|&(s,n)|at(s)==n as f64)
            || at(9)!=1.2699999809265137 || !color(2,[255,248,233,159])
            || ![[255,233,38,239],[255,192,215,172],[255,124,34,100],[255,17,7,127],[255,212,216,8]].iter().enumerate().all(|(i,&c)|color(11+i,c)){return Ok(false);}
        if depth==Depth::U16 {"c8d5ded0f9da071eb9e14e7bf20300916a3b8b292f081099d25dfc6359bbafa2"}else{"133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b"}
    };
    if world.data.is_null(){return Err(BAD);}
    Ok(crate::sha256::matches(std::slice::from_raw_parts(world.data.cast(),world.rowbytes as usize*1080),hash))
}
