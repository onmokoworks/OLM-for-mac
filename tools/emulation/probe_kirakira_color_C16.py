#!/usr/bin/env python3
"""Generate a diagnostic planar-filter hypothesis for the four-channel owner.

No admission is added. Output must be in ticket scratch; compare with the
original public AEX before interpreting this as a recovered implementation.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def candidate(body, unnormalized=False):
    def replace(old, new):
        nonlocal body
        assert body.count(old) == 1, old
        body = body.replace(old, new)

    replace('return (info.channel == 1 || (info.channel == 2 &&',
            'return (info.channel == 1 || ((info.channel == 2 || info.channel == 3 || info.channel == 5 || info.channel == 6) &&')
    replace('std::vector<float> seed((size_t)w * h);', '''std::vector<float> seed((size_t)w * h);
    if (info.channel == 3 || info.channel == 5 || info.channel == 6) {
        seed.resize((size_t)w*h*4);
        const float exponent = (float)info.strength_multiplier + 1.0f;
        for (size_t i=0; i<pixels.size(); ++i) {
            seed[i*4] = std::pow(pixels[i].r,exponent)*pixels[i].a;
            seed[i*4+1] = std::pow(pixels[i].g,exponent)*pixels[i].a;
            seed[i*4+2] = std::pow(pixels[i].b,exponent)*pixels[i].a;
            seed[i*4+3] = pixels[i].a;
        }
        return seed;
    }''')
    replace('const std::vector<float> zero_ray((size_t)work_width * work_height, 0.0f);',
            '''const bool color_owner = info.channel == 3 || info.channel == 5 || info.channel == 6;
    const std::vector<float> zero_ray(seed.size(), 0.0f);''')
    replace('return RotatedAxisBoxBlur(seed, work_width, work_height, len, angle, passes, info.blur_mode,',
            '''if (color_owner) {
            std::vector<float> result(seed.size()), plane((size_t)work_width*work_height);
            for (int c=0; c<4; ++c) {
                for (size_t i=0; i<plane.size(); ++i) plane[i]=seed[i*4+c];
                const auto ray=RotatedAxisBoxBlur(plane,work_width,work_height,len,angle,passes,info.blur_mode,false,true);
                for (size_t i=0; i<plane.size(); ++i) result[i*4+c]=ray[i];
            }
            return result;
        }
        return RotatedAxisBoxBlur(seed, work_width, work_height, len, angle, passes, info.blur_mode,''')
    replace('highlight = olm::kirakira::highlight_isotropic_box_blur(\n\t\t\tseed, work_width, work_height, highlight_radius * 2 + 1, highlight_passes);',
            '''if (color_owner) {
            highlight.resize(seed.size());
            std::vector<float> plane((size_t)work_width*work_height);
            for (int c=0; c<4; ++c) {
                for (size_t i=0; i<plane.size(); ++i) plane[i]=seed[i*4+c];
                const auto ray=olm::kirakira::highlight_isotropic_box_blur(plane,work_width,work_height,highlight_radius*2+1,highlight_passes);
                for (size_t i=0; i<plane.size(); ++i) highlight[i*4+c]=ray[i];
            }
        } else {
            highlight = olm::kirakira::highlight_isotropic_box_blur(
                seed, work_width, work_height, highlight_radius * 2 + 1, highlight_passes);
        }''')
    replace('\tAddColoredUnion(glow, vertical,', '''    if (color_owner) {
        const std::vector<float>* rays[]={&vertical,&horizontal,&diagonal,&diagonal2,&highlight};
        for (size_t i=0; i<glow.size(); ++i) {
            auto &g=glow[i];
            for (const auto *ray:rays) {
                const float alpha=(*ray)[i*4+3];
                if ((double)alpha <= 0.001) continue;
                const float inv=1.0f/alpha;
                const float a=Clamp01(alpha*scale);
                g.r = inv*(*ray)[i*4]*a+g.r;
                g.g = inv*(*ray)[i*4+1]*a+g.g;
                g.b = inv*(*ray)[i*4+2]*a+g.b;
                g.a = a+g.a;
            }
            if (g.a>0.0f) {
                g.a=Clamp01(g.a);
                const float inv=1.0f/g.a;
                g.r=inv*g.r; g.g=inv*g.g; g.b=inv*g.b;
            }
        }
    } else {
    AddColoredUnion(glow, vertical,''')
    replace('\tstd::vector<FloatRGBA> composed((size_t)work_width * work_height);',
            '\t}\n\tstd::vector<FloatRGBA> composed((size_t)work_width * work_height);')
    if unnormalized:
        # AEX's four-channel owner uses unnormalised box sums. Preserve
        # FLOAT64 accumulation and cast at each pass, not a final rescale.
        assert body.count('bool recovered_scalar_box = false)') == 2
        body=body.replace('bool recovered_scalar_box = false)',
                          'bool recovered_scalar_box = false, bool normalize = true)')
        replace('const double scale = 1.0 / (double)length;',
                'const double scale = normalize ? 1.0 / (double)length : 1.0;')
        replace('passes, recovered_scalar_box);', 'passes, recovered_scalar_box, normalize);')
        replace('passes,info.blur_mode,false,true);', 'passes,info.blur_mode,false,true,false);')
        header=(ROOT/'core/kirakira_highlight.h').read_text()
        header=header.replace('#pragma once','').replace('namespace olm::kirakira {','namespace c16_color {')
        header=header.replace('const double scale = 1.0 /\n\t\t\t(static_cast<double>(kernel_size) * kernel_size);',
                              'const double scale = 1.0;')
        header=header.replace('const double scale = normalize ? 1.0 /\n\t\t\t(static_cast<double>(kernel_size) * kernel_size) : 1.0;',
                              'const double scale = 1.0;')
        replace('namespace {', header+'\nnamespace {')
        replace('const auto ray=olm::kirakira::highlight_isotropic_box_blur(',
                'const auto ray=c16_color::highlight_isotropic_box_blur(')
        replace('for (const auto *ray:rays) {', '''float norms[5] = {(float)info.vertical_length,(float)info.horizontal_length,
                (float)info.diagonal_length,(float)info.diagonal2_length,
                (float)((info.highlight_radius*2+1)*(info.highlight_radius*2+1))};
            if (info.blur_mode == 2) {
                for (int c=0;c<4;++c) norms[c]=norms[c]*norms[c]*norms[c];
                norms[4]=norms[4]*norms[4]; norms[4]=norms[4]*norms[4];
            }
            int ray_index=0;
            for (const auto *ray:rays) {
                const float divisor=norms[ray_index++];
                const float norm=divisor == 0.0f ? 0.0f : 1.0f/divisor;''')
        replace('const float a=Clamp01(alpha*scale);','const float a=Clamp01(alpha*norm);')
        for c in ('r','g','b'):
            body=body.replace('*a+g.'+c+';', '*a*scale+g.'+c+';')
    return body


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True,help='Scalar-only source before the four-channel promotion')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--unnormalized',action='store_true')
    args=p.parse_args()
    assert args.output.resolve().is_relative_to(ROOT/'orchestra/state')
    args.output.write_text(candidate(args.source.read_text(), args.unnormalized))
