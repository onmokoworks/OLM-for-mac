use crate::ae_support::{Effect, Kind, Param, RenderContext, Value};
use crate::algorithm::{self, Params};
use olm_core::{Depth, Error, Result, View, ViewMut};
pub struct Plugin;
impl Effect for Plugin {
    const NAME: &'static str = "OLM Blur";
    const MATCH_NAME: &'static str = "OLM OLM Blur";
    const VERSION: u32 = 591872; // PF_VERSION(1,2,1,DEVELOP,0); original PiPL eVER.
    const FLAGS: u32 = 0x06000040;
    fn params() -> Vec<Param> {
        vec![
            Param {
                id: 5,
                name: "Blur Amount".into(),
                flags: 0,
                kind: Kind::Float {
                    min: 1.0,
                    max: 1000.0,
                    slider_min: 1.0,
                    slider_max: 50.0,
                    default: 5.0,
                    precision: 2,
                },
            },
            Param {
                id: 6,
                name: "Blur Smoothness".into(),
                flags: 0,
                kind: Kind::Fixed,
            },
            Param {
                id: 3,
                name: "Number of Repeat".into(),
                flags: 0,
                kind: Kind::Integer {
                    min: 1,
                    max: 10,
                    slider_min: 1,
                    slider_max: 10,
                    default: 2,
                },
            },
            Param {
                id: 4,
                name: "Bias Direction".into(),
                flags: 0,
                kind: Kind::Popup {
                    choices: "Vertical|Horizontal".into(),
                    default: 1,
                },
            },
            Param {
                id: 7,
                name: "Legacy".into(),
                flags: 128,
                kind: Kind::Checkbox(false),
            },
        ]
    }
    fn render(
        v: &[Value],
        ctx: RenderContext,
        input: &View<'_>,
        output: &mut [u8],
        o: olm_core::Layout,
    ) -> Result<()> {
        let l = input.layout();
        if !ctx.smart {
            if l.depth == Depth::F32
                || l.width != o.width
                || l.height != o.height
                || l.width > 4096
                || l.height > 2160
                || l.width * l.height > 3840 * 2160
                || v[0].number != 5.0
                || v[1].number != 100.0
                || v[2].number != 2.0
            {
                return Err(Error::Unsupported);
            }
            let mut output = ViewMut::new(output, o)?;
            for y in 0..l.height {
                for x in 0..l.width {
                    output.set(x, y, input.get(x, y)?)?;
                }
            }
            return Ok(());
        }
        if !v[0].number.is_finite()
            || !(1.0..=1000.0).contains(&v[0].number)
            || !(1.0..=100.0).contains(&v[1].number)
            || !(1.0..=10.0).contains(&v[2].number)
            || !(1.0..=2.0).contains(&v[3].number)
            || !(v[4].number == 0.0 || v[4].number == 1.0)
        {
            return Err(Error::Unsupported);
        }
        let p = Params {
            amount: v[0].number as f32,
            smoothness: v[1].number.floor() as f32,
            repeat: v[2].number as usize,
            bias: v[3].number as usize,
            legacy: v[4].number != 0.0,
            scale: ctx.downsample_x.numerator as f32 / ctx.downsample_x.denominator as f32,
        };
        algorithm::render_bytes(
            input,
            output,
            o,
            &p,
            render_threads(input.layout().width, input.layout().height),
        )
    }
}
crate::export_blur_effect!(Plugin, entryPointFunc);

// Small worlds do not amortize row-worker startup. No process-global pool/state.
fn render_threads(width: usize, height: usize) -> usize {
    if width.saturating_mul(height) < 65536 {
        1
    } else {
        std::thread::available_parallelism().map_or(1, usize::from)
    }
}
