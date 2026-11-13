"""Reproducible, strict Clang-AST translation of the existing v1 C++ kernels.

No C++ kernels are linked into the production DLL. This development tool emits
Rust control-flow machines, preserving C++ promotions, casts and branch order.
Unknown AST constructs fail generation rather than silently approximating them.
"""
from pathlib import Path
import json, re, subprocess, sys

HERE = Path(__file__).resolve().parent
CRATE = HERE.parent
ROOT = CRATE.parents[2]
SRC = ROOT / 'mac/OLMSmoother/Mac'
WORK = HERE / 'work'
WORK.mkdir(exist_ok=True)

def prepare():
    port = (SRC/'OLMSmoother_port.cpp').read_text(encoding='utf-8')
    constants = port[port.index('static const float DAT_'):port.index('// ============================================================================\n// Plugin lifecycle')]
    header = '''#include <cstdint>
#include <cstddef>
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <new>
struct PF_EffectWorld { void *data; int width,height,rowbytes; };
typedef int A_long; typedef int PF_Err;
const int PF_Err_NONE=0;
struct PF_Pixel8 { uint8_t alpha,red,green,blue; };
struct PF_Pixel16 { uint16_t alpha,red,green,blue; };
'''
    body = constants
    for name in ['state_math','pixel_helpers','classifiers','edge_walkers','subhandler16','subhandler8','interpolation','render']:
        s = (SRC/f'OLMSmoother_{name}.inc').read_text(encoding='utf-8')
        if name == 'render': s=s[:s.index('// 32-bit float')]
        body += '\n' + s
    tu = WORK/'source.cpp'
    tu.write_text(header+body,encoding='utf-8')
    with (WORK/'ast.json').open('w',encoding='utf-8') as out:
        subprocess.run(['C:/Program Files/LLVM/bin/clang++.exe','-std=c++17','-fsyntax-only','-Wno-everything','-I'+str(SRC),'-Xclang','-ast-dump=json',str(tu)],stdout=out,check=True)

def walk(n):
    yield n
    for c in n.get('inner',[]): yield from walk(c)

def ty(n):
    s=n['type']['qualType'] if isinstance(n,dict) else n
    s=re.sub(r'\b(const|volatile|struct)\s*','',s).strip()
    if s.endswith('&'): return '*mut '+ty(s[:-1])
    if s.endswith('*'): return '*mut '+ty(s[:-1])
    m=re.fullmatch(r'(.+)\[(\d+)\]',s)
    if m: return f'[{ty(m[1])}; {m[2]}]'
    if s.startswith('Linear'): return 'Eval'
    return {'void':'()','bool':'bool','char':'i8','unsigned char':'u8','uint8_t':'u8',
      'short':'i16','short int':'i16','unsigned short':'u16','uint16_t':'u16','int16_t':'i16',
      'int':'i32','unsigned int':'u32','int32_t':'i32','uint32_t':'u32','A_long':'i32','PF_Err':'i32',
      'long long':'i64','unsigned long long':'u64','int64_t':'i64','uint64_t':'u64',
      'uintptr_t':'u64','size_t':'u64','__size_t':'u64','float':'f32','double':'f64',
      'SubHandler8Regs':'Regs','Classifier8TailRegs':'Regs','SubHandler8Memory':'Memory',
      'Classifier16Memory':'Memory','EdgeWalker16Memory':'Memory','Classifier8TailMemory':'Memory',
      'PF_EffectWorld':'World','PF_Pixel8':'Pixel8','PF_Pixel16':'Pixel16'}.get(s,s)

def zero(t):
    if t.startswith('*'): return 'std::ptr::null_mut()'
    if t.startswith('['):
        a,b=t[1:-1].rsplit(';',1);return f'[{zero(a.strip())};{b}]'
    if t=='bool':return 'false'
    if t in ('f32','f64'):return '0.0'
    if t in ('Regs','Memory','Eval'):return f'{t}::default()'
    return '0'

def clean(n):
    while n.get('kind') in ('ImplicitCastExpr','ParenExpr','ConstantExpr','ExprWithCleanups') and n.get('inner'): n=n['inner'][0]
    return n

