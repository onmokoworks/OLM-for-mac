"""Extract small pure-kernel tests only from hash-verified exact oracle cases."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
campaign=Path(sys.argv[1]).resolve()
out=HERE/'tests/golden';out.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
summary=json.loads((campaign/'summary.json').read_text())
lines=['use olm_uv_map::algorithm::{render,Layout,Params};\n']
manifest=[]
for depth in [8,16,32]:
    for method in [1,2,3]:
        chosen=None
        for row in summary['results']:
            if row['route']!=f'smart{depth}' or row['status']!='exact':continue
            path=campaign/row['directory'];case=json.loads((path/'case.json').read_text())
            params={a['slot']:a for a in case['case']['assignments']}
            if params.get(2,{}).get('value',3)!=method or min(case['case']['size'])<3:continue
            chosen=(path,case,params);break
        if chosen is None:raise ValueError('no qualified case')
        path,case,params=chosen
        for file,digest in case['assets'].items():
            if sha((path/file).read_bytes())!=digest:raise ValueError(f'asset drift: {file}')
        bpp=depth//2
        def convert(png):
            image=Image.open(png).convert('RGBA');arr=np.array(image)[:,:,[3,0,1,2]]
            if depth==16:arr=(arr.astype(np.float32)*np.float32(1/255)*np.float32(32768)+np.float32(.5)).astype('<u2')
            if depth==32:arr=arr.astype(np.float32)*np.float32(1/255)
            return image.size,arr.tobytes()
        (w,h),uv=convert(path/'input.png');(tw,th),tex=convert(path/params[1]['layer'])
        if depth==8:expected=convert(path/'reference.png')[1]
        else:
            # Request sidecars are RGBA; fixture checkpoints are separately ARGB.
            raw=(path/('reference.rgba16le' if depth==16 else 'reference.rgba32f-le')).read_bytes()
            dtype='<u2' if depth==16 else '<u4'
            expected=np.frombuffer(raw,dtype=dtype).reshape(-1,4)[:,[3,0,1,2]].tobytes()
        name=f'm{method}-d{depth}';smooth=params.get(3,{}).get('value',.5)
        for kind,data in [('uv',uv),('texture',tex),('expected',expected)]:
            (out/f'{name}-{kind}.bin').write_bytes(data)
        lines.append(f'''#[test]
fn m{method}_d{depth}() {{
 let a=Layout{{width:{w},height:{h},row_bytes:{w*bpp},bytes_per_pixel:{bpp},origin:(0,0)}};
 let t=Layout{{width:{tw},height:{th},row_bytes:{tw*bpp},..a}};
 let mut output=vec![0;{w*h*bpp}];
 render(include_bytes!("golden/{name}-uv.bin"),a,Some((include_bytes!("golden/{name}-texture.bin"),t)),&mut output,a,Params{{method:{method},smoothness:{smooth}f32}}).unwrap();
 let expected=include_bytes!("golden/{name}-expected.bin");
 assert_eq!(output.len(),expected.len());
 assert!(output.iter().zip(expected).all(|(a,b)|a==b), "first differing byte: {{:?}}",output.iter().zip(expected).position(|(a,b)|a!=b));
}}
''')
        manifest.append(dict(name=name,source=str(path),reference=case['reference'],candidate=case['candidate'],harness=case['harness'],uv_sha256=sha(uv),texture_sha256=sha(tex),expected_sha256=sha(expected)))
(HERE/'tests/golden.rs').write_text(''.join(lines))
(out/'provenance.json').write_text(json.dumps(manifest,indent=2))
print('captured',len(manifest),'original-backed tests')
