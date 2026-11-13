//! New upstream border/extent declaration, RVA 0x1174330.
use olm_ae::{sys::*, BAD};

unsafe fn value(i: &PF_InData, slot: i32) -> Result<PF_ParamDef, PF_Err> {
    let put = i.inter.checkin_param.ok_or(BAD)?;
    let mut p = std::mem::zeroed();
    let err = i.inter.checkout_param.ok_or(BAD)?(
        i.effect_ref,
        slot,
        i.current_time,
        i.time_step,
        i.time_scale,
        &mut p,
    );
    if err != 0 {
        return Err(err);
    }
    let result = p;
    let err = put(i.effect_ref, &mut p);
    if err != 0 {
        return Err(err);
    }
    Ok(result)
}

pub unsafe fn run(i: &PF_InData, extra: *mut std::ffi::c_void) -> Result<(), PF_Err> {
    let in_out = value(i, 2)?.u.pd.value as i32;
    let use_padding = value(i, 13)?.u.bd.value != 0;
    let outside = if use_padding && (in_out == 2 || in_out == 3) {
        value(i, 4)?.u.sd.value
    } else {
        0
    };
    let (_, px, py) = crate::algorithm::padding(&crate::algorithm::Params {
        in_out,
        use_padding,
        outside,
        scale_x: (i.downsample_x.num as u32, i.downsample_x.den),
        scale_y: (i.downsample_y.num as u32, i.downsample_y.den),
        ..Default::default()
    })
    .map_err(|_| BAD)?;
    let px = i32::try_from(px).map_err(|_| BAD)?;
    let py = i32::try_from(py).map_err(|_| BAD)?;
    let e = (extra as *mut PF_PreRenderExtra).as_mut().ok_or(BAD)?;
    let ei = e.input.as_ref().ok_or(BAD)?;
    let eo = e.output.as_mut().ok_or(BAD)?;
    let cb = e.cb.as_ref().ok_or(BAD)?;
    let mut request = ei.output_request;
    request.preserve_rgb_of_zero_alpha = 0;
    let mut r: PF_CheckoutResult = std::mem::zeroed();
    let err = cb.checkout_layer.ok_or(BAD)?(
        i.effect_ref,
        0,
        0,
        &request,
        i.current_time,
        i.time_step,
        i.time_scale,
        &mut r,
    );
    if err != 0 {
        return Err(err);
    }
    let rect = r.result_rect;
    if rect.left == 0 && rect.top == 0 && rect.right == 0 && rect.bottom == 0 {
        eo.result_rect = rect;
        eo.max_result_rect = rect;
    } else {
        eo.result_rect = PF_LRect {
            left: rect.left.checked_sub(px).ok_or(BAD)?,
            top: rect.top.checked_sub(py).ok_or(BAD)?,
            right: rect.right.checked_add(px).ok_or(BAD)?,
            bottom: rect.bottom.checked_add(py).ok_or(BAD)?,
        };
        eo.max_result_rect = eo.result_rect;
        eo.flags |= 1;
    }
    Ok(())
}
