//! Classic-only byte-row adapter. Same validation and suite ownership as olm-ae;
//! local because the shared View API intentionally exposes only checked pixels.
use crate::algorithm::{render_bytes, Params};
use olm_ae::{sys::*, Downsample, BAD};
use olm_core::{Depth, Layout, Rect};

fn check(error: PF_Err) -> olm_ae::Result<()> {
    if error == 0 {
        Ok(())
    } else {
        Err(error)
    }
}

unsafe fn layout(world: &PF_LayerDef, depth: Depth) -> olm_ae::Result<Layout> {
    if world.width <= 0 || world.height <= 0 || world.rowbytes <= 0 || world.data.is_null() {
        return Err(BAD);
    }
    let layout = Layout {
        width: world.width as usize,
        height: world.height as usize,
        stride: world.rowbytes as usize,
        depth,
        origin: (world.origin_x, world.origin_y),
    };
    layout.span().map_err(|_| BAD)?;
    Ok(layout)
}

pub(super) unsafe fn render(
    i: *const PF_InData,
    o: *mut PF_OutData,
    params: PF_ParamList,
    output: *mut PF_LayerDef,
) -> PF_Err {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| -> olm_ae::Result<()> {
        let i = i.as_ref().ok_or(BAD)?;
        o.as_mut().ok_or(BAD)?;
        if params.is_null() {
            return Err(BAD);
        }
        let input = &(*params).as_ref().ok_or(BAD)?.u.ld;
        let output = output.as_ref().ok_or(BAD)?;
        let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
        let acquire = basic.AcquireSuite.ok_or(BAD)?;
        let release = basic.ReleaseSuite.ok_or(BAD)?;
        let mut raw = std::ptr::null();
        check(acquire(kPFWorldSuite.as_ptr().cast(), 2, &mut raw) as PF_Err)?;
        let depth = (|| {
            let suite = (raw as *const PF_WorldSuite2).as_ref().ok_or(BAD)?;
            let format = suite.PF_GetPixelFormat.ok_or(BAD)?;
            let (mut a, mut b) = (0, 0);
            check(format(input, &mut a))?;
            check(format(output, &mut b))?;
            if a != b {
                return Err(BAD);
            }
            match a {
                PF_PixelFormat_ARGB32 => Ok(Depth::U8),
                PF_PixelFormat_ARGB64 => Ok(Depth::U16),
                _ => Err(BAD),
            }
        })();
        let freed = check(release(kPFWorldSuite.as_ptr().cast(), 2) as PF_Err);
        let depth = depth?;
        freed?;
        let a = layout(input, depth)?;
        let b = layout(output, depth)?;
        let na = a.span().map_err(|_| BAD)?;
        let nb = b.span().map_err(|_| BAD)?;
        let pa = input.data as usize;
        let pb = output.data as usize;
        let ea = pa.checked_add(na).ok_or(BAD)?;
        let eb = pb.checked_add(nb).ok_or(BAD)?;
        if pa < eb && pb < ea {
            return Err(BAD);
        }
        Downsample::new(i.downsample_x.num, i.downsample_x.den)?;
        Downsample::new(i.downsample_y.num, i.downsample_y.den)?;
        let e = output.extent_hint;
        let extent = Rect::new(e.left, e.top, e.right, e.bottom).map_err(|_| BAD)?;
        let key_on = (*params.add(1)).as_ref().ok_or(BAD)?.u.bd.value;
        if key_on != 0 && key_on != 1 {
            return Err(BAD);
        }
        let color = (*params.add(2)).as_ref().ok_or(BAD)?;
        let tolerance = (*params.add(3)).as_ref().ok_or(BAD)?.u.sd.value;
        // Preserve the shared adapter's color-suite callback/error behavior even
        // though Classic Smoother consumes the exact 8-bit parameter value.
        raw = std::ptr::null();
        check(acquire(kPFColorParamSuite.as_ptr().cast(), 1, &mut raw) as PF_Err)?;
        let color_result = (|| {
            let suite = (raw as *const PF_ColorParamSuite1).as_ref().ok_or(BAD)?;
            let mut floating = std::mem::zeroed();
            check(suite.PF_GetFloatingPointColorFromColorDef.ok_or(BAD)?(
                i.effect_ref,
                color,
                &mut floating,
            ))
        })();
        let freed = check(release(kPFColorParamSuite.as_ptr().cast(), 1) as PF_Err);
        color_result?;
        freed?;
        let c = color.u.cd.value;
        render_bytes(
            std::slice::from_raw_parts(input.data.cast(), na),
            a,
            std::slice::from_raw_parts_mut(output.data.cast(), nb),
            b,
            Params {
                use_key: key_on != 0,
                key: [c.alpha, c.red, c.green, c.blue],
                tolerance,
            },
            extent,
        )
        .map_err(|_| BAD)
    }))
    .unwrap_or(Err(BAD))
    .err()
    .unwrap_or(0)
}
