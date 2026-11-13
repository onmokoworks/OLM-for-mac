//! Measured original PARAMS_SETUP, cross-checked with AEXCompat inventory.
//! Slot order, disk IDs and raw numeric bits are intentional; do not normalize.
use crate::ae::{check, Result, BAD};
#[cfg(not(target_os = "macos"))]
use after_effects_sys::*;
#[cfg(target_os = "macos")]
use olm_ae::sys::*;
pub const VERSION: u32 = 569344;
pub const FLAGS: u32 = 33554496;
pub const FLAGS2: u32 = 134222848;
pub unsafe fn setup(i: &PF_InData, o: &mut PF_OutData) -> Result<()> {
    let add = i.inter.add_param.ok_or(BAD)?;
    // Slot 1: Number of Colors; slider
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 0;
        p.param_type = 1;
        p.u.sd.dephault = 0;
        p.u.sd.slider_max = 100;
        p.u.sd.slider_min = 0;
        p.u.sd.valid_max = 100;
        p.u.sd.valid_min = 0;
        p.u.sd.value = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 1;
        p.name = [
            78, 117, 109, 98, 101, 114, 32, 111, 102, 32, 67, 111, 108, 111, 114, 115, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        p.u.sd.value_str = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0,
        ];
        p.u.sd.value_desc = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 2: Use automatic colors; checkbox
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 0;
        p.param_type = 4;
        p.u.bd.dephault = 0;
        p.u.bd.value = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 2;
        p.name = [
            85, 115, 101, 32, 97, 117, 116, 111, 109, 97, 116, 105, 99, 32, 99, 111, 108, 111, 114,
            115, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        const LABEL: &[u8] = &[0];
        p.u.bd.u.nameptr = LABEL.as_ptr().cast();
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 3: Initalize colors; button
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 15;
        p.u.button_d.value = 0;
        p.ui_flags = 4;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 3;
        p.name = [
            73, 110, 105, 116, 97, 108, 105, 122, 101, 32, 99, 111, 108, 111, 114, 115, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        const LABEL: &[u8] = &[73, 110, 105, 116, 0];
        p.u.button_d.u.namesptr = LABEL.as_ptr().cast();
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 4: Add automatic colors; button
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 15;
        p.u.button_d.value = 0;
        p.ui_flags = 4;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 4;
        p.name = [
            65, 100, 100, 32, 97, 117, 116, 111, 109, 97, 116, 105, 99, 32, 99, 111, 108, 111, 114,
            115, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        const LABEL: &[u8] = &[65, 100, 100, 0];
        p.u.button_d.u.namesptr = LABEL.as_ptr().cast();
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 5: Clear colors list; button
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 15;
        p.u.button_d.value = 0;
        p.ui_flags = 4;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 5;
        p.name = [
            67, 108, 101, 97, 114, 32, 99, 111, 108, 111, 114, 115, 32, 108, 105, 115, 116, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        const LABEL: &[u8] = &[67, 108, 101, 97, 114, 0];
        p.u.button_d.u.namesptr = LABEL.as_ptr().cast();
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 6: Colors list; group_start
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 32;
        p.param_type = 13;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 6;
        p.name = [
            67, 111, 108, 111, 114, 115, 32, 108, 105, 115, 116, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 7: Color 1; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 7;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 8: Color 2; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 8;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 9: Color 3; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 9;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 10: Color 4; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 10;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 11: Color 5; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 11;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 12: Color 6; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 12;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 13: Color 7; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 13;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 14: Color 8; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 14;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 15: Color 9; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 15;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 16: Color 10; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 16;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 17: Color 11; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 17;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 18: Color 12; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 18;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 19: Color 13; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 19;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 20: Color 14; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 20;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 21: Color 15; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 21;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 22: Color 16; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 22;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 23: Color 17; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 23;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 24: Color 18; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 24;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 25: Color 19; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 25;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 26: Color 20; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 26;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 27: Color 21; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 27;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 28: Color 22; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 28;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 29: Color 23; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 29;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 30: Color 24; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 30;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 31: Color 25; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 31;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 32: Color 26; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 32;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 33: Color 27; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 33;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 34: Color 28; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 34;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 35: Color 29; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 35;
        p.name = [
            67, 111, 108, 111, 114, 32, 50, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 36: Color 30; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 36;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 37: Color 31; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 37;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 38: Color 32; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 38;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 39: Color 33; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 39;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 40: Color 34; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 40;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 41: Color 35; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 41;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 42: Color 36; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 42;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 43: Color 37; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 43;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 44: Color 38; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 44;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 45: Color 39; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 45;
        p.name = [
            67, 111, 108, 111, 114, 32, 51, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 46: Color 40; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 46;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 47: Color 41; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 47;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 48: Color 42; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 48;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 49: Color 43; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 49;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 50: Color 44; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 50;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 51: Color 45; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 51;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 52: Color 46; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 52;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 53: Color 47; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 53;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 54: Color 48; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 54;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 55: Color 49; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 55;
        p.name = [
            67, 111, 108, 111, 114, 32, 52, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 56: Color 50; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 56;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 57: Color 51; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 57;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 58: Color 52; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 58;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 59: Color 53; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 59;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 60: Color 54; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 60;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 61: Color 55; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 61;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 62: Color 56; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 62;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 63: Color 57; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 63;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 64: Color 58; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 64;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 65: Color 59; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 65;
        p.name = [
            67, 111, 108, 111, 114, 32, 53, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 66: Color 60; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 66;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 67: Color 61; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 67;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 68: Color 62; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 68;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 69: Color 63; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 69;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 70: Color 64; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 70;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 71: Color 65; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 71;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 72: Color 66; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 72;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 73: Color 67; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 73;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 74: Color 68; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 74;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 75: Color 69; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 75;
        p.name = [
            67, 111, 108, 111, 114, 32, 54, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 76: Color 70; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 76;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 77: Color 71; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 77;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 78: Color 72; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 78;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 79: Color 73; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 79;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 80: Color 74; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 80;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 81: Color 75; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 81;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 82: Color 76; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 82;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 83: Color 77; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 83;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 84: Color 78; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 84;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 85: Color 79; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 85;
        p.name = [
            67, 111, 108, 111, 114, 32, 55, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 86: Color 80; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 86;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 87: Color 81; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 87;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 88: Color 82; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 88;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 89: Color 83; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 89;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 90: Color 84; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 90;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 91: Color 85; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 91;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 92: Color 86; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 92;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 93: Color 87; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 93;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 94: Color 88; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 94;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 95: Color 89; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 95;
        p.name = [
            67, 111, 108, 111, 114, 32, 56, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 96: Color 90; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 96;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 97: Color 91; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 97;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 98: Color 92; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 98;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 99: Color 93; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 99;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 100: Color 94; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 100;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 101: Color 95; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 101;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 53, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 102: Color 96; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 102;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 54, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 103: Color 97; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 103;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 104: Color 98; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 104;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 105: Color 99; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 105;
        p.name = [
            67, 111, 108, 111, 114, 32, 57, 57, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 106: Color 100; color
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 64;
        p.param_type = 5;
        p.u.cd.dephault.alpha = 255;
        p.u.cd.dephault.blue = 0;
        p.u.cd.dephault.green = 0;
        p.u.cd.dephault.red = 0;
        p.u.cd.value.alpha = 255;
        p.u.cd.value.blue = 0;
        p.u.cd.value.green = 0;
        p.u.cd.value.red = 0;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 106;
        p.name = [
            67, 111, 108, 111, 114, 32, 49, 48, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    // Slot 107: ; group_end
    {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.flags = 0;
        p.param_type = 14;
        p.ui_flags = 0;
        p.ui_height = 0;
        p.ui_width = 0;
        p.uu.id = 107;
        p.name = [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0,
        ];
        check(add(i.effect_ref, -1, &mut p))?;
    }
    o.num_params = 108;
    Ok(())
}
