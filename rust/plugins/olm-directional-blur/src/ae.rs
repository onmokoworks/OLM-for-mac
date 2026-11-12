//! Local extension of the pilot AE boundary: fixed, angle and layer parameters.
use crate::{
    algorithm::{self, Depth, Params},
    host::{self, Effect, Kind, Param, RenderContext, Value},
};
use olm_core::{Error, Pixel, View, ViewMut};
pub struct Plugin;
fn param(id: i32, name: &str, kind: Kind) -> Param {
    Param {
        id,
        name: name.into(),
        flags: 0,
        kind,
    }
}
fn integer(id: i32, name: &str, min: i32, max: i32, default: i32) -> Param {
    param(
        id,
        name,
        Kind::Integer {
            min,
            max,
            slider_min: min,
            slider_max: max,
            default,
        },
    )
}
impl Effect for Plugin {
    const NAME: &'static str = "OLM DirectionalBlur";
    const MATCH_NAME: &'static str = "OLM Directional Blur";
    const VERSION: u32 = 559104;
    const FLAGS: u32 = 0x06000040;
    const FLAGS2: u32 = 0x08001408;
    const PRESERVE_ZERO_ALPHA_RGB: Option<bool> = Some(true);
    unsafe fn global_setup(i: &host::sys::PF_InData) -> host::Result<()> {
        crate::ui::register(i)
    }
    unsafe fn update_ui(i: &host::sys::PF_InData) -> host::Result<()> {
        crate::ui::update(i)
    }
    fn params() -> Vec<Param> {
        vec![
            param(1, "Angle", Kind::Angle),
            param(
                2,
                "Brightness Gain",
                Kind::Float {
                    min: 0.0,
                    max: 10.0,
                    slider_min: 0.0,
                    slider_max: 2.0,
                    default: 1.0,
                    precision: 2,
                },
            ),
            param(3, "Size Variation", Kind::Fixed),
            param(4, "Front Blur Parameters", Kind::GroupStart),
            integer(5, "Blur Strength", 0, 4000, 0),
            integer(6, "Alpha Fade", 0, 100, 0),
            param(7, "Sharp Tail", Kind::Fixed),
            param(8, "Sharp Tail", Kind::GroupEnd),
            param(9, "Back Blur Parameters", Kind::GroupStart),
            integer(10, "Blur Strength", 0, 4000, 0),
            integer(11, "Alpha Fade", 0, 100, 0),
            param(12, "Sharp Tail", Kind::Fixed),
            param(13, "Sharp Tail", Kind::GroupEnd),
            param(14, "Noise Parameters", Kind::GroupStart),
            param(15, "Noise Variation", Kind::Fixed),
            param(
                16,
                "Noise Type",
                Kind::Popup {
                    choices: "Smooth | Block | Layer".into(),
                    default: 1,
                },
            ),
            param(17, "Noise Layer", Kind::Layer),
            integer(18, "Seed", 1, 1000, 1),
            param(19, "Offset", Kind::Angle),
            param(
                20,
                "Thickness",
                Kind::Float {
                    min: 1.0,
                    max: 100.0,
                    slider_min: 1.0,
                    slider_max: 100.0,
                    default: 10.0,
                    precision: 2,
                },
            ),
            param(21, "Thickness", Kind::GroupEnd),
        ]
    }
    fn render(
        v: &[Value],
        ctx: RenderContext,
        input: &View<'_>,
        output: &mut ViewMut<'_>,
    ) -> olm_core::Result<()> {
        let a = input.layout();
        let b = output.layout();
        if b.width > a.width || b.height > a.height {
            return Err(Error::Geometry);
        }
        let scale = ctx.downsample_x.numerator as f32 / ctx.downsample_x.denominator as f32;
        if scale <= 0.0
            || scale > 1.0
            || ctx.downsample_y.numerator as u32 > ctx.downsample_y.denominator
        {
            return Err(Error::Geometry);
        }
        let mut p = Params {
            angle: v[0].number as f32,
            gain: v[1].number as f32,
            size: v[2].number as f32,
            front: v[4].number as i32,
            front_fade: v[5].number as i32,
            front_tail: v[6].number as f32,
            back: v[9].number as i32,
            back_fade: v[10].number as i32,
            back_tail: v[11].number as f32,
            noise: v[14].number as f32,
            noise_type: v[15].number as i32,
            seed: v[17].number as u32,
            offset: v[18].number as i32,
            thickness: v[19].number as f32,
        }
        .sampled(scale);
        let depth = match a.depth {
            olm_core::Depth::U8 => Depth::U8,
            olm_core::Depth::U16 => Depth::U16,
            olm_core::Depth::F32 => Depth::F32,
        };
        let mut layer_view = None;
        if p.noise > 0.0 && p.noise_type == 3 {
            if let Some(world) = v[16].layer.as_ref() {
                if world.width == a.width as i32
                    && world.height == a.height as i32
                    && !world.data.is_null()
                {
                    unsafe {
                        let layout =
                            host::world_layout(world, a.depth).map_err(|_| Error::Geometry)?;
                        layer_view = Some(View::new(
                            std::slice::from_raw_parts(world.data.cast(), layout.span()?),
                            layout,
                        )?);
                    }
                }
            }
            if layer_view.is_none() && depth != Depth::U8 {
                p.noise = 0.0;
            }
        }
        crate::admission::check(input, b, &p, depth, ctx, layer_view.as_ref())?;
        if p.identity() {
            for y in 0..b.height {
                for x in 0..b.width {
                    output.set(x, y, input.get(x, y)?)?;
                }
            }
            return Ok(());
        }
        let mut source = algorithm::zeros(a.width * a.height).map_err(|_| Error::Allocation)?;
        for y in 0..b.height {
            for x in 0..b.width {
                source[y * a.width + x] = unpack(input.get(x, y)?);
            }
        }
        let layer = if let Some(view) = layer_view {
            let mut pixels = algorithm::zeros(a.width * a.height).map_err(|_| Error::Allocation)?;
            for y in 0..a.height {
                for x in 0..a.width {
                    pixels[y * a.width + x] = unpack(view.get(x, y)?);
                }
            }
            Some(pixels)
        } else {
            None
        };
        let result = algorithm::render(&source, a.width, a.height, &p, depth, layer.as_deref(), 1)
            .map_err(|_| Error::Geometry)?;
        for y in 0..b.height {
            for x in 0..b.width {
                let v = result[y * a.width + x];
                let argb = [v[3], v[0], v[1], v[2]];
                let pixel = match depth {
                    Depth::U8 => Pixel::U8(argb.map(|v| olm_math::x86::cvttss2si(v * 255.0) as u8)),
                    Depth::U16 => {
                        Pixel::U16(argb.map(|v| olm_math::x86::cvttss2si(v * 32768.0) as u16))
                    }
                    Depth::F32 => Pixel::F32(argb),
                };
                output.set(x, y, pixel)?;
            }
        }
        Ok(())
    }
}
fn unpack(p: Pixel) -> [f32; 4] {
    let a = match p {
        Pixel::U8(v) => v.map(|x| x as f32 / 255.0),
        Pixel::U16(v) => v.map(|x| x as f32 * (1.0 / 32768.0)),
        Pixel::F32(v) => v,
    };
    [a[1], a[2], a[3], a[0]]
}
#[no_mangle]
pub unsafe extern "C" fn EffectMain(
    cmd: host::sys::PF_Cmd,
    i: *mut host::sys::PF_InData,
    o: *mut host::sys::PF_OutData,
    p: host::sys::PF_ParamList,
    w: *mut host::sys::PF_LayerDef,
    e: *mut std::ffi::c_void,
) -> host::sys::PF_Err {
    host::entry::<Plugin>(cmd, i, o, p, w, e)
}
#[no_mangle]
pub unsafe extern "C" fn entryPointFunc(
    cmd: host::sys::PF_Cmd,
    i: *mut host::sys::PF_InData,
    o: *mut host::sys::PF_OutData,
    p: host::sys::PF_ParamList,
    w: *mut host::sys::PF_LayerDef,
    e: *mut std::ffi::c_void,
) -> host::sys::PF_Err {
    EffectMain(cmd, i, o, p, w, e)
}

#[cfg(target_os = "macos")]
#[no_mangle]
pub unsafe extern "C" fn PluginDataEntryFunction2(
    p: host::sys::PF_PluginDataPtr,
    cb: host::sys::PF_PluginDataCB2,
    _basic: *const host::sys::SPBasicSuite,
    _host: *const std::ffi::c_char,
    _version: *const std::ffi::c_char,
) -> host::sys::PF_Err {
    let Some(cb) = cb else { return host::BAD };
    cb(
        p,
        b"OLM DirectionalBlur\0".as_ptr().cast(),
        b"OLM Directional Blur\0".as_ptr().cast(),
        b"OLM Plug-ins\0".as_ptr(),
        b"EffectMain\0".as_ptr(),
        i32::from_be_bytes(*b"eFKT"),
        13,
        28,
        0,
        b"https://olm.co.jp/\0".as_ptr(),
    )
}
