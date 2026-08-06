#!/usr/bin/env python3
"""Execute the 187-instruction InterpExecutor8 CFG on a pinned in-bounds call."""
import ctypes
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader
from test_olmsmoother_v1_mainkernel8_cfg_interpreter_20260805 import (
    ALIASES, Machine, STACK, f32, split_ops,
)
from test_olmsmoother_v1_mainkernel8_case0001_all_boundaries_20260805 import (
    load_production_harness,
)

AEX = ROOT / "plugins_2025/OLMSmoother.aex"
SHA = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
CFG = ROOT / "refs/conformance/olmsmoother_v1_executor8_cfg_20260805.json"
BOUNDARY = ROOT / "refs/conformance/olmsmoother_v1_case0001_pf8_mainkernel_boundary_20260805.json"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMSmoother/case_0001_before_effects.png"
ENTRY = 0x180006270
ALPHA_BLEND = 0x180002060
KIND_TO_FUNCTION = (0x1800010C0, 0x1800010E0, 0x180001110, 0x180001150, 0x180001180)
FUNCTION_TO_KIND = {address: kind for kind, address in enumerate(KIND_TO_FUNCTION)}


class ExecutorMachine(Machine):
    def write_bytes(self, address, data):
        if STACK <= address and address + len(data) <= STACK + 0x1000:
            super().write_bytes(address, data)
        else:
            self.loader.write_bytes(address, bytes(data))

    def evaluate_virtual(self, operand, pc, size):
        assert operand == "qword ptr [rax]"
        vtable = self.reg("rax")
        target = self.read_int(vtable, 8)
        assert target in FUNCTION_TO_KIND
        result = self.loader.call_function(
            target, [self.reg("rcx"), 0],
            float_args={1: bytes(self.xmm["xmm1"])}, max_instructions=1000)
        self.xmm["xmm0"][:] = result["xmm0"]

    def alpha_blend(self):
        source_a, source_b = self.reg("rcx"), self.reg("r8")
        destination = self.read_int(self.reg("rsp") + 0x20, 8)
        host_a = self.loader.host_alloc(4, align=4)
        host_b = self.loader.host_alloc(4, align=4)
        host_out = self.loader.host_alloc(4, align=4)
        self.loader.write_bytes(host_a, self.read_bytes(source_a, 4))
        self.loader.write_bytes(host_b, self.read_bytes(source_b, 4))
        self.loader.write_bytes(host_out, b"\0" * 4)
        self.loader.call_function(
            ALPHA_BLEND, [host_a, 0, host_b, 0, host_out],
            float_args={1: bytes(self.xmm["xmm1"]), 3: bytes(self.xmm["xmm3"])},
            max_instructions=10000)
        self.write_bytes(destination, self.loader.read_bytes(host_out, 4))

    def run_executor(self):
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
                self.set_reg(ops[0], self.address(ops[1], pc, size)); pc = nxt
            elif mnemonic in ("add", "sub", "cmp"):
                left, width, _ = self.operand(ops[0], pc, size)
                right, _, _ = self.operand(ops[1], pc, size, width)
                result = self.add_flags(left, right, width) if mnemonic == "add" else self.sub_flags(left, right, width)
                if mnemonic != "cmp": self.put(ops[0], result, pc, size, width)
                pc = nxt
            elif mnemonic in ("xor", "test"):
                left, width, _ = self.operand(ops[0], pc, size)
                right, _, _ = self.operand(ops[1], pc, size, width)
                result = left ^ right if mnemonic == "xor" else left & right
                self.logic_flags(result, width)
                if mnemonic == "xor": self.put(ops[0], result, pc, size, width)
                pc = nxt
            elif mnemonic == "inc":
                value, width, _ = self.operand(ops[0], pc, size)
                old_cf = self.cf
                self.put(ops[0], self.add_flags(value, 1, width), pc, size, width)
                self.cf = old_cf; pc = nxt
            elif mnemonic == "cdq":
                self.set_reg("edx", 0xFFFFFFFF if self.reg("eax") & 0x80000000 else 0); pc = nxt
            elif mnemonic == "imul":
                left, width, _ = self.operand(ops[0], pc, size)
                right, _, _ = self.operand(ops[1], pc, size, width)
                bits = width * 8
                left = left - (1 << bits) if left & (1 << (bits - 1)) else left
                right = right - (1 << bits) if right & (1 << (bits - 1)) else right
                self.put(ops[0], left * right, pc, size, width); pc = nxt
            elif mnemonic == "push":
                self.regs["rsp"] -= 8
                self.write_int(self.regs["rsp"], self.reg(ops[0]), 8); pc = nxt
            elif mnemonic == "pop":
                self.set_reg(ops[0], self.read_int(self.regs["rsp"], 8))
                self.regs["rsp"] += 8; pc = nxt
            elif mnemonic.startswith("cmov"):
                suffix = mnemonic[4:]
                take = {"g": not self.zf and self.sf == self.of}[suffix]
                if take:
                    value, width, _ = self.operand(ops[1], pc, size)
                    self.put(ops[0], value, pc, size, width)
                pc = nxt
            elif mnemonic == "movaps":
                value, _, _ = self.operand(ops[1], pc, size, 16)
                self.put(ops[0], value, pc, size, 16); pc = nxt
            elif mnemonic == "movss":
                value, _, _ = self.operand(ops[1], pc, size, 4)
                if ops[0].startswith("xmm"):
                    self.xmm[ops[0]][:4] = int(value & 0xFFFFFFFF).to_bytes(4, "little")
                else: self.put(ops[0], value & 0xFFFFFFFF, pc, size, 4)
                pc = nxt
            elif mnemonic == "movd":
                value, _, _ = self.operand(ops[1], pc, size, 4)
                if ops[0].startswith("xmm"):
                    self.xmm[ops[0]][:] = int(value & 0xFFFFFFFF).to_bytes(4, "little") + b"\0" * 12
                else: self.put(ops[0], value & 0xFFFFFFFF, pc, size, 4)
                pc = nxt
            elif mnemonic == "cvtdq2ps":
                source = self.xmm[ops[1]]
                self.xmm[ops[0]][:] = b"".join(
                    struct.pack("<f", f32(struct.unpack_from("<i", source, lane * 4)[0]))
                    for lane in range(4))
                pc = nxt
            elif mnemonic in ("subss", "divss", "minss", "maxss"):
                left = self.xmm_f32(ops[0])
                if ops[1].startswith("xmm"): right = self.xmm_f32(ops[1])
                else:
                    raw, _, _ = self.operand(ops[1], pc, size, 4)
                    right = struct.unpack("<f", int(raw).to_bytes(4, "little"))[0]
                if mnemonic == "subss": result = f32(left - right)
                elif mnemonic == "divss": result = f32(left / right)
                elif mnemonic == "minss": result = right if math.isnan(left) or math.isnan(right) else min(left, right)
                else: result = right if math.isnan(left) or math.isnan(right) else max(left, right)
                self.set_xmm_f32(ops[0], result); pc = nxt
            elif mnemonic == "xorps":
                left = int.from_bytes(self.xmm[ops[0]], "little")
                right, _, _ = self.operand(ops[1], pc, size, 16)
                self.xmm[ops[0]][:] = (left ^ right).to_bytes(16, "little"); pc = nxt
            elif mnemonic == "comiss":
                left, right = self.xmm_f32(ops[0]), self.xmm_f32(ops[1])
                if math.isnan(left) or math.isnan(right): self.zf = self.cf = 1
                else: self.zf, self.cf = int(left == right), int(left < right)
                self.sf = self.of = 0; pc = nxt
            elif mnemonic == "call":
                if ops[0].startswith("qword ptr"):
                    self.evaluate_virtual(ops[0], pc, size)
                else:
                    assert int(ops[0], 0) == ALPHA_BLEND
                    self.alpha_blend()
                pc = nxt
            elif mnemonic == "jmp": pc = int(ops[0], 0)
            elif mnemonic in ("je", "jne", "jg", "jge", "jle", "js", "jb", "jae"):
                pc = int(ops[0], 0) if self.condition(mnemonic) else nxt
            elif mnemonic == "ret": return step + 1
            else: raise AssertionError((hex(pc), mnemonic, ops))
        raise AssertionError("InterpExecutor8 did not return")


