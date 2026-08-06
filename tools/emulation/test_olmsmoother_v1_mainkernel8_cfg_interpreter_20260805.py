#!/usr/bin/env python3
"""Interpret the actual FUN_180005570 CFG and pin its first residual boundary.

The interpreter executes the checked-in Capstone CFG, not Unicorn instructions.
The actual ColorCompare8 leaf is used as a bound primitive, the five tiny curve
constructors are modeled from their pinned object layouts, and calls to
InterpExecutor8 are captured at the Windows x64 ABI boundary.  This keeps the
test focused on MainInterpKernel8's control flow and float32 construction order.
"""
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader

AEX = ROOT / "plugins_2025/OLMSmoother.aex"
SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
CFG = ROOT / "refs/conformance/olmsmoother_v1_mainkernel8_cfg_20260805.json"
BOUNDARY = ROOT / "refs/conformance/olmsmoother_v1_case0001_pf8_mainkernel_boundary_20260805.json"
ENTRY = 0x180005570
EXECUTOR = 0x180006270
STACK = 0x700000000000

BASES = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
         "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15")
ALIASES = {}
for base in BASES:
    if base[1:].isdigit():
        ALIASES.update({base: (base, 64), base + "d": (base, 32),
                        base + "w": (base, 16), base + "b": (base, 8)})
for base, stem in (("rax", "a"), ("rbx", "b"), ("rcx", "c"), ("rdx", "d")):
    ALIASES.update({base: (base, 64), "e" + stem + "x": (base, 32),
                    stem + "x": (base, 16), stem + "l": (base, 8)})
ALIASES.update({
    "rsi": ("rsi", 64), "esi": ("rsi", 32), "si": ("rsi", 16), "sil": ("rsi", 8),
    "rdi": ("rdi", 64), "edi": ("rdi", 32), "di": ("rdi", 16), "dil": ("rdi", 8),
    "rbp": ("rbp", 64), "ebp": ("rbp", 32), "bp": ("rbp", 16), "bpl": ("rbp", 8),
    "rsp": ("rsp", 64), "esp": ("rsp", 32), "sp": ("rsp", 16), "spl": ("rsp", 8),
})

CONSTRUCTORS = {
    0x180001000: 0x18000D1A8,  # LinearOffsetFunction -> evaluator 0x1800010c0
    0x180001020: 0x18000D1D8,  # LinearOffsetOneValue -> evaluator 0x1800010e0
    0x180001040: 0x18000D1E8,  # LinearOffsetZeroOneValue -> evaluator 0x180001110
    0x180001070: 0x18000D1C8,  # LinearOffsetZeroValue -> evaluator 0x180001150
    0x180001090: 0x18000D1B8,  # LinearThreeOffsetFunction -> evaluator 0x180001180
}


def split_ops(text):
    depth = 0
    for index, char in enumerate(text):
        depth += char == "["
        depth -= char == "]"
        if char == "," and depth == 0:
            return text[:index].strip(), text[index + 1:].strip()
    return (text.strip(),) if text.strip() else ()


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def s32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