class Translator:
    def __init__(self,fn):
        self.fn=fn;self.names={};self.locals={};self.lambdas={};self.blocks={};self.labels={};self.seq=0
        self.params=[c for c in fn['inner'] if c['kind']=='ParmVarDecl']
        self.body=next(c for c in fn['inner'] if c['kind']=='CompoundStmt')
        for c in walk(self.body):
            if c.get('kind')=='LabelStmt': self.labels[c['declId']]=self.new()
        for c in self.params: self.name(c)
        for c in walk(self.body):
            if c.get('kind')=='VarDecl':
                if '(lambda at ' in c['type']['qualType']:
                    self.lambdas[c['id']]=next(x for x in walk(c) if x.get('kind')=='LambdaExpr')
                else:self.locals[self.name(c)]='[u64; 8]' if re.fullmatch(r'curve_.*_buf',c.get('name','')) else ty(c)
    def name(self,n):
        if n['id'] not in self.names:
            raw=n.get('name','arg'+str(len(self.names)))
            if raw in ('ref','type','loop','match','in'):raw+='_' 
            name=raw
            if name in self.names.values():name+='_'+str(len(self.names))
            self.names[n['id']]=name
        return self.names[n['id']]
    def new(self):
        self.seq+=1;return self.seq
    def block(self,s):
        i=self.new();self.blocks[i]=s;return i
    def jump(self,i):return f'pc={i}; continue;'
    def expr(self,n):
        k=n['kind'];cs=n.get('inner',[]);t=ty(n) if 'type' in n else '';e=self.expr
        if k=='DeclRefExpr':
            d=n['referencedDecl'];name=d['name']
            if d['id'] in self.names:return self.names[d['id']]
            if name=='kStack':return 'KSTACK'
            if name=='kModule':return 'KMODULE'
            return name
        if k in ('ParenExpr','ConstantExpr','ExprWithCleanups'):return '('+e(cs[0])+')'
        if k in ('IntegerLiteral','CharacterLiteral'):return str(n['value'])+'_'+t
        if k=='FloatingLiteral':return str(n['value'])+('_'+t if '.' in str(n['value']) or 'E' in str(n['value']) or 'e' in str(n['value']) else '.0_'+t)
        if k=='CXXBoolLiteralExpr':return str(n['value']).lower()
        if k=='CXXNullPtrLiteralExpr':return 'std::ptr::null_mut::<u8>()'
        if k in ('ImplicitCastExpr','CStyleCastExpr','CXXFunctionalCastExpr','CXXReinterpretCastExpr','CXXStaticCastExpr'):
            v=e(cs[0]);src=ty(cs[0]);ck=n.get('castKind')
            if ck=='ArrayToPointerDecay':return f'({v}).'+('as_ptr()' if 'DAT_' in v else 'as_mut_ptr()')+f' as {t}'
            if ck in ('FunctionToPointerDecay','LValueToRValue','NoOp','DerivedToBase') or t==src:return v
            if t=='()':return f'{{let _ = {v};}}'
            if t=='bool':return f'({v} != '+('std::ptr::null_mut()' if src.startswith('*') else '0')+')'
            if src=='f32' and t in ('i32','u32','i16','u16','u8','i8'):
                return f'(olm_math::x86::cvttss2si({v}) as {t})'
            return f'({v} as {t})'
        if k=='MemberExpr':
            obj=e(cs[0]);return f'(*{obj}).{n["name"]}' if n.get('isArrow') else f'({obj}).{n["name"]}'
        if k=='ArraySubscriptExpr':return f'(*({e(cs[0])}).wrapping_offset({e(cs[1])} as isize))'
        if k in ('BinaryOperator','CompoundAssignOperator'):
            op=n['opcode'];a=e(cs[0]);b=e(cs[1]);ta=ty(cs[0])
            if op=='=':return f'{{{a} = {b}; {a}}}'
            if op==',':return f'{{let _ = {a}; {b}}}'
            if k=='CompoundAssignOperator':
                pure=op[:-1];v=self.binary(a,b,pure,ta);return f'{{{a} = ({v}) as {ta}; {a}}}'
            return self.binary(a,b,op,ta)
        if k=='UnaryOperator':
            op=n['opcode'];v=e(cs[0]);st=ty(cs[0])
            if op=='&':return f'(&raw mut {v})'
            if op=='*':return f'(*{v})'
            if op=='!':return f'(!{v})'
            if op=='~':return f'(!{v})'
            if op=='-':return f'({v}).wrapping_neg()' if st[0:1] in ('u','i') else f'(-{v})'
            if op=='+':return v
            if op in ('++','--'):
                upd=self.binary(v,'1', '+' if op=='++' else '-',st)
                return f'{{let old={v}; {v}={upd}; '+('old' if n.get('isPostfix') else v)+'}'
        if k=='ConditionalOperator':return f'(if {e(cs[0])} {{ {e(cs[1])} }} else {{ {e(cs[2])} }})'
        if k=='CXXConstructExpr':return zero(t)
        if k=='InitListExpr':return '['+', '.join(e(c) for c in cs)+']'
        if k=='UnaryExprOrTypeTraitExpr':
            st=ty(n['argType']['qualType']) if 'argType' in n else ty(cs[0])
            return f'(std::mem::size_of::<{st}>() as {t})'
        if k=='CallExpr':
            fn=e(cs[0]);args=cs[1:]
            if fn=='fprintf':return '()'
            if fn=='trace_xy_enabled':return 'false'
            if fn in ('floorf','ceilf'):return f'({e(args[0])}).'+('floor' if fn=='floorf' else 'ceil')+'()'
            return fn+'('+', '.join(e(c) for c in args)+')'
        if k=='CXXMemberCallExpr':
            method=cs[0]['name'];obj=e(cs[0]['inner'][0]);args=cs[1:]
            if method.startswith('~'):return '()'
            if method=='Evaluate':return f'(*{obj}).evaluate('+','.join(e(c) for c in args)+')'
            return f'{obj}.{method}('+','.join(e(c) for c in args)+')'
        if k=='CXXOperatorCallExpr':
            d=clean(cs[1])['referencedDecl'];l=self.lambdas[d['id']]
            if d['name']=='put':return f'M.write64(KSTACK+{e(cs[2])} as u64,{e(cs[3])} as u64)'
            record=l['inner'][0]
            method=next(x for x in record['inner'] if x.get('name')=='operator()')
            sub=Translator(method)
            sub.names.update(self.names);sub.lambdas.update(self.lambdas)
            # Lambda parameter/local IDs are disjoint from their enclosing scope.
            for p in sub.params:sub.name(p)
            code=sub.code(closure=True)
            return '('+code+')('+', '.join(e(c) for c in cs[2:])+')'
        if k=='CXXNewExpr':
            ctor=cs[0];kind={'LinearOffsetFunction':0,'LinearOffsetOneValue':1,'LinearOffsetZeroOneValue':2,'LinearOffsetZeroValue':3,'LinearThreeOffsetFunction':4}[ctor['type']['qualType']]
            args=[e(c) for c in ctor.get('inner',[])];args+=['0.0']*(4-len(args))
            return '{let p='+e(cs[1])+' as *mut Eval; p.write_unaligned(Eval::new('+str(kind)+', '+', '.join(args)+')); p}'
        raise ValueError(('expression',k,n.get('range')))
    def binary(self,a,b,op,t):
        if t.startswith('*') and op in ('+','-'):return f'({a}).wrapping_offset('+('-' if op=='-' else '')+f'({b} as isize))'
        if op in ('+','-','*','<<','>>') and re.fullmatch('[ui](8|16|32|64|size)',t):
            method={'+':'add','-':'sub','*':'mul','<<':'shl','>>':'shr'}[op]
            return f'({a}).wrapping_{method}({b}'+(' as u32' if op in ('<<','>>') else '')+')'
        return f'({a} {op} {b})'
    def stmt(self,n,nxt,br=None,cont=None):
        k=n.get('kind');cs=n.get('inner',[]);s=self.stmt;j=self.jump
        if not k or k=='NullStmt':return nxt
        if k=='CompoundStmt':
            for c in reversed(cs):nxt=s(c,nxt,br,cont)
            return nxt
        if k=='DeclStmt':
            code=[]
            for c in cs:
                if c['kind']!='VarDecl' or c['id'] in self.lambdas:continue
                init=[x for x in c.get('inner',[]) if not x['kind'].endswith('Attr')]
                if init:code.append(self.name(c)+' = '+self.expr(init[-1])+';')
            return self.block('\n'.join(code)+j(nxt)) if code else nxt
        if k=='LabelStmt':
            i=self.labels[n['declId']];self.blocks[i]=j(s(cs[0],nxt,br,cont));
            return i
        if k=='GotoStmt':return self.block(j(self.labels[n['targetLabelDeclId']]))
        if k=='ReturnStmt':return self.block('return '+(self.expr(cs[0]) if cs else '')+';')
        if k=='IfStmt':
            a=s(cs[1],nxt,br,cont);b=s(cs[2],nxt,br,cont) if len(cs)>2 else nxt
            return self.block(f'if {self.expr(cs[0])} {{pc={a};}} else {{pc={b};}} continue;')
        if k in ('WhileStmt','DoStmt'):
            test=self.new();cond,body=(cs[0],cs[1]) if k=='WhileStmt' else (cs[1],cs[0])
            start=s(body,test,nxt,test)
            self.blocks[test]=f'if {self.expr(cond)} {{pc={start};}} else {{pc={nxt};}} continue;'
            return test if k=='WhileStmt' else start
        if k=='ForStmt':
            init,_,cond,inc,body=cs;test=self.new();increment=s(inc,test,nxt,test);start=s(body,increment,nxt,increment)
            self.blocks[test]=f'if {self.expr(cond)} {{pc={start};}} else {{pc={nxt};}} continue;'
            return s(init,test,br,cont)
        if k=='BreakStmt':return self.block(j(br))
        if k=='ContinueStmt':return self.block(j(cont))
        return self.block('let _ = '+self.expr(n)+';'+j(nxt))
    def code(self,closure=False):
        ret=self.fn['type']['qualType'].split('(')[0].strip()
        if '->' in self.fn['type']['qualType']:ret=self.fn['type']['qualType'].split('->')[-1].strip()
        ret=ty(ret)
        end=self.block('return '+('' if ret=='()' else zero(ret))+';')
        start=self.stmt(self.body,end)
        # Collapse linear chains and forwarding labels; preserve each branch.
        for _ in range(3):
            for i,code in list(self.blocks.items()):
                seen={i}
                while True:
                    m=re.search(r'pc=(\d+); continue;$',code)
                    if not m:break
                    dest=int(m[1])
                    if dest in seen:break
                    seen.add(dest);code=code[:m.start()]+self.blocks[dest]
                self.blocks[i]=code
        reachable=set();todo=[start]
        while todo:
            i=todo.pop()
            if i in reachable:continue
            reachable.add(i);todo += [int(v) for v in re.findall(r'pc=(\d+);',self.blocks[i])]
        args=', '.join('mut '+self.name(p)+': '+ty(p) for p in self.params)
        pre=('|'+args+'| -> '+ret if closure else 'pub(super) unsafe fn '+self.fn['name']+'('+args+') -> '+ret)
        local='\n'.join(f'let mut {n}: {t} = {zero(t)};' for n,t in self.locals.items())
        blocks='\n'.join(f'{i} => {{ {self.blocks[i]} }},' for i in sorted(reachable))
        return pre+' {\n'+local+f'\nlet mut pc: u32={start};\nloop {{match pc {{\n'+blocks+'\n_ => unreachable!(),\n}}}\n'

