"""Extract only this ticket's baseline cores into isolated scratch files."""
import subprocess
BASELINE='a3b3b263f7cea3a92013f935bd9879762c1d4e28'
def cores(module, root, scratch, divisor=False, wrap=False):
 for name in ('dblur_frontonly.cpp','dblur_rowdriver.cpp'):
  original=root/'core'/name
  body=subprocess.check_output(['git','show',f'{BASELINE}:core/{name}'],cwd=root,text=True)
  if divisor and name=='dblur_frontonly.cpp':
   pos=body.index('static int render_minimal_argb32(')
   body=body[:pos]+body[pos:].replace('if (component_divisor <= 0.0f) component_divisor = 1.0f;','// Preserve original zero divisor.')
  if wrap and name=='dblur_rowdriver.cpp':
   body=body.replace('if (start - backward < 0)', 'if (((static_cast<std::uint32_t>(start) - static_cast<std::uint32_t>(backward)) & 0x80000000u) != 0)')
  for hdr in (root/'core').glob('*.h'):body=body.replace('"'+hdr.name+'"','"'+str(hdr)+'"')
  body=body.replace('../ucrtmath/include/ucrtmath.h',str(root/'ucrtmath/include/ucrtmath.h'))
  dst=scratch/name;dst.write_text(body)
  module.CORES=[dst if p.name==name else p for p in module.CORES]