class Machine:
    def __init__(self, loader, instructions, args, pixel_ptrs):
        self.loader = loader
        self.instructions = instructions
        self.regs = {name: 0 for name in BASES}
        self.xmm = {f"xmm{i}": bytearray(16) for i in range(16)}
        self.memory = {}
        self.zf = self.sf = self.of = self.cf = 0
        self.trace = []
        self.captures = []
        self.pixel_ptrs = pixel_ptrs
        self.regs["rsp"] = STACK + 0x800
        self.regs.update(zip(("rcx", "rdx", "r8", "r9"), args[:4]))
        self.write_int(self.regs["rsp"], 0xDEADBEEFDEADBEEF, 8)
        for index, value in enumerate(args[4:]):
            self.write_int(self.regs["rsp"] + 0x28 + index * 8, value, 8)

    def reg(self, name):
        base, width = ALIASES[name]
        return self.regs[base] & ((1 << width) - 1)

    def set_reg(self, name, value):
        base, width = ALIASES[name]
        mask = (1 << width) - 1
        if width >= 32:
            self.regs[base] = value & mask
        else:
            self.regs[base] = (self.regs[base] & ~mask) | (value & mask)

    def address(self, expression, pc, size):
        text = expression[1:-1].replace(" ", "")
        total = pc + size if text.startswith("rip") else 0
        if text.startswith("rip"):
            text = text[3:]
        for sign, term in re.findall(r"(^|[+-])([^+-]+)", text):
            if "*" in term:
                item, scale = term.split("*")
                value = self.reg(item) * int(scale, 0)
            else:
                value = self.reg(term) if term in ALIASES else int(term, 0)
            total = total - value if sign == "-" else total + value
        return total & 0xFFFFFFFFFFFFFFFF

    def read_bytes(self, address, size):
        result = bytearray()
        for offset in range(size):
            here = address + offset
            if here in self.memory:
                result.append(self.memory[here])
            elif STACK <= here < STACK + 0x1000:
                result.append(0)
            else:
                result.extend(self.loader.read_bytes(here, 1))
        return bytes(result)

    def write_bytes(self, address, data):
        for offset, value in enumerate(data):
            self.memory[address + offset] = value

    def read_int(self, address, size):
        return int.from_bytes(self.read_bytes(address, size), "little")

    def write_int(self, address, value, size):
        self.write_bytes(address, int(value & ((1 << (size * 8)) - 1)).to_bytes(size, "little"))

    def operand(self, operand, pc, size, forced=None):
        match = re.match(r"(?:(byte|word|dword|qword|xmmword) ptr )?(\[.*\])$", operand)
        if match:
            width = {"byte": 1, "word": 2, "dword": 4, "qword": 8, "xmmword": 16}.get(match.group(1), forced)
            assert width is not None, (hex(pc), operand)
            address = self.address(match.group(2), pc, size)
            return self.read_int(address, width), width, address
        if operand in ALIASES:
            return self.reg(operand), ALIASES[operand][1] // 8, None
        if operand.startswith("xmm"):
            return int.from_bytes(self.xmm[operand], "little"), 16, None
        return int(operand, 0), forced, None

    def put(self, operand, value, pc, size, forced=None):
        _, width, address = self.operand(operand, pc, size, forced)
        if address is not None:
            self.write_int(address, value, width)
        elif operand.startswith("xmm"):
            self.xmm[operand][:] = int(value & ((1 << 128) - 1)).to_bytes(16, "little")
        else:
            self.set_reg(operand, value)

    def logic_flags(self, value, width):
        self.zf = int(value == 0)
        self.sf = (value >> (width * 8 - 1)) & 1
        self.of = self.cf = 0

    def sub_flags(self, left, right, width):
        bits = width * 8
        mask = (1 << bits) - 1
        result = (left - right) & mask
        self.zf = int(result == 0)
        self.sf = (result >> (bits - 1)) & 1
        self.of = (((left ^ right) & (left ^ result)) >> (bits - 1)) & 1
        self.cf = int((left & mask) < (right & mask))
        return result

    def add_flags(self, left, right, width):
        bits = width * 8
        mask = (1 << bits) - 1
        result = (left + right) & mask
        self.zf = int(result == 0)
        self.sf = (result >> (bits - 1)) & 1
        self.of = ((~(left ^ right) & (left ^ result)) >> (bits - 1)) & 1
        self.cf = int(left + right > mask)
        return result

    def xmm_f32(self, name):
        return struct.unpack("<f", self.xmm[name][:4])[0]

    def set_xmm_f32(self, name, value):
        self.xmm[name][:4] = struct.pack("<f", f32(value))

    def construct_curve(self, target):
        obj = self.reg("rcx")
        values = [self.xmm_f32("xmm1"), self.xmm_f32("xmm2"), self.xmm_f32("xmm3")]
        if target in (0x180001040, 0x180001090):
            values.append(struct.unpack("<f", self.read_bytes(self.reg("rsp") + 0x20, 4))[0])
        count = {0x180001000: 2, 0x180001020: 3, 0x180001040: 4,
                 0x180001070: 3, 0x180001090: 4}[target]
        self.write_int(obj, CONSTRUCTORS[target], 8)
        if target == 0x180001040:
            # The fourth LinearOffsetZeroOneValue member is deliberately at
            # +0x18 (the actual evaluator also reads +0x18), leaving +0x14
            # untouched.  It is the sole non-contiguous curve layout.
            self.write_bytes(obj + 8, b"".join(struct.pack("<f", value) for value in values[:3]))
            self.write_bytes(obj + 0x18, struct.pack("<f", values[3]))
        else:
            self.write_bytes(obj + 8, b"".join(struct.pack("<f", value) for value in values[:count]))
        self.set_reg("rax", obj)

    def capture_executor(self):
        rsp = self.reg("rsp")
        evaluator = self.read_int(rsp + 0x40, 8)
        vtable = self.read_int(evaluator, 8)
        color_a = self.read_int(rsp + 0x20, 8)
        color_b = self.read_int(rsp + 0x38, 8)
        self.captures.append({
            "direction": s32(self.reg("edx")),
            "start": [s32(self.reg("r8d")), s32(self.reg("r9d"))],
            "color_a_index": self.pixel_ptrs.index(color_a) if color_a in self.pixel_ptrs else None,
            "end": [s32(self.read_int(rsp + 0x28, 4)), s32(self.read_int(rsp + 0x30, 4))],
            "color_b_index": self.pixel_ptrs.index(color_b) if color_b in self.pixel_ptrs else None,
            "evaluator_bytes": self.read_bytes(evaluator, 0x20).hex(),
            "evaluator_vtable": hex(vtable),
            "evaluator_function": hex(self.read_int(vtable, 8)),
            "use_source": self.read_int(rsp + 0x48, 1),
            "leading_span": s32(self.read_int(rsp + 0x50, 4)),
        })

    def direct_call(self, target):
        if target == 0x180002430:
            result = self.loader.call_function(target, [self.reg("rcx"), self.reg("rdx")], max_instructions=1000)
            self.set_reg("eax", result["rax"])
        elif target in CONSTRUCTORS:
            self.construct_curve(target)
        elif target == EXECUTOR:
            self.capture_executor()
        elif target == 0x180001A90:
            # This leaf is outside the representative path.  Retain its exact
            # implementation for subsequent all-boundary sweeps.
            self.loader.call_function(target, [self.reg("rcx"), self.reg("rdx"), self.reg("r8")], max_instructions=100000)
        elif target == 0x18000B720:
            # __security_check_cookie has no semantic output on a valid frame.
            pass
        else:
            raise AssertionError(("unsupported call", hex(target)))

    def condition(self, mnemonic):
        return {
            "je": self.zf,
            "jne": not self.zf,
            "jg": not self.zf and self.sf == self.of,
            "jge": self.sf == self.of,
            "jle": self.zf or self.sf != self.of,
            "js": self.sf,
            "jns": not self.sf,
            "jb": self.cf,
            "jae": not self.cf,
        }[mnemonic]

    def run(self):
        pc = ENTRY
        for step in range(10000):
            ins = self.instructions[pc]
            mnemonic = ins["mnemonic"]
            ops = split_ops(ins["operands"])
            size = len(bytes.fromhex(ins["bytes"]))
            nxt = pc + size
            self.trace.append(pc)

            if mnemonic in ("mov", "movzx", "movsxd"):
                value, width, _ = self.operand(ops[1], pc, size)
                if mnemonic == "movsxd" and value & (1 << (width * 8 - 1)):
                    value -= 1 << (width * 8)
                self.put(ops[0], value, pc, size)
                pc = nxt
            elif mnemonic == "lea":
                self.set_reg(ops[0], self.address(ops[1], pc, size))
                pc = nxt
            elif mnemonic in ("add", "sub", "cmp"):
                left, width, _ = self.operand(ops[0], pc, size)
                right, _, _ = self.operand(ops[1], pc, size, width)
                result = self.add_flags(left, right, width) if mnemonic == "add" else self.sub_flags(left, right, width)
                if mnemonic != "cmp":
                    self.put(ops[0], result, pc, size, width)
                pc = nxt
            elif mnemonic in ("xor", "and", "or", "test"):
                left, width, _ = self.operand(ops[0], pc, size)
                right, _, _ = self.operand(ops[1], pc, size, width)
                result = {"xor": left ^ right, "and": left & right,
                          "or": left | right, "test": left & right}[mnemonic]
                self.logic_flags(result, width)
                if mnemonic != "test":
                    self.put(ops[0], result, pc, size, width)
                pc = nxt
            elif mnemonic in ("inc", "dec"):
                value, width, _ = self.operand(ops[0], pc, size)
                old_cf = self.cf
                result = self.add_flags(value, 1, width) if mnemonic == "inc" else self.sub_flags(value, 1, width)
                self.cf = old_cf
                self.put(ops[0], result, pc, size, width)
                pc = nxt
            elif mnemonic == "neg":
                value, width, _ = self.operand(ops[0], pc, size)
                self.put(ops[0], self.sub_flags(0, value, width), pc, size, width)
                pc = nxt
            elif mnemonic == "sar":
                value, width, _ = self.operand(ops[0], pc, size)
                count, _, _ = self.operand(ops[1], pc, size, width)
                bits = width * 8
                signed = value - (1 << bits) if value & (1 << (bits - 1)) else value
                self.put(ops[0], signed >> count, pc, size, width)
                pc = nxt
            elif mnemonic == "imul":
                left, width, _ = self.operand(ops[0], pc, size)
                right, _, _ = self.operand(ops[1], pc, size, width)
                bits = width * 8
                left = left - (1 << bits) if left & (1 << (bits - 1)) else left
                right = right - (1 << bits) if right & (1 << (bits - 1)) else right
                self.put(ops[0], left * right, pc, size, width)
                pc = nxt
            elif mnemonic == "cdq":
                self.set_reg("edx", 0xFFFFFFFF if self.reg("eax") & 0x80000000 else 0)
                pc = nxt
            elif mnemonic == "idiv":
                divisor, width, _ = self.operand(ops[0], pc, size)
                assert width == 4
                divisor = s32(divisor)
                dividend = (self.reg("edx") << 32) | self.reg("eax")
                if dividend & (1 << 63):
                    dividend -= 1 << 64
                quotient = math.trunc(dividend / divisor)
                remainder = dividend - quotient * divisor
                self.set_reg("eax", quotient)
                self.set_reg("edx", remainder)
                pc = nxt
            elif mnemonic.startswith("cmov"):
                suffix = mnemonic[4:]
                take = {"e": self.zf, "ne": not self.zf,
                        "g": not self.zf and self.sf == self.of,
                        "le": self.zf or self.sf != self.of,
                        "s": self.sf}[suffix]
                if take:
                    value, width, _ = self.operand(ops[1], pc, size)
                    self.put(ops[0], value, pc, size, width)
                pc = nxt
            elif mnemonic == "push":
                self.regs["rsp"] -= 8
                self.write_int(self.regs["rsp"], self.reg(ops[0]), 8)
                pc = nxt
            elif mnemonic == "pop":
                value = self.read_int(self.regs["rsp"], 8)
                self.regs["rsp"] += 8
                self.set_reg(ops[0], value)
                pc = nxt
            elif mnemonic == "movaps":
                value, _, _ = self.operand(ops[1], pc, size, 16)
                self.put(ops[0], value, pc, size, 16)
                pc = nxt
            elif mnemonic == "movss":
                value, _, _ = self.operand(ops[1], pc, size, 4)
                if ops[0].startswith("xmm"):
                    self.xmm[ops[0]][:4] = int(value & 0xFFFFFFFF).to_bytes(4, "little")
                else:
                    self.put(ops[0], value & 0xFFFFFFFF, pc, size, 4)
                pc = nxt
            elif mnemonic == "movd":
                value, _, _ = self.operand(ops[1], pc, size, 4)
                if ops[0].startswith("xmm"):
                    self.xmm[ops[0]][:] = int(value & 0xFFFFFFFF).to_bytes(4, "little") + b"\0" * 12
                else:
                    self.put(ops[0], value & 0xFFFFFFFF, pc, size, 4)
                pc = nxt
            elif mnemonic == "cvtdq2ps":
                source = self.xmm[ops[1]]
                self.xmm[ops[0]][:] = b"".join(struct.pack("<f", f32(struct.unpack_from("<i", source, lane * 4)[0])) for lane in range(4))
                pc = nxt
            elif mnemonic in ("addss", "subss", "mulss", "divss", "minss", "maxss"):
                left = self.xmm_f32(ops[0])
                if ops[1].startswith("xmm"):
                    right = self.xmm_f32(ops[1])
                else:
                    raw, _, _ = self.operand(ops[1], pc, size, 4)
                    right = struct.unpack("<f", int(raw).to_bytes(4, "little"))[0]
                if mnemonic == "addss": result = f32(left + right)
                elif mnemonic == "subss": result = f32(left - right)
                elif mnemonic == "mulss": result = f32(left * right)
                elif mnemonic == "divss": result = f32(left / right)
                elif mnemonic == "minss": result = right if math.isnan(left) or math.isnan(right) else min(left, right)
                else: result = right if math.isnan(left) or math.isnan(right) else max(left, right)
                self.set_xmm_f32(ops[0], result)
                pc = nxt
            elif mnemonic == "xorps":
                left = int.from_bytes(self.xmm[ops[0]], "little")
                value, _, _ = self.operand(ops[1], pc, size, 16)
                self.xmm[ops[0]][:] = (left ^ value).to_bytes(16, "little")
                pc = nxt
            elif mnemonic == "call":
                self.direct_call(int(ops[0], 0))
                pc = nxt
            elif mnemonic == "jmp":
                pc = int(ops[0], 0)
            elif mnemonic in ("je", "jne", "jg", "jge", "jle", "js", "jns", "jb", "jae"):
                pc = int(ops[0], 0) if self.condition(mnemonic) else nxt
            elif mnemonic == "ret":
                return step + 1
            else:
                raise AssertionError((hex(pc), mnemonic, ops))
        raise AssertionError("MainInterpKernel8 did not return")


