"""F52c standalone bundle transport; packed bytes plus negotiated rectangle."""
import re,struct
from pathlib import Path
from core import command
from .public import geometry_environment
HOST=Path.home()/'.cache/olm-emu/worker-F52c-bundle/plugin-host'
def candidate(adapter,case,directory,route,deadline):
 declarations=getattr(adapter,'declarations',None) or adapter.binding['parameters']
 schema=directory/'bundle-declarations.txt';params=directory/'bundle-params.txt'
 types=[0]*(max(d['slot'] for d in declarations)+1)
 for d in declarations:types[d['slot']]=d['param_type']
 schema.write_text(str(len(types))+'\n'+'\n'.join(map(str,types))+'\n')
 params.write_text(''.join(f"{p['slot']} {p['kind']} "+(' '.join(map(str,p['value'])) if isinstance(p['value'],list) else str(p['value']))+'\n' for p in case['parameters']))
 trace=directory/'bundle-refusals.txt';trace.unlink(missing_ok=True)
 env=dict(adapter.env,OLM_REFUSAL_TRACE=str(trace))
 if adapter.name=='olmkirakira':env['OLM_NATIVE_PARAMETER_PROFILE']='kirakira-default-ramps'
 geometry_environment(case,directory,env)
 status,raw,err=command([HOST,adapter.executable,*case['geometry'],case['depth'],case['rowbytes_padding'],int(route=='smart'),schema,params],data=case['pixels'],timeout=adapter.timeout,deadline=deadline,env=env)
 guards=trace.read_text().splitlines() if trace.exists() else [];text=err.decode(errors='replace')
 if status['status']!='ok':return dict(status,diagnostic=text[-1600:]),b'',guards
 if len(raw)<4:return {'status':'harness_error','diagnostic':'missing bundle return code'},b'',guards
 error=struct.unpack('<i',raw[:4])[0];raw=raw[4:]
 metadata=dict(line.split(' ',1) for line in text.splitlines() if line.startswith('GEOMETRY'))
 if 'F47c unsupported/invalid callback:' in text:
  return {'status':'harness_error','error':error,'diagnostic':text[-2000:]},b'',guards
 if error:return {'status':'refusal','error':error,'metadata':metadata,'native_trace':text},b'',guards
 rect=list(map(int,metadata['GEOMETRY'].split())) if route=='smart' else [0,0,*case['geometry']]
 if len(raw)!=(rect[2]-rect[0])*(rect[3]-rect[1])*case['depth']//8*4:
  return {'status':'harness_error','diagnostic':'negotiated bundle output length'},b'',guards
 return {'status':'ok','error':0,'output_rect':rect,'metadata':metadata,'native_trace':text},raw,guards
