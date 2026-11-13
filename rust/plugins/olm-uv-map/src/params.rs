//! Measured original PARAMS_SETUP, cross-checked with AEXCompat inventory.
//! Slot order, disk IDs and raw numeric bits are intentional; do not normalize.
use crate::ae::{check, Result, BAD};
#[cfg(not(target_os = "macos"))]
use after_effects_sys::*;
#[cfg(target_os = "macos")]
use olm_ae::sys::*;
pub const VERSION: u32 = 559104;
pub const FLAGS: u32 = 33554496;
pub const FLAGS2: u32 = 402658304;
pub fn arbitrary_default(_id: i16) -> Option<&'static [u8]> {
    None
}
pub unsafe fn setup(i: &PF_InData, o: &mut PF_OutData) -> Result<()> {
    let add = i.inter.add_param.ok_or(BAD)?;
    // Slot 1: Texture; layer
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 0;
        p.param_type = 0;
        p.u.ld.dephault = -1;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 1;
        p.name = [
            84, 101, 120, 116, 117, 114, 101, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 2: Interpolation Method; popup
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 0;
        p.param_type = 7;
        p.u.pd.dephault = 3;
        p.u.pd.num_choices = 3;
        p.u.pd.value = 3;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 2;
        p.name = [
            73, 110, 116, 101, 114, 112, 111, 108, 97, 116, 105, 111, 110, 32, 77, 101, 116, 104,
            111, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        const LABEL: &[u8] = &[
            78, 101, 97, 114, 101, 115, 116, 32, 78, 101, 105, 103, 104, 98, 111, 114, 124, 66,
            105, 108, 105, 110, 101, 97, 114, 124, 84, 114, 105, 108, 105, 110, 101, 97, 114, 0,
        ];
        p.u.pd.u.namesptr = LABEL.as_ptr().cast();
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 3: Smoothness; float_slider
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 10;
        p.u.fs_d.curve_tolerance = f32::from_bits(1028443341);
        p.u.fs_d.dephault = f32::from_bits(1056964608);
        p.u.fs_d.display_flags = 0;
        p.u.fs_d.exponent = f32::from_bits(0);
        p.u.fs_d.fs_flags = 0;
        p.u.fs_d.phase = f64::from_bits(0);
        p.u.fs_d.precision = 2;
        p.u.fs_d.slider_max = f32::from_bits(1065353216);
        p.u.fs_d.slider_min = f32::from_bits(0);
        p.u.fs_d.useExponent = 0;
        p.u.fs_d.valid_max = f32::from_bits(1065353216);
        p.u.fs_d.valid_min = f32::from_bits(0);
        p.u.fs_d.value = f64::from_bits(4602678819172646912);
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 3;
        p.name = [
            83, 109, 111, 111, 116, 104, 110, 101, 115, 115, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        p.u.fs_d.value_desc = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    o.num_params = 4;
    Ok(())
}
