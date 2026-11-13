"""Fail-closed translator for this port's small C++ geometry subset.

Keeps expressions, branch bodies, call order and C++ switch fallthrough.
It is not a general C++ compiler. Unrecognized statements raise an exception.
Only diagnostic printing/histograms are omitted (normal plug-in values are zero).
Generated Rust calls checked Rust storage and previously verified scan/weight leaves.
"""
from pathlib import Path
import re, json, hashlib, argparse

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'mac/OLMSmoother2/Mac'
TYPE={'int':'i32','long':'i32','float':'f32','bool':'bool','uint8_t':'u8','uint32_t':'u32','size_t':'usize','void':'()','GridDesc':"GridDesc<'_>"}
RENAMES={'in':'input_xy','self':'self_value'}
TOKEN=re.compile(r'"(?:\\.|[^"\\])*"|0x[0-9a-fA-F]+|\d+\.\d*(?:[eE][+-]?\d+)?f?|\d+|[A-Za-z_]\w*|::|->|\+\+|--|<<|>>|<=|>=|==|!=|&&|\|\||\*=|/=|\+=|-=|\[\[|\]\]|[^\s]')

def clean(s):
    return re.sub(r'//[^\n]*|/\*.*?\*/','',s,flags=re.S)

def functions(text):
    result={}
    for m in re.finditer(r'static\s+(?:inline\s+)?(bool|int|long|void)\s+(\w+)\s*\(([^)]*)\)\s*\{',text):
        start=m.end(); depth=1; i=start
        while depth:
            depth+=(text[i]=='{')-(text[i]=='}'); i+=1
        result[m[2]]=(m[1],m[3],text[start:i-1])
    return result