def dual_world(loader, pixels, width, height, rowbytes):
    world = loader.host_alloc(0x50, align=16)
    loader.write_bytes(world, b"\0" * 0x50)
    # Compact helper layout used by the surrounding recovered stages.
    loader.write_bytes(world + 4, struct.pack("<iii", width, height, rowbytes))
    loader.write_bytes(world + 0x10, struct.pack("<Q", pixels))
    # Native PF_EffectWorld offsets consumed by FUN_180006270 itself.
    loader.write_bytes(world + 0x18, struct.pack("<Qiii", pixels, rowbytes, width, height))
    return world


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == SHA
    cfg = json.loads(CFG.read_text())
    assert cfg["instruction_count"] == 187 and cfg["block_count"] == 33
    instructions = {int(ins["address"], 0): ins
                    for block in cfg["blocks"] for ins in block["instructions"]}
    boundary = json.loads(BOUNDARY.read_text())
    image = Image.open(SOURCE).convert("RGBA")
    width, height = image.size
    argb = bytearray()
    for red, green, blue, alpha in image.getdata(): argb += bytes((alpha, red, green, blue))
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    source = loader.host_alloc(len(argb), align=16)
    destination = loader.host_alloc(len(argb), align=16)
    loader.write_bytes(source, bytes(argb))
    loader.write_bytes(destination, bytes(argb))
    src_world = dual_world(loader, source, width, height, width * 4)
    dst_world = dual_world(loader, destination, width, height, width * 4)
    state = loader.host_alloc(0x80, align=16)
    loader.write_bytes(state, b"\0" * 0x80)
    loader.write_bytes(state + 0x10, struct.pack("<QQ", src_world, dst_world))

    call = boundary["executor_captures"][0]
    raw_evaluator = bytes.fromhex(call["evaluator_bytes"])
    evaluator = loader.host_alloc(0x20, align=16)
    loader.write_bytes(evaluator, raw_evaluator)
    center_x, center_y = boundary["center"]
    pointers = [source + ((center_y + dy) * width + center_x + dx) * 4
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    args = [state, call["direction"], *call["start"], pointers[call["color_a_index"]],
            *call["end"], pointers[call["color_b_index"]], evaluator,
            call["use_source"], call["leading_span"]]

    loader.call_function(ENTRY, args, max_instructions=100000)
    actual = loader.read_bytes(destination, len(argb))
    loader.write_bytes(destination, bytes(argb))
    machine = ExecutorMachine(loader, instructions, args, pointers)
    interpreted_steps = machine.run_executor()
    interpreted = loader.read_bytes(destination, len(argb))

    temporary, library, production_function = load_production_harness()
    executor_function = library.olmsmoother_run_executor8_production
    executor_function.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                                  ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
                                  ctypes.POINTER(ctypes.c_int32), ctypes.c_int32,
                                  ctypes.POINTER(ctypes.c_uint32)]
    source_array = (ctypes.c_uint8 * len(argb)).from_buffer_copy(argb)
    destination_array = (ctypes.c_uint8 * len(argb)).from_buffer_copy(argb)
    args11 = (ctypes.c_int32 * 11)(
        call["direction"], *call["start"], center_x, center_y,
        *call["end"], center_x + 1, center_y,
        call["use_source"], call["leading_span"])
    evaluator_function = int(call["evaluator_function"], 0)
    kind = FUNCTION_TO_KIND[evaluator_function]
    fields = (ctypes.c_uint32 * 4)(*struct.unpack("<4I", raw_evaluator[8:24]))
    executor_function(source_array, destination_array, width, height, width * 4,
                      args11, kind, fields)
    production = bytes(destination_array)

    changed_actual = sum(a != b for a, b in zip(argb, actual))
    report = {
        "status": "exact" if actual == interpreted == production else "fail",
        "actual_aex_sha256": SHA,
        "cfg_instructions": len(instructions),
        "interpreted_instructions": interpreted_steps,
        "call": call,
        "actual_changed_bytes": changed_actual,
        "actual_output_sha256": hashlib.sha256(actual).hexdigest(),
        "interpreted_output_sha256": hashlib.sha256(interpreted).hexdigest(),
        "production_output_sha256": hashlib.sha256(production).hexdigest(),
        "actual_vs_interpreted_mismatch": sum(a != b for a, b in zip(actual, interpreted)),
        "actual_vs_production_mismatch": sum(a != b for a, b in zip(actual, production)),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    assert actual == interpreted == production
    del production_function, library
    temporary.cleanup()


if __name__ == "__main__":
    main()
