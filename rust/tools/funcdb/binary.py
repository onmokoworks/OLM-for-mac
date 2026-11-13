"""PE decoding with hub-owned discovery. No JVM, binary execution or code-byte output."""
from collections import deque
import hashlib
from pathlib import Path
import re
from types import SimpleNamespace

import capstone as cs
from capstone import x86_const as x
import pefile

NORMALIZER = 'funcdb-x64-v1'


def digest(value):
    return hashlib.sha256(value).hexdigest()


class Image:
    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self.sha256 = digest(self.data)
        self.pe = pefile.PE(data=self.data)
        if self.pe.FILE_HEADER.Machine != 0x8664:
            raise ValueError('Only AMD64 PE images are supported')
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = [(self.base+s.VirtualAddress, s.get_data(), s.Characteristics)
                         for s in self.pe.sections]
        self.imports = {}
        for attr in ('DIRECTORY_ENTRY_IMPORT', 'DIRECTORY_ENTRY_DELAY_IMPORT'):
            for dll in getattr(self.pe, attr, []):
                for imp in dll.imports:
                    self.imports[imp.address] = dll.dll.decode(errors='replace').lower()+'!'+(
                        imp.name.decode(errors='replace') if imp.name else '#'+str(imp.ordinal))
        self.relocations = {}
        for block in getattr(self.pe, 'DIRECTORY_ENTRY_BASERELOC', []):
            for entry in block.entries:
                if entry.type:
                    if entry.type not in (3, 10):
                        raise ValueError(f'Unsupported relocation type {entry.type}')
                    self.relocations[self.base+entry.rva] = 8 if entry.type == 10 else 4
        self.decoder = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_64)
        self.decoder.detail = True

    def section(self, address):
        return next((s for s in self.sections if s[0] <= address < s[0]+len(s[1])), None)

    def read(self, address, size):
        s = self.section(address)
        return s[1][address-s[0]:address-s[0]+size] if s else b''

    def instruction(self, address):
        return next(self.decoder.disasm(self.read(address, 15), address, count=1), None)

    def recover(self, entry, size, entries):
        """Walk direct CFG edges, stopping at other hub entries; require exact body size.

        Indirect jump tables/non-contiguous bodies that cannot be recovered fall back
        to the hub's listing export, never a guessed contiguous entry+size slice.
        """
        pending, found, total = deque([entry]), {}, 0
        while pending:
            address = pending.popleft()
            while address not in found and (address == entry or address not in entries):
                section = self.section(address)
                if not section or not section[2] & 0x20000000:
                    break
                ins = self.instruction(address)
                if ins is None:
                    return None
                found[address] = ins
                total += ins.size
                if total > size:
                    return None
                jump = ins.group(cs.CS_GRP_JUMP)
                if jump and ins.operands and ins.operands[0].type == x.X86_OP_IMM:
                    pending.append(ins.operands[0].imm)
                if ins.group(cs.CS_GRP_RET) or ins.group(cs.CS_GRP_IRET) or ins.id in (
                        x.X86_INS_JMP, x.X86_INS_INT3, x.X86_INS_UD2, x.X86_INS_HLT):
                    break
                address += ins.size
        if total != size:
            return None
        return [found[a] for a in sorted(found)]

    def exported(self, directory, size):
        lines = [line.split(None,1) for line in
                 (Path(directory)/'disassembly.txt').read_text().splitlines() if line.strip()]
        result = [self.instruction(int(a,16)) or SimpleNamespace(address=int(a,16),size=0,text=text)
                  for a,text in lines]
        return result

    def fingerprint(self, instructions):
        indices = {i.address: n for n, i in enumerate(instructions)}
        strict, loose, literals, imports = [], [], [], set()
        for ins in instructions:
            if hasattr(ins, 'text'):
                # Unsupported Capstone opcode: hash Ghidra's textual listing with
                # address operands abstracted. Keep the decoder domain explicit.
                def replace(m):
                    value = int(m[0],16)
                    return 'TARGET' if self.section(value) else m[0].lower()
                normalized = re.sub(r'0x[0-9a-fA-F]+', replace, ins.text)
                strict.append('ghidra:'+normalized)
                loose.append('ghidra:'+re.sub(r'0x[0-9a-fA-F]+','IMM',normalized))
                continue
            operands, shapes = [], []
            control = ins.group(cs.CS_GRP_CALL) or ins.group(cs.CS_GRP_JUMP)
            relocated = any(r in self.relocations for r in range(ins.address, ins.address+ins.size))
            for op in ins.operands:
                if op.type == x.X86_OP_REG:
                    value = ['reg', ins.reg_name(op.reg), op.size]
                    shape = value
                elif op.type == x.X86_OP_IMM:
                    if control:
                        value = ['branch', indices[op.imm]] if op.imm in indices else ['target']
                        shape = ['target']
                    elif relocated:
                        value = shape = ['reloc', op.size]
                    else:
                        value, shape = ['imm', op.imm, op.size], ['imm', op.size]
                elif op.type == x.X86_OP_MEM:
                    mem = op.mem
                    target = ins.address+ins.size+mem.disp if mem.base == x.X86_REG_RIP else None
                    if target is not None or relocated:
                        value = shape = ['mem-address', op.size]
                        if target in self.imports:
                            imports.add(self.imports[target])
                        section = self.section(target) if target is not None else None
                        # Only fixed-width non-pointer loads from immutable non-code data.
                        # LEA, mutable globals, jump tables and pointers are address-only.
                        if (section and not section[2] & (0x80000000 | 0x20000000)
                                and ins.id != x.X86_INS_LEA and target not in self.imports
                                and not any(r in self.relocations for r in range(target, target+op.size))):
                            data = self.read(target, op.size)
                            if len(data) == op.size:
                                literals.append(digest(data))
                    else:
                        value = ['mem', ins.reg_name(mem.segment), ins.reg_name(mem.base),
                                 ins.reg_name(mem.index), mem.scale, mem.disp, op.size]
                        shape = value[:-2]+['disp', op.size]
                else:
                    raise ValueError(f'Unsupported operand type {op.type}')
                operands.append(value)
                shapes.append(shape)
            strict.append(repr([ins.mnemonic, operands]))
            loose.append(repr([ins.mnemonic, shapes]))
        # Bottom-k hashed shingles: stable, bounded, no disassembly or bytes stored.
        shingles = sorted({digest('\n'.join(loose[i:i+3]).encode())[:16]
                           for i in range(max(1, len(loose)-2))})[:48]
        return dict(exact=digest('\n'.join(strict).encode()),
                    literals=digest('\n'.join(literals).encode()),
                    fuzzy=shingles, instructions=len(instructions), imports=sorted(imports))


def similarity(a, b):
    """Bottom-k union sample Jaccard estimate, corrected for instruction count."""
    sa, sb = set(a['fuzzy']), set(b['fuzzy'])
    sample = sorted(sa | sb)[:48]
    if not sample:
        return 0.0
    jaccard = sum(v in sa and v in sb for v in sample)/len(sample)
    ratio = min(a['instructions'], b['instructions'])/max(a['instructions'], b['instructions'], 1)
    return round(jaccard*ratio, 6)