def generate():
    ast=json.loads((WORK/'ast.json').read_text(encoding='utf-8'))
    names=['ColorBlend16','ColorBlend8','AlphaBlend16','AlphaBlend8','ColorCompare16','ColorCompare8',
      'NeighborExtract16','NeighborExtract8','DispatchDirection16','DispatchDirection8','Classifier8Tail',
      'Classifier8','Classifier16Exact','EdgeWalker16Exact','SubHandler16Exact','EdgeWalker8Exact','SubHandler8Exact',
      'MainInterpKernel16','MainInterpKernel8','InterpExecutor16','InterpExecutor8',
      'ScanlinePixel16_Main','ScanlinePixel8_Main','ScanlinePixel8_KeyMask','ScanlinePixel16_KeyMask','AltHandler16','AltHandler8']
    functions={n['name']:n for n in ast['inner'] if n.get('kind')=='FunctionDecl' and any(c.get('kind')=='CompoundStmt' for c in n.get('inner',[]))}
    out=['// @generated by tools/translate.py from the existing C++ port; do not hand edit.\nuse super::support::*;\n']
    for name in names:
        print(name,flush=True)
        out.append(Translator(functions[name]).code())
    content='\n'.join(out)
    for old,new in [('Classifier16','Classifier16Exact'),('EdgeWalker16','EdgeWalker16Exact'),('EdgeWalker8','EdgeWalker8Exact'),('SubHandler16','SubHandler16Exact'),('SubHandler8','SubHandler8Exact')]:
        content=re.sub(r'\b'+old+r'\(',new+'(',content)
    (CRATE/'src').mkdir(exist_ok=True)
    (CRATE/'src/generated.rs').write_text(content,encoding='utf-8')

if __name__ == '__main__':
    if '--reuse-ast' not in sys.argv:prepare()
    generate()
