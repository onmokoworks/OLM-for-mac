from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader
from unicorn.x86_const import (
    UC_X86_REG_RAX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RSP,
    UC_X86_REG_RIP,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "plugins_2025" / "OLMDirectionalBlur.aex"

FUN_1800038d0 = 0x1800038d0
FUN_180004a20 = 0x180004a20
FUN_180007bd0 = 0x180007bd0

def u32(loader, addr):
    return struct.unpack("<I", loader.read_bytes(addr, 4))[0]

def u64(loader, addr):
    return struct.unpack("<Q", loader.read_bytes(addr, 8))[0]

def f32_from_bits(bits):
    return struct.unpack("<f", struct.pack("<I", bits))[0]

def build_host_suites(loader):
    def h_new(ld, args):
        size = args[0] & 0xFFFFFFFF
        print(f"h_new allocating {size} bytes")
        data = ld.bump_alloc(max(size, 1), align=64)
        ld.write_bytes(data, b"\x00" * max(size, 1))
        handle = ld.host_alloc(8)
        ld.write_bytes(handle, struct.pack("<Q", data))
        return handle

    def h_lock(ld, args):
        return u64(ld, args[0]) if args[0] else 0

    def h_noop(ld, args):
        return 0

    handle_suite = loader.host_alloc(0x20)
    cbs = [
        loader.install_callback("PFHandle.new", h_new),
        loader.install_callback("PFHandle.lock", h_lock),
        loader.install_callback("PFHandle.unlock", h_noop),
        loader.install_callback("PFHandle.dispose", h_noop),
    ]
    loader.write_bytes(handle_suite, struct.pack("<4Q", *cbs))

    def sp_acquire(ld, args):
        out_ptr = args[2]
        ld.write_bytes(out_ptr, struct.pack("<Q", handle_suite))
        return 0

    spbasic = loader.host_alloc(0x10)
    spbasic_cbs = [
        loader.install_callback("SPBasic.AcquireSuite", sp_acquire),
        loader.install_callback("SPBasic.ReleaseSuite", h_noop),
    ]
    loader.write_bytes(spbasic, struct.pack("<2Q", *spbasic_cbs))
    return spbasic

def build_render_context(loader, spbasic):
    ctx = loader.host_alloc(0x200)
    loader.write_bytes(ctx, b"\x00" * 0x200)
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", spbasic))
    loader.write_bytes(ctx + 0x11C, struct.pack("<I", 1))
    loader.write_bytes(ctx + 0x120, struct.pack("<I", 1))
    loader.write_bytes(ctx + 0x124, struct.pack("<I", 1))
    loader.write_bytes(ctx + 0x128, struct.pack("<I", 1))

    def pf_checkout(ld, args):
        index = args[1]
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        param_def_ptr = struct.unpack("<Q", ld.read_bytes(rsp + 0x30, 8))[0]
        # zero out the PF_ParamDef (size is around 0xB0 bytes)
        ld.write_bytes(param_def_ptr, b"\x00" * 0xB0)
        return 0

    def pf_checkin(ld, args):
        return 0

    loader.write_bytes(
        ctx + 0,
        struct.pack("<Q", loader.install_callback("PF_ParamCheckout", pf_checkout))
    )
    loader.write_bytes(
        ctx + 8,
        struct.pack("<Q", loader.install_callback("PF_ParamCheckin", pf_checkin))
    )

    dispatch = loader.host_alloc(0x80)
    loader.write_bytes(dispatch, b"\x00" * 0x80)

    def suite_40(ld, args):
        return 0

    loader.write_bytes(
        dispatch + 0x40,
        struct.pack("<Q", loader.install_callback("RenderCtx.suite40", suite_40)),
    )
    loader.write_bytes(ctx + 0xB0, struct.pack("<Q", dispatch))
    loader.write_bytes(ctx + 0xB8, struct.pack("<Q", loader.host_alloc(8)))
    return ctx, dispatch

def build_world(loader, width, height):
    rgba_bytes = b"\x80" * (width * height * 4)  # dummy gray
    data = loader.bump_alloc(len(rgba_bytes), align=64)
    loader.write_bytes(data, rgba_bytes)
    world = loader.host_alloc(0x80)
    loader.write_bytes(world, b"\x00" * 0x80)
    rowbytes = width * 4
    loader.write_bytes(world + 0x18, struct.pack("<Q", data))
    loader.write_bytes(world + 0x20, struct.pack("<I", rowbytes))
    loader.write_bytes(world + 0x24, struct.pack("<I", width))
    loader.write_bytes(world + 0x28, struct.pack("<I", height))
    loader.write_bytes(world + 0x2C, struct.pack("<H", 8))
    return world

def main():
    loader = AexLoader(str(AEX_PATH), verbose=True)
    loader.register_libm_impls(max_threads=1)

    spbasic = build_host_suites(loader)
    in_data, dispatch = build_render_context(loader, spbasic)
    
    width, height = 1920, 200
    world_in = build_world(loader, 1920, 200)
    world_out = build_world(loader, 1920, 200)
    
    # We need to build the params array.
    # But instead of calling FUN_180007bd0 (which needs accurate params layout),
    # let's try to just run it and see where it crashes, then mock readers.
    
    params_arr = loader.host_alloc(8 * 30)
    loader.write_bytes(params_arr, b"\x00" * (8 * 30))
    # Build param_6 (extra)
    # param_6 has: [0] = PF_EffectWorld* (input), [1] = CBStruct*
    # CBStruct has: [0] = checkout_layer_pixels
    param_6 = loader.host_alloc(0x20)
    cb_struct = loader.host_alloc(0x20)
    
    def checkout_layer_pixels(ld, args):
        out_world_ptr = args[2]
        ld.write_bytes(out_world_ptr, struct.pack("<Q", world_in))
        return 0

    def checkout_output(ld, args):
        out_world_ptr = args[1]
        ld.write_bytes(out_world_ptr, struct.pack("<Q", world_out))
        return 0

    loader.write_bytes(cb_struct, struct.pack("<Q", loader.install_callback("checkout_layer", checkout_layer_pixels)))
    loader.write_bytes(cb_struct + 0x10, struct.pack("<Q", loader.install_callback("checkout_output", checkout_output)))
    
    loader.write_bytes(param_6, struct.pack("<Q", world_in))
    loader.write_bytes(param_6 + 8, struct.pack("<Q", cb_struct))

    
    # We will hook FUN_1800038d0 and dump param_7 state for row 169
    hook_called = False
    
    def hook_38d0(ld, addr, size):
        nonlocal hook_called
        param_1 = ld.uc.reg_read(UC_X86_REG_RCX)
        param_2 = ld.uc.reg_read(UC_X86_REG_RDX)
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        param_7 = struct.unpack("<Q", ld.read_bytes(rsp + 0x30, 8))[0]
        
        # param_5 is width, which is the 5th arg at [RSP + 0x20]
        param_5 = struct.unpack("<I", ld.read_bytes(rsp + 0x20, 4))[0]
        
        hook_called = True
        print(f"HOOK HIT! row {param_1} to {param_2}, width {param_5}")
        if param_1 <= 169 < param_2:
            # Dump param_7
            comp_map = u64(ld, param_7 + 0x8118)
            f_pow_exp = struct.unpack("<f", ld.read_bytes(param_7 + 0x30, 4))[0]
            f_pow_div = struct.unpack("<f", ld.read_bytes(param_7 + 0x38, 4))[0]
            denom_arr = u64(ld, param_7 + 0x8080)
            av_arr = u64(ld, param_7 + 0x8088)
            noise_mode = u32(ld, param_7 + 0x20)
            front_str = u32(ld, param_7 + 0x48)
            
            print(f"comp_map={hex(comp_map)}, exp={f_pow_exp}, div={f_pow_div}")
            print(f"denom={hex(denom_arr)}, av={hex(av_arr)}")
            print(f"noise_mode={noise_mode}, front_str={front_str}")
            
            # Print per-column state for row 169
            row = 169
            base_idx = row * param_5
            print("Col | av_src | comp_area | fVar10 | fVar11=p11 | span | left_reach")
            for col in range(param_5):
                idx = base_idx + col
                av = struct.unpack("<f", ld.read_bytes(av_arr + idx * 4, 4))[0]
                comp_area = struct.unpack("<f", ld.read_bytes(comp_map + idx * 16 + 0, 4))[0]
                
                fVar10 = 0.0
                if f_pow_div != 0:
                    fVar10 = (comp_area / f_pow_div) ** f_pow_exp
                fVar11 = 1.0 # default?
                p11 = fVar10 * fVar11
                span = int(front_str * p11)
                
                if av > 0:
                    print(f"{col:3d} | {av:6.3f} | {comp_area:9.3f} | {fVar10:6.3f} | {p11:6.3f} | {span:4d} | {col - (span - 1)}")
                    
            sys.exit(0)

    loader.add_code_hook(0x1800038d0, hook_38d0)

    def hook_28e0(ld, address, size):
        print("hook_28e0 called!")
        print(f"RCX = {hex(ld.uc.reg_read(UC_X86_REG_RCX))}")
        print(f"RDX = {hex(ld.uc.reg_read(UC_X86_REG_RDX))}")
        print(f"R8  = {hex(ld.uc.reg_read(UC_X86_REG_R8))}")
        print(f"R9  = {hex(ld.uc.reg_read(UC_X86_REG_R9))}")
        sys.exit(0)

    loader.add_code_hook(0x1800028e0, hook_28e0)

    def hook_5510(ld, address, size):
        r12 = ld.uc.reg_read(UC_X86_REG_R12)
        r14 = ld.uc.reg_read(UC_X86_REG_R14)
        print(f"hook_5510: R12={r12}, R14={r14}")
        return True

    loader.add_code_hook(0x180005510, hook_5510)
    
    def iterate_generic(ld, args):
        print(f"IterateGeneric CALLED!")
        print(f"arg0: {hex(args[0])}")
        print(f"arg1: {hex(args[1])}")
        print(f"arg2: {hex(args[2])}")
        print(f"arg3: {hex(args[3])}")
        print(f"arg4: {hex(args[4])}")
        sys.exit(0)
        return 0

    loader.write_bytes(
        dispatch + 0x20,
        struct.pack("<Q", loader.install_callback("RenderCtx.IterateGeneric", iterate_generic)),
    )


    # We will run FUN_180007bd0
    
    def hook_180006c50(ld, address, size):
        # FUN_180006c50(in_data, out_data, param_3, height, &local_8168)
        # Arg 5 is on the stack at [RSP + 0x28] (because of return address)
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        local_8168_ptr = struct.unpack("<Q", ld.read_bytes(rsp + 0x28, 8))[0]
        
        # Populate local_8168 with some blur params
        # iVar9 (offset 36), iVar17 (offset 40), iVar11 (offset 76), iVar15 (offset 84)
        # Let's set iVar9 = 5, iVar17 = 5 (Angle components)
        # Actually, Angle is index 1. Blur Strength is index 5?
        # Let's just set offset 36 to 10, offset 40 to 10, offset 76 to 10, offset 84 to 10
        # Also offset 0x34 is float fVar21?
        # And we must return 0
        
        ld.write_bytes(local_8168_ptr + 36, struct.pack("<I", 10))
        ld.write_bytes(local_8168_ptr + 40, struct.pack("<I", 10))
        ld.write_bytes(local_8168_ptr + 52, struct.pack("<f", 1.0))
        ld.write_bytes(local_8168_ptr + 56, struct.pack("<f", 1.0))
        ld.write_bytes(local_8168_ptr + 76, struct.pack("<I", 10))
        ld.write_bytes(local_8168_ptr + 84, struct.pack("<I", 10))
        ld.write_bytes(local_8168_ptr + 24, struct.pack("<f", -1.0))
        ld.write_bytes(local_8168_ptr + 32, struct.pack("<f", -1.0))
        ld.write_bytes(local_8168_ptr + 68, struct.pack("<f", -1.0))
        ld.write_bytes(local_8168_ptr + 0x1014, struct.pack("<I", 2000)) # width + margin
        ld.write_bytes(local_8168_ptr + 0x80a0, struct.pack("<I", 2000)) # width + margin
        ld.write_bytes(local_8168_ptr + 0x80a4, struct.pack("<I", 300)) # height + margin
        ld.write_bytes(local_8168_ptr + 0x8184, struct.pack("<f", 10.0))
        ld.write_bytes(local_8168_ptr + 0x8188, struct.pack("<f", 10.0))
        
        ld.uc.reg_write(UC_X86_REG_RAX, 0)
        ret_addr = struct.unpack("<Q", ld.read_bytes(rsp, 8))[0]
        ld.uc.reg_write(UC_X86_REG_RSP, rsp + 8)
        ld.uc.reg_write(UC_X86_REG_RIP, ret_addr)
        return True

    # loader.uc.hook_add(UC_HOOK_CODE, hook_code)
    loader.add_code_hook(0x180006c50, hook_180006c50)

    try:
        loader.call_function(FUN_180007bd0, int_args=[in_data, world_out, param_6], max_instructions=0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Exception: {e}")

    print(f"Hook called: {hook_called}")

if __name__ == "__main__":
    main()