class Parser:
    PRE={'=':1,'+=':1,'-=':1,'*=':1,'/=':1,'?':2,'||':3,'&&':4,'|':5,'^':6,'&':7,'==':8,'!=':8,'<':9,'>':9,'<=':9,'>=':9,'<<':10,'>>':10,'+':11,'-':11,'*':12,'/':12,'%':12}
    def __init__(self,tokens,arrays=(),refs=()): self.t=tokens; self.i=0; self.arrays=set(arrays); self.refs=set(refs)
    def peek(self): return self.t[self.i] if self.i<len(self.t) else ''
    def pop(self): v=self.peek(); self.i+=1; return v
    def need(self,v):
        a=self.pop()
        assert a==v,(v,a,self.t[max(0,self.i-10):self.i+10])
    def expression(self,level=0):
        v=self.pop()
        if v=='(':
            if self.peek() in TYPE and self.t[self.i+1]==')':
                typ=self.pop();self.need(')'); out=f'({self.expression(13)} as {TYPE[typ]})'
            else: out='('+self.expression()+')';self.need(')')
        elif v in ['!','~','-','+','&','*']:
            out=('!' if v=='~' else v)+self.expression(13)
        else:
            out=RENAMES.get(v,v)
            if out in self.refs: out='(*'+out+')'
            out=re.sub(r'(?<=\d)f$', '_f32',out)
        while True:
            op=self.peek()
            if op in ['.','->']:
                self.pop();field=self.pop();out+='.'+('weight' if field=='w' and out.startswith('poly.samples') else field)
            elif op=='[':
                self.pop();idx=self.expression();self.need(']');out+=f'[({idx}) as usize]'
            elif op=='(':
                self.pop();args=[]
                while self.peek()!=')':
                    args.append(self.expression())
                    if self.peek()!=',': break
                    self.pop()
                self.need(')')
                if out.startswith('scan_'):
                    args[0]='&mut '+args[0]
                    if args[2] in self.arrays: args[2]='&'+args[2]
                elif out.startswith('win_') or out.startswith('endpoint_'):
                    args=[('&'+a if a in self.arrays else a) for a in args]
                if out=='win_weight_pair': args[0]='&mut '+args[0].lstrip('&')
                if out=='append_weighted' and len(args)==6: args.append('1')
                if args and args[0]=='poly' and (out.startswith('win_') or out=='append_weighted'):
                    args=args[1:]+args[:1]
                out+='('+','.join(args)+')'
            else: break
        while self.peek() in self.PRE and self.PRE[self.peek()]>=level:
            op=self.pop();prec=self.PRE[op]
            if op=='?':
                yes=self.expression();self.need(':');no=self.expression(prec)
                out=f'(if {out} {{ {yes} }} else {{ {no} }})'
            else:
                right=self.expression(prec if prec==1 else prec+1)
                out=f'{out} {op} {right}' if prec==1 else f'({out} {op} {right})'
        if self.peek() in ['++','--']:
            op=self.pop();out+= ' += 1' if op=='++' else ' -= 1'
        return out
    def statements(self,end=''):
        out=[]
        while self.peek() and self.peek()!=end: out.append(self.statement())
        return '\n'.join(out)
    def block(self):
        self.need('{');out=self.statements('}');self.need('}');return '{\n'+out+'\n}'
    def statement(self):
        token=self.peek()
        if token=='{': return self.block()
        if token==';': self.pop();return ''
        if token=='if':
            self.pop();self.need('(');cond=self.expression();self.need(')')
            if any(x in cond for x in ['trace_this_pixel','g_olmsmoother2_trace','hist_enabled']):
                self.need('{');depth=1
                while depth:
                    t=self.pop();depth+=(t=='{')-(t=='}')
                return ''
            body=self.statement();other=''
            if self.peek()=='else': self.pop();other=self.statement()
            if any(x in cond for x in ['trace_this_pixel','g_olmsmoother2_trace','hist_enabled']): return ''
            return f'if {cond} {{ {body} }}'+(f' else {{ {other} }}' if other else '')
        if token in ['while','for']:
            self.pop();self.need('(')
            if token=='for':
                if self.peek()==';': self.pop();init=''
                else: init=self.statement()
                cond='true' if self.peek()==';' else self.expression();self.need(';')
                inc='' if self.peek()==')' else self.expression()
            else: init='';cond=self.expression();inc=''
            self.need(')');body=self.statement()
            return f'{{ {init} while {cond} {{ {body} {inc}; }} }}'
        if token=='switch':
            self.pop();self.need('(');key=self.expression();self.need(')');self.need('{');arms=[]
            while self.peek()!='}':
                labels=[]
                while self.peek() in ['case','default']:
                    label=self.pop();labels.append('_' if label=='default' else self.pop());self.need(':')
                assert labels,self.t[self.i:self.i+10]
                body=[];fall=False
                while self.peek() not in ['case','default','}']:
                    if self.peek()=='[[':
                        self.need('[[');self.need('fallthrough');self.need(']]');self.need(';');fall=True
                    elif self.peek()=='break': self.pop();self.need(';')
                    else: body.append(self.statement())
                arms.append([labels,body,fall])
            self.need('}')
            for i in reversed(range(len(arms)-1)):
                if arms[i][2]: arms[i][1]+=arms[i+1][1]
            return 'match '+key+' {\n'+'\n'.join(' | '.join(l)+' => {\n'+'\n'.join(b)+'\n},' for l,b,_ in arms)+'\n}'
        if token in ['return','break','continue']:
            self.pop();value='' if self.peek()==';' else self.expression();self.need(';');return token+' '+value+';'
        if token=='const': self.pop();token=self.peek()
        if token in TYPE:
            typ=self.pop();decl=[]
            while True:
                pointer=self.peek()=='*'; ref=self.peek()=='&'
                if pointer or ref:self.pop()
                name=RENAMES.get(self.pop(),self.t[self.i-1]);n=None
                if self.peek()=='[':self.pop();n=self.pop();self.need(']');self.arrays.add(name)
                value=None
                if self.peek()=='=':
                    self.pop()
                    if self.peek()=='{':
                        self.pop();values=[]
                        while self.peek()!='}':
                            values.append(self.expression())
                            if self.peek()!=',':break
                            self.pop()
                        self.need('}');value='['+','.join(values)+']'
                    else:value=self.expression()
                if name=='trace_this_pixel': pass
                elif ref:
                    self.refs.add(name);decl.append(f'let {name} = &mut {value};')
                else:
                    rt=TYPE[typ]
                    if pointer:rt='&[u8]' if typ=='uint8_t' else '&[i32]'
                    if n:rt=f'[{rt};{n}]'
                    if value is None:
                        value=f'[{"0.0" if typ=="float" else "0"};{n}]' if n else ('0.0' if typ=='float' else 'false' if typ=='bool' else '0')
                    decl.append(f'let mut {name}: {rt} = {value};')
                if self.peek()!=',':break
                self.pop()
            self.need(';');return '\n'.join(decl)
        if token=='(' and self.t[self.i+1]=='void':
            while self.pop()!=';': pass
            return ''
        if token=='std':
            while self.pop()!=';':pass
            return ''
        if token in ['++','--']:
            op=self.pop();value=self.expression();self.need(';');return value+(' += 1;' if op=='++' else ' -= 1;')
        value=self.expression();self.need(';')
        if 'g_olmsmoother2_current_switch_idx' in value:return ''
        return value+';'

