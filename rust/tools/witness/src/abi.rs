//! Windows x64 scalar ABI. Slots are positional, never packed by type.
use std::arch::global_asm;

#[derive(Default, Clone, Copy)]
#[repr(C)]
pub struct Return {
    pub rax: u64,
    pub xmm0: [u8; 16],
}
#[repr(C)]
pub struct Call {
    pub target: usize,
    pub slots: [u64; 32],
    pub result: Return,
}
impl Call {
    pub fn new(target: usize) -> Self {
        Self {
            target,
            slots: [0; 32],
            result: Return::default(),
        }
    }
    pub unsafe fn run(&mut self) -> Return {
        witness_invoke(self);
        self.result
    }
}

// 32-byte home space + 28 stack arguments = 256 bytes. RBX is the only
// nonvolatile register used. At CALL, RSP is 16-byte aligned. GP and XMM
// copies intentionally also support the Windows vararg duplication rule.
global_asm!(
    r#"
.text
.globl witness_invoke
.p2align 4
witness_invoke:
    push rbx
    sub rsp, 256
    mov rbx, rcx
    xor r10d, r10d
2:
    mov rax, [rbx + r10*8 + 40]
    mov [rsp + r10*8 + 32], rax
    inc r10d
    cmp r10d, 28
    jb 2b
    mov rcx, [rbx + 8]
    mov rdx, [rbx + 16]
    mov r8, [rbx + 24]
    mov r9, [rbx + 32]
    movq xmm0, rcx
    movq xmm1, rdx
    movq xmm2, r8
    movq xmm3, r9
    call qword ptr [rbx]
    mov [rbx + 264], rax
    movdqu [rbx + 272], xmm0
    add rsp, 256
    pop rbx
    ret

.globl witness_trace_entry
.p2align 4
witness_trace_entry:
    sub rsp, 136
    mov [rsp + 32], rcx
    mov [rsp + 40], rdx
    mov [rsp + 48], r8
    mov [rsp + 56], r9
    movq [rsp + 64], xmm0
    movq [rsp + 72], xmm1
    movq [rsp + 80], xmm2
    movq [rsp + 88], xmm3
    lea rax, [rsp + 176]
    mov [rsp + 96], rax
    mov rcx, r10
    lea rdx, [rsp + 32]
    call witness_trace_dispatch
    mov rax, [rsp + 104]
    movdqu xmm0, [rsp + 112]
    add rsp, 136
    ret
"#
);
extern "C" {
    fn witness_invoke(call: *mut Call);
    pub fn witness_trace_entry();
}

#[repr(C)]
pub struct TraceFrame {
    pub gp: [u64; 4],
    pub xmm: [u64; 4],
    pub stack: *const u64,
    pub result: Return,
}

#[cfg(test)]
mod tests {
    use super::*;
    global_asm!(
        r#"
    .text
    .globl witness_test_stack
    witness_test_stack:
        mov rax, rsp
        and eax, 15
        cmp eax, 8
        jne 3f
        mov [rsp + 8], rcx
        mov [rsp + 16], rdx
        mov [rsp + 24], r8
        mov [rsp + 32], r9
        mov rax, [rsp + 40]
        add rax, [rsp + 256]
        ret
    3:
        ud2
    "#
    );
    extern "C" {
        fn witness_test_stack();
    }
    #[test]
    fn alignment_shadow_and_argument_32() {
        let mut call = Call::new(witness_test_stack as usize);
        for i in 0..32 {
            call.slots[i] = i as u64 + 1;
        }
        assert_eq!(unsafe { call.run().rax }, 37);
    }
    unsafe extern "C" fn mixed(
        a: u64,
        b: f64,
        c: f32,
        d: u64,
        e: f64,
        f: u64,
        g: f32,
        p: *mut u64,
    ) -> f64 {
        *p = a ^ d ^ f;
        b + c as f64 + e + g as f64
    }
    unsafe extern "C" fn integer(a: u64, b: u64, c: u64, d: u64, e: u64) -> u64 {
        a.wrapping_add(b)
            .wrapping_add(c)
            .wrapping_add(d)
            .wrapping_add(e)
    }
    #[test]
    fn mixed_register_stack_and_returns() {
        for i in 0..1000u64 {
            let mut output = 0;
            let mut call = Call::new(mixed as usize);
            call.slots[..8].copy_from_slice(&[
                i,
                1.25f64.to_bits(),
                (-2.5f32).to_bits() as u64,
                77,
                9.5f64.to_bits(),
                123,
                0.25f32.to_bits() as u64,
                &mut output as *mut u64 as u64,
            ]);
            let r = unsafe { call.run() };
            assert_eq!(f64::from_le_bytes(r.xmm0[..8].try_into().unwrap()), 8.5);
            assert_eq!(output, i ^ 77 ^ 123);
            let mut call = Call::new(integer as usize);
            call.slots[..5].copy_from_slice(&[i, 2, 3, 4, 5]);
            assert_eq!(unsafe { call.run().rax }, i + 14);
        }
    }
}
