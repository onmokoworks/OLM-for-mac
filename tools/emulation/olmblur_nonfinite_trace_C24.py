"""Raw nonfinite SSE observation; no instruction or result modification."""
from unicorn import UC_HOOK_CODE
import struct


def install_nonfinite_hooks(loader, stages, nonfinite_ops, ranges):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    from capstone.x86 import X86_OP_REG, X86_OP_MEM
    import unicorn.x86_const as regs
    decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
    for begin,end in ranges:
        for ins in decoder.disasm(loader.read_bytes(begin,end-begin),begin):
            if ins.mnemonic == 'ret':break
            if ins.mnemonic not in ('addss','mulss','divss'):continue
            dr=getattr(regs,'UC_X86_REG_'+ins.reg_name(ins.operands[0].reg).upper())
            source=ins.operands[1]
            if source.type==X86_OP_REG:
                sr=getattr(regs,'UC_X86_REG_'+ins.reg_name(source.reg).upper())
                def read_source(uc,sr=sr):return uc.reg_read(sr)&0xffffffff
            else:
                assert source.type==X86_OP_MEM
                mem=source.mem
                base=getattr(regs,'UC_X86_REG_'+ins.reg_name(mem.base).upper()) if mem.base else None
                index=getattr(regs,'UC_X86_REG_'+ins.reg_name(mem.index).upper()) if mem.index else None
                def read_source(uc,base=base,index=index,scale=mem.scale,disp=mem.disp):
                    address=(uc.reg_read(base) if base else 0)+(uc.reg_read(index)*scale if index else 0)+disp
                    return struct.unpack('<I',uc.mem_read(address,4))[0]
            state={}
            def before(uc,address,size,user,dr=dr,read_source=read_source,state=state,ins=ins):
                state.update(address=hex(address),operation=ins.mnemonic,operands=ins.op_str,
                    stage=len(stages)-1,left=uc.reg_read(dr)&0xffffffff,right=read_source(uc))
            def after(uc,address,size,user,dr=dr,state=state):
                if not state:return
                result=uc.reg_read(dr)&0xffffffff
                if any((v&0x7f800000)==0x7f800000 for v in (state['left'],state['right'],result)):
                    nonfinite_ops.append(dict(state,result=result))
                state.clear()
            loader.uc.hook_add(UC_HOOK_CODE,before,begin=ins.address,end=ins.address)
            loader.uc.hook_add(UC_HOOK_CODE,after,begin=ins.address+ins.size,end=ins.address+ins.size)