def translate(name,definition):
    ret,args,body=definition; params=[]; arrays=[]
    for arg in args.split(','):
        arg=arg.strip().split('=')[0].strip()
        m=re.fullmatch(r'(const )?(\w+)\s*([&*]?)\s*(\w+)',arg)
        assert m,(name,arg)
        const,typ,ptr,n=m.groups();n=RENAMES.get(n,n)
        if typ=='SmootherPolygon': rt='&State' if const else '&mut State'
        elif typ=='GridDesc':rt='&GridDesc'
        elif ptr=='*':rt='&[i32]'
        else:rt=TYPE[typ]
        params.append(f'{n}: {rt}')
    if params and params[0].startswith('poly:'):params=params[1:]+params[:1]
    parser=Parser(TOKEN.findall(body),arrays)
    converted=parser.statements()
    converted=converted.replace('(win_FUN_180011300(poly) != 0)', 'win_FUN_180011300(poly)')
    return f'pub(super) fn {name}('+','.join(params)+f') -> {TYPE[ret]} {{\n{converted}\n}}\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['leaves','all'],default='all');args=ap.parse_args()
    files=['classification','cardinal_leaves']
    if args.stage=='all':files+=['corner_samples','polygon_dispatch']
    output=['// @generated by generate_geometry.py; do not edit.\nuse super::*;\n'];manifest=[]
    for f in files:
        path=SOURCE/f'OLMSmoother2_{f}.inc';text=clean(path.read_text(encoding='utf-8')); funcs=functions(text)
        for name,definition in funcs.items():
            if name.startswith('scan_') or name in ['cp_b','grid_of','win_FUN_180010550','win_FUN_180013630_trapezoid','build_polygon']:continue
            if args.stage=='leaves' and (name.startswith('win_disp_') or name.startswith('win_cardinal_')):continue
            output.append(translate(name,definition));manifest.append({'source':path.name,'function':name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    if args.stage=='all':
        body=funcs['build_polygon'][2]
        tokens=TOKEN.findall(body[body.index('switch (idx)'):])
        parser=Parser(tokens)
        dispatch=parser.statement().replace('(win_FUN_180011300(poly) != 0)', 'win_FUN_180011300(poly)')
        count=tokens[:parser.i].count('case')
        assert count==222,count
        output.append('pub(super) fn dispatch(idx:i32,poly:&mut State) { const STEP:f32=0.125;\n'+dispatch+'\n}')
        manifest.append({'source':path.name,'function':'dispatch','case_labels':count,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    leaves=[m['function'] for m in manifest if m['function'].startswith('win_leaf_')]
    parameterized={'f220','f0e0','f1d0','f090','f270','f130','f2c0','f180'}
    output.append('#[cfg(test)]\npub(super) fn call_leaf(id:usize,p2:&[i32],scale:f32,poly:&mut State)->bool { match id {')
    for i,n in enumerate(leaves):output.append(f'{i} => {n}(p2,'+('scale,' if n.split('_')[-1] in parameterized else '')+'poly),')
    output.append('_ => panic!("unknown leaf") } }')
    (HERE/'src/geometry_generated.rs').write_text('\n'.join(output),encoding='utf-8')
    cpp=['// @generated names only; function implementations are the unchanged C++ includes.\n',
         'extern "C" int sm2_ref_leaf(int id, FPix *pixels, const uint8_t *classes, int w, int h, int x, int y, float smooth, float extra, const int *desc, float scale, PolyVertex *out, int *count) {',
         'FPlane plane{pixels,(size_t)w*sizeof(FPix),0}; SmootherPolygon p{}; p.plane=&plane; p.cplane_base=classes; p.cplane_w=w; p.cplane_h=h; p.cplane_stride=w*4; p.cur_x=x; p.cur_y=y; p.smoothness_n=smooth; p.extra_n=extra; bool result=false; switch(id) {']
    for i,n in enumerate(leaves):cpp.append(f'case {i}: result={n}(p,desc'+(',scale' if n.split('_')[-1] in parameterized else '')+'); break;')
    cpp.append('default: return -1; } *count=p.count; std::memcpy(out,p.samples,p.count*sizeof(PolyVertex)); return result; }')
    (HERE/'tests/leaf_reference.inc').write_text('\n'.join(cpp),encoding='utf-8')
    (HERE/'geometry-generation.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(manifest)} functions ({args.stage})')

if __name__=='__main__':main()
