//! Local extension of olm-ae setup: explicit color defaults and popup count.
use olm_ae::sys::*;
use olm_ae::{Effect, Kind, Result, BAD};
use std::ffi::CString;
pub unsafe fn setup<E: Effect>(i: &PF_InData, o: &mut PF_OutData) -> Result<()> {
    let add = i.inter.add_param.ok_or(BAD)?;
    let specs = E::params();
    for s in &specs {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.uu.id = s.id;
        p.flags = s.flags;
        for (a, b) in p.name.iter_mut().take(31).zip(s.name.bytes()) {
            *a = b as _;
        }
        let mut text = None;
        match &s.kind {
            Kind::Integer {
                min,
                max,
                slider_min,
                slider_max,
                default,
            } => {
                p.param_type = PF_Param_SLIDER;
                p.u.sd = PF_SliderDef {
                    value: *default,
                    dephault: *default,
                    valid_min: *min,
                    valid_max: *max,
                    slider_min: *slider_min,
                    slider_max: *slider_max,
                    ..std::mem::zeroed()
                };
            }
            Kind::Float {
                min,
                max,
                slider_min,
                slider_max,
                default,
                precision,
            } => {
                p.param_type = PF_Param_FLOAT_SLIDER;
                p.u.fs_d = PF_FloatSliderDef {
                    value: *default as f64,
                    dephault: *default,
                    valid_min: *min,
                    valid_max: *max,
                    slider_min: *slider_min,
                    slider_max: *slider_max,
                    precision: *precision,
                    curve_tolerance: 0.05,
                    ..std::mem::zeroed()
                };
            }
            Kind::Checkbox(v) => {
                p.param_type = PF_Param_CHECKBOX;
                p.u.bd.value = *v as _;
                p.u.bd.dephault = *v as _;
                text = Some(CString::new(s.name.as_bytes()).map_err(|_| BAD)?);
                p.u.bd.u.nameptr = text.as_ref().unwrap().as_ptr();
            }
            Kind::Color => {
                p.param_type = PF_Param_COLOR;
                p.u.cd.value.alpha = 255;
                p.u.cd.dephault.alpha = 255;
            }
            Kind::Popup { choices, default } => {
                p.param_type = PF_Param_POPUP;
                text = Some(CString::new(choices.as_bytes()).map_err(|_| BAD)?);
                p.u.pd.num_choices = choices.split('|').count() as _;
                p.u.pd.value = *default as _;
                p.u.pd.dephault = *default;
                p.u.pd.u.namesptr = text.as_ref().unwrap().as_ptr();
            }
            Kind::GroupStart => p.param_type = PF_Param_GROUP_START,
            Kind::GroupEnd => p.param_type = PF_Param_GROUP_END,
        }
        // Original declares five modes but supplies only three visible labels.
        if s.id == 11 {
            p.u.pd.num_choices = 5;
        }
        if s.id == 7 {
            p.u.cd.value.red = 255;
            p.u.cd.dephault.red = 255;
        }
        let err = add(i.effect_ref, -1, &mut p);
        if err != 0 {
            return Err(err);
        }
        drop(text);
    }
    o.num_params = specs.len() as i32 + 1;
    Ok(())
}