def make_fixture(loader, boundary):
    state = loader.host_alloc(0x80, align=16)
    loader.write_bytes(state, b"\0" * 0x80)
    loader.write_bytes(state + 8, struct.pack("<i", 6))
    pointers = []
    for argb in boundary["neighborhood_argb"]:
        pointer = loader.host_alloc(4, align=4)
        loader.write_bytes(pointer, bytes(argb))
        pointers.append(pointer)
    neighborhood = loader.host_alloc(72, align=16)
    loader.write_bytes(neighborhood, struct.pack("<9Q", *pointers))
    return state, neighborhood, pointers


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == SHA
    cfg = json.loads(CFG.read_text())
    boundary = json.loads(BOUNDARY.read_text())
    assert cfg["instruction_count"] == 586 and cfg["block_count"] == 47
    instructions = {int(ins["address"], 0): ins for block in cfg["blocks"] for ins in block["instructions"]}
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    state, neighborhood, pointers = make_fixture(loader, boundary)
    args = [state, neighborhood, *boundary["main_args"]]
    machine = Machine(loader, instructions, args, pointers)
    steps = machine.run()
    expected = boundary["executor_captures"]
    report = {
        "status": "exact" if machine.captures == expected else "fail",
        "cfg_instructions": len(instructions),
        "executed_instructions": steps,
        "executor_calls": len(machine.captures),
        "captures": machine.captures,
        "expected": expected,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    assert machine.captures == expected


if __name__ == "__main__":
    main()
