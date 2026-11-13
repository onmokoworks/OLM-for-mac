// Retained contour loops and blending helpers.
use super::support::*;
pub(super) use super::structured::*;
pub(super) unsafe fn ColorBlend16(mut param_1: *mut u64, mut param_2: *mut u16, mut param_3: i32) -> () {
let mut uVar1: u16 = 0;
let mut uVar2: u16 = 0;
let mut uVar3: u16 = 0;
let mut uVar5: u16 = 0;
let mut puVar4: *mut u16 = std::ptr::null_mut();
let mut uVar6: u32 = 0;
let mut uVar7: u32 = 0;
let mut uVar8: u32 = 0;
let mut uVar11: u32 = 0;
let mut uVar13: u32 = 0;
let mut iVar9: i32 = 0;
let mut iVar12: i32 = 0;
let mut puVar14: *mut u64 = std::ptr::null_mut();
let mut fVar15: f32 = 0.0;
let mut fVar16: f32 = 0.0;
let mut fVar17: f32 = 0.0;
let mut fVar18: f32 = 0.0;
let mut fVar19: f32 = 0.0;
let mut fVar20: f32 = 0.0;
let mut fVar21: f32 = 0.0;
let mut fVar22: f32 = 0.0;
let mut fVar23: f32 = 0.0;
let mut uVar6_outer: u32 = 0;
let mut uVar10: u64 = 0;
let mut uVar10_27: u64 = 0;
let mut pc: u32=105;
loop {match pc {
1 => { if (fVar18 <= 0.0_f32) {pc=26;} else {pc=30;} continue; },
3 => { let _ = {(*param_2) = uVar5; (*param_2)};return ; },
4 => { let _ = {uVar5 = (32768_i32 as u16); uVar5};let _ = {(*param_2) = uVar5; (*param_2)};return ; },
7 => { let _ = {(*(param_2).wrapping_offset(2_i32 as isize)) = uVar5; (*(param_2).wrapping_offset(2_i32 as isize))};let _ = {uVar5 = (uVar6 as u16); uVar5};if ((32768_i32 as u32) < ((uVar6 & (65535_i32 as u32)))) {pc=4;} else {pc=3;} continue; },
8 => { let _ = {uVar5 = (32768_i32 as u16); uVar5};let _ = {(*(param_2).wrapping_offset(2_i32 as isize)) = uVar5; (*(param_2).wrapping_offset(2_i32 as isize))};let _ = {uVar5 = (uVar6 as u16); uVar5};if ((32768_i32 as u32) < ((uVar6 & (65535_i32 as u32)))) {pc=4;} else {pc=3;} continue; },
11 => { let _ = {(*(param_2).wrapping_offset(1_i32 as isize)) = uVar5; (*(param_2).wrapping_offset(1_i32 as isize))};let _ = {uVar5 = (uVar11 as u16); uVar5};if ((32768_i32 as u32) < ((uVar11 & (65535_i32 as u32)))) {pc=8;} else {pc=7;} continue; },
12 => { let _ = {uVar5 = (32768_i32 as u16); uVar5};let _ = {(*(param_2).wrapping_offset(1_i32 as isize)) = uVar5; (*(param_2).wrapping_offset(1_i32 as isize))};let _ = {uVar5 = (uVar11 as u16); uVar5};if ((32768_i32 as u32) < ((uVar11 & (65535_i32 as u32)))) {pc=8;} else {pc=7;} continue; },
15 => { let _ = {(*(param_2).wrapping_offset(3_i32 as isize)) = uVar5; (*(param_2).wrapping_offset(3_i32 as isize))};let _ = {uVar5 = (uVar8 as u16); uVar5};if ((32768_i32 as u32) < ((uVar8 & (65535_i32 as u32)))) {pc=12;} else {pc=11;} continue; },
16 => { let _ = {uVar5 = (32768_i32 as u16); uVar5};let _ = {(*(param_2).wrapping_offset(3_i32 as isize)) = uVar5; (*(param_2).wrapping_offset(3_i32 as isize))};let _ = {uVar5 = (uVar8 as u16); uVar5};if ((32768_i32 as u32) < ((uVar8 & (65535_i32 as u32)))) {pc=12;} else {pc=11;} continue; },
26 => { let _ = {uVar6 = ((*param_2) as u32); uVar6};let _ = {uVar7 = ((*(param_2).wrapping_offset(1_i32 as isize)) as u32); uVar7};let _ = {uVar13 = ((*(param_2).wrapping_offset(3_i32 as isize)) as u32); uVar13};let _ = {uVar11 = ((*(param_2).wrapping_offset(2_i32 as isize)) as u32); uVar11};let _ = {fVar18 = ((((uVar6 & (65535_i32 as u32))) as f32) * DAT_18000d250); fVar18};let _ = {uVar8 = (olm_math::x86::cvttss2si((((((uVar7 & (65535_i32 as u32))) as f32) / fVar18))) as u32); uVar8};let _ = {uVar11 = (olm_math::x86::cvttss2si((((((uVar11 & (65535_i32 as u32))) as f32) / fVar18))) as u32); uVar11};let _ = {uVar7 = (olm_math::x86::cvttss2si((((((uVar13 & (65535_i32 as u32))) as f32) / fVar18))) as u32); uVar7};let _ = {uVar5 = (uVar7 as u16); uVar5};if ((32768_i32 as u32) < ((uVar7 & (65535_i32 as u32)))) {pc=16;} else {pc=15;} continue; },
30 => { let _ = {uVar6 = (olm_math::x86::cvttss2si(((fVar19 / fVar18))) as u32); uVar6};let _ = {uVar7 = (olm_math::x86::cvttss2si(((fVar20 / fVar18))) as u32); uVar7};let _ = {uVar13 = (olm_math::x86::cvttss2si(((fVar21 / fVar18))) as u32); uVar13};let _ = {uVar11 = (olm_math::x86::cvttss2si(((fVar22 / fVar18))) as u32); uVar11};let _ = {fVar18 = ((((uVar6 & (65535_i32 as u32))) as f32) * DAT_18000d250); fVar18};let _ = {uVar8 = (olm_math::x86::cvttss2si((((((uVar7 & (65535_i32 as u32))) as f32) / fVar18))) as u32); uVar8};let _ = {uVar11 = (olm_math::x86::cvttss2si((((((uVar11 & (65535_i32 as u32))) as f32) / fVar18))) as u32); uVar11};let _ = {uVar7 = (olm_math::x86::cvttss2si((((((uVar13 & (65535_i32 as u32))) as f32) / fVar18))) as u32); uVar7};let _ = {uVar5 = (uVar7 as u16); uVar5};if ((32768_i32 as u32) < ((uVar7 & (65535_i32 as u32)))) {pc=16;} else {pc=15;} continue; },
38 => { let _ = {fVar19 = (fVar19 + (uVar5 as f32)); fVar19};let _ = {fVar20 = (fVar20 + ((uVar1 as f32) * fVar16)); fVar20};let _ = {fVar21 = (fVar21 + ((uVar2 as f32) * fVar16)); fVar21};let _ = {fVar22 = (fVar22 + ((uVar3 as f32) * fVar16)); fVar22};let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {uVar10_27 = (uVar10_27).wrapping_sub((1_i32 as u64)); uVar10_27};if (uVar10_27 != (0_i32 as u64)) {pc=38;} else {pc=1;} continue; },
40 => { let _ = {fVar16 = ((uVar5 as f32) * DAT_18000d250); fVar16};uVar10_27 = ((((param_3).wrapping_sub(iVar9)) as u32) as u64);let _ = {fVar19 = (fVar19 + (uVar5 as f32)); fVar19};let _ = {fVar20 = (fVar20 + ((uVar1 as f32) * fVar16)); fVar20};let _ = {fVar21 = (fVar21 + ((uVar2 as f32) * fVar16)); fVar21};let _ = {fVar22 = (fVar22 + ((uVar3 as f32) * fVar16)); fVar22};let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {uVar10_27 = (uVar10_27).wrapping_sub((1_i32 as u64)); uVar10_27};if (uVar10_27 != (0_i32 as u64)) {pc=38;} else {pc=1;} continue; },
45 => { let _ = {puVar4 = (*((((param_1 as *mut u8)).wrapping_offset((32_i32 as isize))) as *mut *mut u16)); puVar4};let _ = {uVar5 = (*puVar4); uVar5};let _ = {uVar1 = (*(puVar4).wrapping_offset(1_i32 as isize)); uVar1};let _ = {uVar2 = (*(puVar4).wrapping_offset(3_i32 as isize)); uVar2};let _ = {uVar3 = (*(puVar4).wrapping_offset(2_i32 as isize)); uVar3};let _ = {fVar16 = ((uVar5 as f32) * DAT_18000d250); fVar16};uVar10_27 = ((((param_3).wrapping_sub(iVar9)) as u32) as u64);let _ = {fVar19 = (fVar19 + (uVar5 as f32)); fVar19};let _ = {fVar20 = (fVar20 + ((uVar1 as f32) * fVar16)); fVar20};let _ = {fVar21 = (fVar21 + ((uVar2 as f32) * fVar16)); fVar21};let _ = {fVar22 = (fVar22 + ((uVar3 as f32) * fVar16)); fVar22};let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {uVar10_27 = (uVar10_27).wrapping_sub((1_i32 as u64)); uVar10_27};if (uVar10_27 != (0_i32 as u64)) {pc=38;} else {pc=1;} continue; },
46 => { if (fVar18 <= 0.0_f32) {pc=26;} else {pc=30;} continue; },
47 => { if (param_3 < 1_i32) {pc=46;} else {pc=45;} continue; },
48 => { if (fVar18 <= 0.0_f32) {pc=26;} else {pc=30;} continue; },
49 => { if (param_3 <= iVar9) {pc=48;} else {pc=40;} continue; },
56 => { let _ = {fVar18 = ((((((((fVar18 + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4); fVar18};let _ = {fVar19 = ((((((((fVar23 + fVar19) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23); fVar19};let _ = {fVar20 = ((((((((fVar15 + fVar20) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15); fVar20};let _ = {fVar21 = ((((((((fVar17 + fVar21) + fVar17) + fVar17) + fVar17) + fVar17) + fVar17) + fVar17) + fVar17); fVar21};let _ = {fVar22 = ((((((((fVar16 + fVar22) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16); fVar22};let _ = {uVar10 = (uVar10).wrapping_sub((1_i32 as u64)); uVar10};if (uVar10 != (0_i32 as u64)) {pc=56;} else {pc=49;} continue; },
69 => { let _ = {puVar4 = (*((((param_1 as *mut u8)).wrapping_offset((32_i32 as isize))) as *mut *mut u16)); puVar4};let _ = {uVar5 = (*puVar4); uVar5};let _ = {uVar1 = (*(puVar4).wrapping_offset(1_i32 as isize)); uVar1};let _ = {uVar2 = (*(puVar4).wrapping_offset(3_i32 as isize)); uVar2};let _ = {uVar3 = (*(puVar4).wrapping_offset(2_i32 as isize)); uVar3};let _ = {fVar23 = (uVar5 as f32); fVar23};uVar6_outer = ((((((param_3).wrapping_sub(8_i32)) as u32)).wrapping_shr(3_i32 as u32))).wrapping_add((1_i32 as u32));uVar10 = (uVar6_outer as u64);let _ = {iVar9 = (((uVar6_outer).wrapping_mul((8_i32 as u32))) as i32); iVar9};let _ = {fVar16 = (fVar23 * DAT_18000d250); fVar16};let _ = {fVar15 = ((uVar1 as f32) * fVar16); fVar15};let _ = {fVar17 = ((uVar2 as f32) * fVar16); fVar17};let _ = {fVar16 = ((uVar3 as f32) * fVar16); fVar16};let _ = {fVar18 = ((((((((fVar18 + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4); fVar18};let _ = {fVar19 = ((((((((fVar23 + fVar19) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23); fVar19};let _ = {fVar20 = ((((((((fVar15 + fVar20) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15); fVar20};let _ = {fVar21 = ((((((((fVar17 + fVar21) + fVar17) + fVar17) + fVar17) + fVar17) + fVar17) + fVar17) + fVar17); fVar21};let _ = {fVar22 = ((((((((fVar16 + fVar22) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16); fVar22};let _ = {uVar10 = (uVar10).wrapping_sub((1_i32 as u64)); uVar10};if (uVar10 != (0_i32 as u64)) {pc=56;} else {pc=49;} continue; },
70 => { if (param_3 < 8_i32) {pc=47;} else {pc=69;} continue; },
73 => { let _ = {iVar12 = (iVar12).wrapping_add(3_i32); iVar12};let _ = {puVar14 = (puVar14).wrapping_offset((3_i32 as isize)); puVar14};if (iVar12 < 9_i32) {pc=97;} else {pc=70;} continue; },
79 => { let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {fVar19 = (fVar19 + ((*puVar4) as f32)); fVar19};let _ = {fVar16 = (((*puVar4) as f32) * DAT_18000d250); fVar16};let _ = {fVar20 = (fVar20 + (((*(puVar4).wrapping_offset(1_i32 as isize)) as f32) * fVar16)); fVar20};let _ = {fVar21 = (fVar21 + (((*(puVar4).wrapping_offset(3_i32 as isize)) as f32) * fVar16)); fVar21};let _ = {fVar22 = (fVar22 + (((*(puVar4).wrapping_offset(2_i32 as isize)) as f32) * fVar16)); fVar22};let _ = {iVar12 = (iVar12).wrapping_add(3_i32); iVar12};let _ = {puVar14 = (puVar14).wrapping_offset((3_i32 as isize)); puVar14};if (iVar12 < 9_i32) {pc=97;} else {pc=70;} continue; },
81 => { let _ = {puVar4 = ((*puVar14) as *mut u16); puVar4};if (((puVar4 != (std::ptr::null_mut::<u8>() as *mut u16))) && ((iVar12 != 2_i32))) {pc=79;} else {pc=73;} continue; },
87 => { let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {fVar19 = (fVar19 + ((*puVar4) as f32)); fVar19};let _ = {fVar16 = (((*puVar4) as f32) * DAT_18000d250); fVar16};let _ = {fVar20 = (fVar20 + (((*(puVar4).wrapping_offset(1_i32 as isize)) as f32) * fVar16)); fVar20};let _ = {fVar21 = (fVar21 + (((*(puVar4).wrapping_offset(3_i32 as isize)) as f32) * fVar16)); fVar21};let _ = {fVar22 = (fVar22 + (((*(puVar4).wrapping_offset(2_i32 as isize)) as f32) * fVar16)); fVar22};let _ = {puVar4 = ((*puVar14) as *mut u16); puVar4};if (((puVar4 != (std::ptr::null_mut::<u8>() as *mut u16))) && ((iVar12 != 2_i32))) {pc=79;} else {pc=73;} continue; },
89 => { let _ = {puVar4 = ((*(puVar14).wrapping_offset((1_i32).wrapping_neg() as isize)) as *mut u16); puVar4};if (((puVar4 != (std::ptr::null_mut::<u8>() as *mut u16))) && ((iVar12 != 3_i32))) {pc=87;} else {pc=81;} continue; },
95 => { let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {fVar19 = (fVar19 + ((*puVar4) as f32)); fVar19};let _ = {fVar16 = (((*puVar4) as f32) * DAT_18000d250); fVar16};let _ = {fVar20 = (fVar20 + (((*(puVar4).wrapping_offset(1_i32 as isize)) as f32) * fVar16)); fVar20};let _ = {fVar21 = (fVar21 + (((*(puVar4).wrapping_offset(3_i32 as isize)) as f32) * fVar16)); fVar21};let _ = {fVar22 = (fVar22 + (((*(puVar4).wrapping_offset(2_i32 as isize)) as f32) * fVar16)); fVar22};let _ = {puVar4 = ((*(puVar14).wrapping_offset((1_i32).wrapping_neg() as isize)) as *mut u16); puVar4};if (((puVar4 != (std::ptr::null_mut::<u8>() as *mut u16))) && ((iVar12 != 3_i32))) {pc=87;} else {pc=81;} continue; },
97 => { let _ = {puVar4 = ((*(puVar14).wrapping_offset((2_i32).wrapping_neg() as isize)) as *mut u16); puVar4};if (((puVar4 != (std::ptr::null_mut::<u8>() as *mut u16))) && ((iVar12 != 4_i32))) {pc=95;} else {pc=89;} continue; },
105 => { iVar9 = 0_i32;iVar12 = 0_i32;puVar14 = (param_1).wrapping_offset((2_i32 as isize));let _ = {fVar18 = 0.0_f32; fVar18};let _ = {fVar19 = 0.0_f32; fVar19};let _ = {fVar20 = 0.0_f32; fVar20};let _ = {fVar21 = 0.0_f32; fVar21};let _ = {fVar22 = 0.0_f32; fVar22};let _ = {puVar4 = ((*(puVar14).wrapping_offset((2_i32).wrapping_neg() as isize)) as *mut u16); puVar4};if (((puVar4 != (std::ptr::null_mut::<u8>() as *mut u16))) && ((iVar12 != 4_i32))) {pc=95;} else {pc=89;} continue; },
_ => unreachable!(),
}}}

pub(super) unsafe fn ColorBlend8(mut param_1: *mut u64, mut param_2: *mut u8, mut param_3: i32) -> () {
let mut bVar1: u8 = 0;
let mut bVar2: u8 = 0;
let mut bVar3: u8 = 0;
let mut bVar4: u8 = 0;
let mut pbVar5: *mut u8 = std::ptr::null_mut();
let mut uVar6: u32 = 0;
let mut uVar9: u32 = 0;
let mut uVar11: u32 = 0;
let mut uVar12: u32 = 0;
let mut iVar7: i32 = 0;
let mut iVar10: i32 = 0;
let mut puVar13: *mut u64 = std::ptr::null_mut();
let mut fVar14: f32 = 0.0;
let mut fVar15: f32 = 0.0;
let mut fVar16: f32 = 0.0;
let mut fVar17: f32 = 0.0;
let mut fVar18: f32 = 0.0;
let mut fVar19: f32 = 0.0;
let mut fVar20: f32 = 0.0;
let mut fVar21: f32 = 0.0;
let mut fVar22: f32 = 0.0;
let mut fVar23: f32 = 0.0;
let mut uVar8: u64 = 0;
let mut uVar8_26: u64 = 0;
let mut pc: u32=91;
loop {match pc {
1 => { if (fVar18 <= 0.0_f32) {pc=11;} else {pc=15;} continue; },
11 => { let _ = {uVar9 = ((*param_2) as u32); uVar9};let _ = {uVar6 = ((*(param_2).wrapping_offset(1_i32 as isize)) as u32); uVar6};let _ = {uVar11 = ((*(param_2).wrapping_offset(3_i32 as isize)) as u32); uVar11};let _ = {uVar12 = ((*(param_2).wrapping_offset(2_i32 as isize)) as u32); uVar12};let _ = {(*param_2) = (uVar9 as u8); (*param_2)};let _ = {fVar17 = ((((uVar9 & (255_i32 as u32))) as f32) / fVar17); fVar17};let _ = {(*(param_2).wrapping_offset(1_i32 as isize)) = ((olm_math::x86::cvttss2si((((((uVar6 & (255_i32 as u32))) as f32) / fVar17))) as i32) as u8); (*(param_2).wrapping_offset(1_i32 as isize))};let _ = {(*(param_2).wrapping_offset(3_i32 as isize)) = ((olm_math::x86::cvttss2si((((((uVar11 & (255_i32 as u32))) as f32) / fVar17))) as i32) as u8); (*(param_2).wrapping_offset(3_i32 as isize))};let _ = {(*(param_2).wrapping_offset(2_i32 as isize)) = ((olm_math::x86::cvttss2si((((((uVar12 & (255_i32 as u32))) as f32) / fVar17))) as i32) as u8); (*(param_2).wrapping_offset(2_i32 as isize))};return ; },
15 => { let _ = {uVar9 = (olm_math::x86::cvttss2si(((fVar19 / fVar18))) as u32); uVar9};let _ = {uVar6 = (olm_math::x86::cvttss2si(((fVar20 / fVar18))) as u32); uVar6};let _ = {uVar11 = (olm_math::x86::cvttss2si(((fVar21 / fVar18))) as u32); uVar11};let _ = {uVar12 = (olm_math::x86::cvttss2si(((fVar22 / fVar18))) as u32); uVar12};let _ = {(*param_2) = (uVar9 as u8); (*param_2)};let _ = {fVar17 = ((((uVar9 & (255_i32 as u32))) as f32) / fVar17); fVar17};let _ = {(*(param_2).wrapping_offset(1_i32 as isize)) = ((olm_math::x86::cvttss2si((((((uVar6 & (255_i32 as u32))) as f32) / fVar17))) as i32) as u8); (*(param_2).wrapping_offset(1_i32 as isize))};let _ = {(*(param_2).wrapping_offset(3_i32 as isize)) = ((olm_math::x86::cvttss2si((((((uVar11 & (255_i32 as u32))) as f32) / fVar17))) as i32) as u8); (*(param_2).wrapping_offset(3_i32 as isize))};let _ = {(*(param_2).wrapping_offset(2_i32 as isize)) = ((olm_math::x86::cvttss2si((((((uVar12 & (255_i32 as u32))) as f32) / fVar17))) as i32) as u8); (*(param_2).wrapping_offset(2_i32 as isize))};return ; },
23 => { let _ = {fVar19 = (fVar19 + (bVar1 as f32)); fVar19};let _ = {fVar20 = (fVar20 + ((bVar2 as f32) * fVar15)); fVar20};let _ = {fVar21 = (fVar21 + ((bVar3 as f32) * fVar15)); fVar21};let _ = {fVar22 = (fVar22 + ((bVar4 as f32) * fVar15)); fVar22};let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {uVar8_26 = (uVar8_26).wrapping_sub((1_i32 as u64)); uVar8_26};if (uVar8_26 != (0_i32 as u64)) {pc=23;} else {pc=1;} continue; },
25 => { let _ = {fVar15 = ((bVar1 as f32) / DAT_18000d268); fVar15};uVar8_26 = ((((param_3).wrapping_sub(iVar7)) as u32) as u64);let _ = {fVar19 = (fVar19 + (bVar1 as f32)); fVar19};let _ = {fVar20 = (fVar20 + ((bVar2 as f32) * fVar15)); fVar20};let _ = {fVar21 = (fVar21 + ((bVar3 as f32) * fVar15)); fVar21};let _ = {fVar22 = (fVar22 + ((bVar4 as f32) * fVar15)); fVar22};let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {uVar8_26 = (uVar8_26).wrapping_sub((1_i32 as u64)); uVar8_26};if (uVar8_26 != (0_i32 as u64)) {pc=23;} else {pc=1;} continue; },
30 => { let _ = {pbVar5 = (*((((param_1 as *mut u8)).wrapping_offset((32_i32 as isize))) as *mut *mut u8)); pbVar5};let _ = {bVar1 = (*pbVar5); bVar1};let _ = {bVar2 = (*(pbVar5).wrapping_offset(1_i32 as isize)); bVar2};let _ = {bVar3 = (*(pbVar5).wrapping_offset(3_i32 as isize)); bVar3};let _ = {bVar4 = (*(pbVar5).wrapping_offset(2_i32 as isize)); bVar4};let _ = {fVar15 = ((bVar1 as f32) / DAT_18000d268); fVar15};uVar8_26 = ((((param_3).wrapping_sub(iVar7)) as u32) as u64);let _ = {fVar19 = (fVar19 + (bVar1 as f32)); fVar19};let _ = {fVar20 = (fVar20 + ((bVar2 as f32) * fVar15)); fVar20};let _ = {fVar21 = (fVar21 + ((bVar3 as f32) * fVar15)); fVar21};let _ = {fVar22 = (fVar22 + ((bVar4 as f32) * fVar15)); fVar22};let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {uVar8_26 = (uVar8_26).wrapping_sub((1_i32 as u64)); uVar8_26};if (uVar8_26 != (0_i32 as u64)) {pc=23;} else {pc=1;} continue; },
31 => { if (fVar18 <= 0.0_f32) {pc=11;} else {pc=15;} continue; },
32 => { if (param_3 < 1_i32) {pc=31;} else {pc=30;} continue; },
33 => { if (fVar18 <= 0.0_f32) {pc=11;} else {pc=15;} continue; },
34 => { if (param_3 <= iVar7) {pc=33;} else {pc=25;} continue; },
41 => { let _ = {fVar18 = ((((((((fVar18 + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4); fVar18};let _ = {fVar19 = ((((((((fVar23 + fVar19) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23); fVar19};let _ = {fVar20 = ((((((((fVar14 + fVar20) + fVar14) + fVar14) + fVar14) + fVar14) + fVar14) + fVar14) + fVar14); fVar20};let _ = {fVar21 = ((((((((fVar16 + fVar21) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16); fVar21};let _ = {fVar22 = ((((((((fVar15 + fVar22) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15); fVar22};let _ = {uVar8 = (uVar8).wrapping_sub((1_i32 as u64)); uVar8};if (uVar8 != (0_i32 as u64)) {pc=41;} else {pc=34;} continue; },
54 => { let _ = {pbVar5 = (*((((param_1 as *mut u8)).wrapping_offset((32_i32 as isize))) as *mut *mut u8)); pbVar5};let _ = {bVar1 = (*pbVar5); bVar1};let _ = {bVar2 = (*(pbVar5).wrapping_offset(1_i32 as isize)); bVar2};let _ = {bVar3 = (*(pbVar5).wrapping_offset(3_i32 as isize)); bVar3};let _ = {bVar4 = (*(pbVar5).wrapping_offset(2_i32 as isize)); bVar4};let _ = {fVar23 = (bVar1 as f32); fVar23};let _ = {uVar6 = ((((((param_3).wrapping_sub(8_i32)) as u32)).wrapping_shr(3_i32 as u32))).wrapping_add((1_i32 as u32)); uVar6};uVar8 = (uVar6 as u64);let _ = {fVar15 = (fVar23 / DAT_18000d268); fVar15};let _ = {iVar7 = (((uVar6).wrapping_mul((8_i32 as u32))) as i32); iVar7};let _ = {fVar14 = ((bVar2 as f32) * fVar15); fVar14};let _ = {fVar16 = ((bVar3 as f32) * fVar15); fVar16};let _ = {fVar15 = ((bVar4 as f32) * fVar15); fVar15};let _ = {fVar18 = ((((((((fVar18 + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4) + DAT_18000d1f4); fVar18};let _ = {fVar19 = ((((((((fVar23 + fVar19) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23) + fVar23); fVar19};let _ = {fVar20 = ((((((((fVar14 + fVar20) + fVar14) + fVar14) + fVar14) + fVar14) + fVar14) + fVar14) + fVar14); fVar20};let _ = {fVar21 = ((((((((fVar16 + fVar21) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16) + fVar16); fVar21};let _ = {fVar22 = ((((((((fVar15 + fVar22) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15) + fVar15); fVar22};let _ = {uVar8 = (uVar8).wrapping_sub((1_i32 as u64)); uVar8};if (uVar8 != (0_i32 as u64)) {pc=41;} else {pc=34;} continue; },
55 => { if (param_3 < 8_i32) {pc=32;} else {pc=54;} continue; },
58 => { let _ = {iVar10 = (iVar10).wrapping_add(3_i32); iVar10};let _ = {puVar13 = (puVar13).wrapping_offset((3_i32 as isize)); puVar13};if (iVar10 < 9_i32) {pc=82;} else {pc=55;} continue; },
64 => { let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {fVar19 = (fVar19 + ((*pbVar5) as f32)); fVar19};let _ = {fVar15 = (((*pbVar5) as f32) / DAT_18000d268); fVar15};let _ = {fVar20 = (fVar20 + (((*(pbVar5).wrapping_offset(1_i32 as isize)) as f32) * fVar15)); fVar20};let _ = {fVar21 = (fVar21 + (((*(pbVar5).wrapping_offset(3_i32 as isize)) as f32) * fVar15)); fVar21};let _ = {fVar22 = (fVar22 + (((*(pbVar5).wrapping_offset(2_i32 as isize)) as f32) * fVar15)); fVar22};let _ = {iVar10 = (iVar10).wrapping_add(3_i32); iVar10};let _ = {puVar13 = (puVar13).wrapping_offset((3_i32 as isize)); puVar13};if (iVar10 < 9_i32) {pc=82;} else {pc=55;} continue; },
66 => { let _ = {pbVar5 = ((*puVar13) as *mut u8); pbVar5};if (((pbVar5 != (std::ptr::null_mut::<u8>() as *mut u8))) && ((iVar10 != 2_i32))) {pc=64;} else {pc=58;} continue; },
72 => { let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {fVar19 = (fVar19 + ((*pbVar5) as f32)); fVar19};let _ = {fVar15 = (((*pbVar5) as f32) / DAT_18000d268); fVar15};let _ = {fVar20 = (fVar20 + (((*(pbVar5).wrapping_offset(1_i32 as isize)) as f32) * fVar15)); fVar20};let _ = {fVar21 = (fVar21 + (((*(pbVar5).wrapping_offset(3_i32 as isize)) as f32) * fVar15)); fVar21};let _ = {fVar22 = (fVar22 + (((*(pbVar5).wrapping_offset(2_i32 as isize)) as f32) * fVar15)); fVar22};let _ = {pbVar5 = ((*puVar13) as *mut u8); pbVar5};if (((pbVar5 != (std::ptr::null_mut::<u8>() as *mut u8))) && ((iVar10 != 2_i32))) {pc=64;} else {pc=58;} continue; },
74 => { let _ = {pbVar5 = ((*(puVar13).wrapping_offset((1_i32).wrapping_neg() as isize)) as *mut u8); pbVar5};if (((pbVar5 != (std::ptr::null_mut::<u8>() as *mut u8))) && ((iVar10 != 3_i32))) {pc=72;} else {pc=66;} continue; },
80 => { let _ = {fVar18 = (fVar18 + DAT_18000d1f4); fVar18};let _ = {fVar19 = (fVar19 + ((*pbVar5) as f32)); fVar19};let _ = {fVar15 = (((*pbVar5) as f32) / DAT_18000d268); fVar15};let _ = {fVar20 = (fVar20 + (((*(pbVar5).wrapping_offset(1_i32 as isize)) as f32) * fVar15)); fVar20};let _ = {fVar21 = (fVar21 + (((*(pbVar5).wrapping_offset(3_i32 as isize)) as f32) * fVar15)); fVar21};let _ = {fVar22 = (fVar22 + (((*(pbVar5).wrapping_offset(2_i32 as isize)) as f32) * fVar15)); fVar22};let _ = {pbVar5 = ((*(puVar13).wrapping_offset((1_i32).wrapping_neg() as isize)) as *mut u8); pbVar5};if (((pbVar5 != (std::ptr::null_mut::<u8>() as *mut u8))) && ((iVar10 != 3_i32))) {pc=72;} else {pc=66;} continue; },
82 => { let _ = {pbVar5 = ((*(puVar13).wrapping_offset((2_i32).wrapping_neg() as isize)) as *mut u8); pbVar5};if (((pbVar5 != (std::ptr::null_mut::<u8>() as *mut u8))) && ((iVar10 != 4_i32))) {pc=80;} else {pc=74;} continue; },
91 => { iVar7 = 0_i32;iVar10 = 0_i32;puVar13 = (param_1).wrapping_offset((2_i32 as isize));let _ = {fVar17 = DAT_18000d268; fVar17};let _ = {fVar18 = 0.0_f32; fVar18};let _ = {fVar19 = 0.0_f32; fVar19};let _ = {fVar20 = 0.0_f32; fVar20};let _ = {fVar21 = 0.0_f32; fVar21};let _ = {fVar22 = 0.0_f32; fVar22};let _ = {pbVar5 = ((*(puVar13).wrapping_offset((2_i32).wrapping_neg() as isize)) as *mut u8); pbVar5};if (((pbVar5 != (std::ptr::null_mut::<u8>() as *mut u8))) && ((iVar10 != 4_i32))) {pc=80;} else {pc=74;} continue; },
_ => unreachable!(),
}}}

pub(super) unsafe fn AlphaBlend16(mut param_1: *mut u16, mut param_2: f32, mut param_3: *mut u16, mut param_4: f32, mut param_5: *mut u16) -> () {
let mut fVar1: f32 = 0.0;
let mut fVar6: f32 = 0.0;
let mut fVar7: f32 = 0.0;
let mut alpha_first: f32 = 0.0;
let mut alpha_second: f32 = 0.0;
let mut alpha_sum: f32 = 0.0;
let mut fVar3: f32 = 0.0;
let mut fVar5: f32 = 0.0;
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut fVar4: f32 = 0.0;
let mut fVar2: f32 = 0.0;
let mut pc: u32=35;
loop {match pc {
3 => { let _ = {(*(param_5).wrapping_offset(2_i32 as isize)) = (((olm_math::x86::cvttss2si(fVar3) as i32) as i16) as u16); (*(param_5).wrapping_offset(2_i32 as isize))};let _ = {(*param_5) = (((olm_math::x86::cvttss2si(fVar5) as i32) as i16) as u16); (*param_5)};return ; },
4 => { let _ = {fVar3 = 0.0_f32; fVar3};let _ = {(*(param_5).wrapping_offset(2_i32 as isize)) = (((olm_math::x86::cvttss2si(fVar3) as i32) as i16) as u16); (*(param_5).wrapping_offset(2_i32 as isize))};let _ = {(*param_5) = (((olm_math::x86::cvttss2si(fVar5) as i32) as i16) as u16); (*param_5)};return ; },
5 => { if (fVar2 < 0.0_f32) {pc=4;} else {pc=3;} continue; },
6 => { let _ = {fVar3 = fVar1; fVar3};if (fVar2 < 0.0_f32) {pc=4;} else {pc=3;} continue; },
9 => { let _ = {(*(param_5).wrapping_offset(1_i32 as isize)) = (((olm_math::x86::cvttss2si(fVar3) as i32) as i16) as u16); (*(param_5).wrapping_offset(1_i32 as isize))};let _ = {fVar3 = fVar2; fVar3};if (fVar1 < fVar2) {pc=6;} else {pc=5;} continue; },
10 => { let _ = {fVar3 = 0.0_f32; fVar3};let _ = {(*(param_5).wrapping_offset(1_i32 as isize)) = (((olm_math::x86::cvttss2si(fVar3) as i32) as i16) as u16); (*(param_5).wrapping_offset(1_i32 as isize))};let _ = {fVar3 = fVar2; fVar3};if (fVar1 < fVar2) {pc=6;} else {pc=5;} continue; },
11 => { if (fVar4 < 0.0_f32) {pc=10;} else {pc=9;} continue; },
12 => { let _ = {fVar3 = fVar1; fVar3};if (fVar4 < 0.0_f32) {pc=10;} else {pc=9;} continue; },
15 => { let _ = {(*(param_5).wrapping_offset(3_i32 as isize)) = (((olm_math::x86::cvttss2si(fVar3) as i32) as i16) as u16); (*(param_5).wrapping_offset(3_i32 as isize))};let _ = {fVar3 = fVar4; fVar3};if (fVar1 < fVar4) {pc=12;} else {pc=11;} continue; },
16 => { let _ = {fVar3 = 0.0_f32; fVar3};let _ = {(*(param_5).wrapping_offset(3_i32 as isize)) = (((olm_math::x86::cvttss2si(fVar3) as i32) as i16) as u16); (*(param_5).wrapping_offset(3_i32 as isize))};let _ = {fVar3 = fVar4; fVar3};if (fVar1 < fVar4) {pc=12;} else {pc=11;} continue; },
17 => { if (fVar6 < 0.0_f32) {pc=16;} else {pc=15;} continue; },
18 => { let _ = {fVar3 = DAT_18000d26c; fVar3};if (fVar6 < 0.0_f32) {pc=16;} else {pc=15;} continue; },
23 => { fVar4 = (|mut first: u16, mut first_weight: f32, mut first_alpha: f32, mut second: u16, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(1_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(1_i32 as isize)), param_4, fVar6, fVar5);fVar2 = (|mut first: u16, mut first_weight: f32, mut first_alpha: f32, mut second: u16, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(2_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(2_i32 as isize)), param_4, fVar6, fVar5);let _ = {fVar6 = (|mut first: u16, mut first_weight: f32, mut first_alpha: f32, mut second: u16, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(3_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(3_i32 as isize)), param_4, fVar6, fVar5); fVar6};let _ = {fVar3 = fVar6; fVar3};if (DAT_18000d26c < fVar6) {pc=18;} else {pc=17;} continue; },
24 => { let _ = {fVar5 = 0.0_f32; fVar5};fVar4 = (|mut first: u16, mut first_weight: f32, mut first_alpha: f32, mut second: u16, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(1_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(1_i32 as isize)), param_4, fVar6, fVar5);fVar2 = (|mut first: u16, mut first_weight: f32, mut first_alpha: f32, mut second: u16, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(2_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(2_i32 as isize)), param_4, fVar6, fVar5);let _ = {fVar6 = (|mut first: u16, mut first_weight: f32, mut first_alpha: f32, mut second: u16, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(3_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(3_i32 as isize)), param_4, fVar6, fVar5); fVar6};let _ = {fVar3 = fVar6; fVar3};if (DAT_18000d26c < fVar6) {pc=18;} else {pc=17;} continue; },
25 => { if (fVar3 < 0.0_f32) {pc=24;} else {pc=23;} continue; },
26 => { let _ = {fVar5 = DAT_18000d26c; fVar5};if (fVar3 < 0.0_f32) {pc=24;} else {pc=23;} continue; },
35 => { fVar1 = DAT_18000d26c;fVar6 = ((*param_3) as f32);fVar7 = ((*param_1) as f32);alpha_first = (fVar7 * param_2);alpha_second = (fVar6 * param_4);alpha_sum = (alpha_first + alpha_second);fVar3 = alpha_sum;fVar5 = fVar3;if (DAT_18000d26c < fVar3) {pc=26;} else {pc=25;} continue; },
_ => unreachable!(),
}}}

pub(super) unsafe fn AlphaBlend8(mut param_1: *mut u8, mut param_2: f32, mut param_3: *mut u8, mut param_4: f32, mut param_5: *mut u8) -> () {
let mut fVar1: f32 = 0.0;
let mut fVar6: f32 = 0.0;
let mut fVar7: f32 = 0.0;
let mut alpha_first: f32 = 0.0;
let mut alpha_second: f32 = 0.0;
let mut alpha_sum: f32 = 0.0;
let mut fVar3: f32 = 0.0;
let mut fVar5: f32 = 0.0;
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut fVar4: f32 = 0.0;
let mut fVar2: f32 = 0.0;
let mut fVar3b: f32 = 0.0;
let mut pc: u32=35;
loop {match pc {
3 => { let _ = {(*(param_5).wrapping_offset(2_i32 as isize)) = ((olm_math::x86::cvttss2si(fVar3) as i32) as u8); (*(param_5).wrapping_offset(2_i32 as isize))};let _ = {(*param_5) = ((olm_math::x86::cvttss2si(fVar5) as i32) as u8); (*param_5)};return ; },
4 => { let _ = {fVar3 = 0.0_f32; fVar3};let _ = {(*(param_5).wrapping_offset(2_i32 as isize)) = ((olm_math::x86::cvttss2si(fVar3) as i32) as u8); (*(param_5).wrapping_offset(2_i32 as isize))};let _ = {(*param_5) = ((olm_math::x86::cvttss2si(fVar5) as i32) as u8); (*param_5)};return ; },
5 => { if (fVar2 < 0.0_f32) {pc=4;} else {pc=3;} continue; },
6 => { let _ = {fVar3 = fVar1; fVar3};if (fVar2 < 0.0_f32) {pc=4;} else {pc=3;} continue; },
9 => { let _ = {(*(param_5).wrapping_offset(1_i32 as isize)) = ((olm_math::x86::cvttss2si(fVar3) as i32) as u8); (*(param_5).wrapping_offset(1_i32 as isize))};let _ = {fVar3 = fVar2; fVar3};if (fVar1 < fVar2) {pc=6;} else {pc=5;} continue; },
10 => { let _ = {fVar3 = 0.0_f32; fVar3};let _ = {(*(param_5).wrapping_offset(1_i32 as isize)) = ((olm_math::x86::cvttss2si(fVar3) as i32) as u8); (*(param_5).wrapping_offset(1_i32 as isize))};let _ = {fVar3 = fVar2; fVar3};if (fVar1 < fVar2) {pc=6;} else {pc=5;} continue; },
11 => { if (fVar4 < 0.0_f32) {pc=10;} else {pc=9;} continue; },
12 => { let _ = {fVar3 = fVar1; fVar3};if (fVar4 < 0.0_f32) {pc=10;} else {pc=9;} continue; },
15 => { let _ = {(*(param_5).wrapping_offset(3_i32 as isize)) = ((olm_math::x86::cvttss2si(fVar3b) as i32) as u8); (*(param_5).wrapping_offset(3_i32 as isize))};let _ = {fVar3 = fVar4; fVar3};if (fVar1 < fVar4) {pc=12;} else {pc=11;} continue; },
16 => { let _ = {fVar3b = 0.0_f32; fVar3b};let _ = {(*(param_5).wrapping_offset(3_i32 as isize)) = ((olm_math::x86::cvttss2si(fVar3b) as i32) as u8); (*(param_5).wrapping_offset(3_i32 as isize))};let _ = {fVar3 = fVar4; fVar3};if (fVar1 < fVar4) {pc=12;} else {pc=11;} continue; },
17 => { if (fVar6 < 0.0_f32) {pc=16;} else {pc=15;} continue; },
18 => { let _ = {fVar3b = DAT_18000d268; fVar3b};if (fVar6 < 0.0_f32) {pc=16;} else {pc=15;} continue; },
23 => { fVar4 = (|mut first: u8, mut first_weight: f32, mut first_alpha: f32, mut second: u8, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(1_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(1_i32 as isize)), param_4, fVar6, fVar5);fVar2 = (|mut first: u8, mut first_weight: f32, mut first_alpha: f32, mut second: u8, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(2_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(2_i32 as isize)), param_4, fVar6, fVar5);let _ = {fVar6 = (|mut first: u8, mut first_weight: f32, mut first_alpha: f32, mut second: u8, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(3_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(3_i32 as isize)), param_4, fVar6, fVar5); fVar6};fVar3b = fVar6;if (DAT_18000d268 < fVar6) {pc=18;} else {pc=17;} continue; },
24 => { let _ = {fVar5 = 0.0_f32; fVar5};fVar4 = (|mut first: u8, mut first_weight: f32, mut first_alpha: f32, mut second: u8, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(1_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(1_i32 as isize)), param_4, fVar6, fVar5);fVar2 = (|mut first: u8, mut first_weight: f32, mut first_alpha: f32, mut second: u8, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(2_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(2_i32 as isize)), param_4, fVar6, fVar5);let _ = {fVar6 = (|mut first: u8, mut first_weight: f32, mut first_alpha: f32, mut second: u8, mut second_weight: f32, mut second_alpha: f32, mut divisor: f32| -> f32 {
let mut first_product: f32 = 0.0;
let mut second_product: f32 = 0.0;
let mut sum: f32 = 0.0;
let mut pc: u32=7;
loop {match pc {
7 => { first_product = ((first as f32) * first_weight);let _ = {first_product = (first_product * first_alpha); first_product};second_product = ((second as f32) * second_weight);let _ = {second_product = (second_product * second_alpha); second_product};sum = (first_product + second_product);return (sum / divisor); },
_ => unreachable!(),
}}}
)((*(param_1).wrapping_offset(3_i32 as isize)), param_2, fVar7, (*(param_3).wrapping_offset(3_i32 as isize)), param_4, fVar6, fVar5); fVar6};fVar3b = fVar6;if (DAT_18000d268 < fVar6) {pc=18;} else {pc=17;} continue; },
25 => { if (fVar3 < 0.0_f32) {pc=24;} else {pc=23;} continue; },
26 => { let _ = {fVar5 = DAT_18000d268; fVar5};if (fVar3 < 0.0_f32) {pc=24;} else {pc=23;} continue; },
35 => { fVar1 = DAT_18000d268;fVar6 = ((*param_3) as f32);fVar7 = ((*param_1) as f32);alpha_first = (fVar7 * param_2);alpha_second = (fVar6 * param_4);alpha_sum = (alpha_first + alpha_second);fVar3 = alpha_sum;fVar5 = fVar3;if (DAT_18000d268 < fVar3) {pc=26;} else {pc=25;} continue; },
_ => unreachable!(),
}}}

pub(super) unsafe fn EdgeWalker16Exact(mut state: *mut RenderState, mut x: i32, mut y: i32, mut dir1: i32, mut dir2: u32, mut out_x: *mut i32, mut out_y: *mut i32, mut threshold: i32) -> *mut u16 {
let mut R: Regs = Regs::default();
let mut M: Memory = Memory::default();
let mut T: u64 = 0;
let mut args: [u64; 4] = [0; 4];
let mut i: u64 = 0;
'b435: {
'b427: {
'b426: {
'b434: {
'b441: {
'b440: {
'b449: {
'b448: {
'b1038: {
'b1031: {
'b454: {
'b1025: {
'b1030: {
'b1037: {
'b1149: {
'b1143: {
'b1120: {
'b1099: {
'b1078: {
'b1055: {
'b1054: {
'b1077: {
'b1098: {
'b1119: {
'b1142: {
'b1148: {
'b1165: {
'b1164: {
'b1185: {
'b1184: {
'b1246: {
'b1230: {
'b1224: {
'b1217: {
'b1210: {
'b1203: {
'b1196: {
'b1195: {
'b1202: {
'b1209: {
'b1216: {
'b1223: {
'b1229: {
'b1245: {
'b1289: {
'b1284: {
'b1278: {
'b1273: {
'b1272: {
'b1277: {
'b1283: {
'b1288: {
'b1322: {
'b1317: {
'b1311: {
'b1306: {
'b1305: {
'b1310: {
'b1316: {
'b1321: {
'b1: {
'b1388: {
R = Regs::default();M = Memory::default();T = (0_i32 as u64);let _ = {(M).state = state; (M).state};let _ = {(M).world = (*state).src_world; (M).world};let _ = {(M).pf16 = true; (M).pf16};let _ = {(R).rcx = (state as u64); (R).rcx};let _ = {(R).rdx = ((x as u32) as u64); (R).rdx};let _ = {(R).r8 = ((y as u32) as u64); (R).r8};let _ = {(R).r9 = ((dir1 as u32) as u64); (R).r9};let _ = {(R).rsp = (KSTACK).wrapping_add((2048_i32 as u64)); (R).rsp};let _ = M.write64((R).rsp,16045690984833335023_u64);args = [(dir2 as u64), (out_x as u64), (out_y as u64), ((threshold as u32) as u64)];i = (0_i32 as u64);
if (i < ((std::mem::size_of::<[u64; 4]>() as u64) / (std::mem::size_of::<u64>() as u64))) { break 'b1388; } else { break 'b1; }
}
'l1388: loop {
let _ = M.write64((((R).rsp).wrapping_add((40_i32 as u64))).wrapping_add((i).wrapping_mul((8_i32 as u64))),(*((args).as_mut_ptr() as *mut u64).wrapping_offset(i as isize)));let _ = {let old=i; i=(i).wrapping_add(1); i};
if (i < ((std::mem::size_of::<[u64; 4]>() as u64) / (std::mem::size_of::<u64>() as u64))) { continue 'l1388; } else { break 'b1; }
}
}
let _ = M.write64((((R).rsp).wrapping_add(16_u64)),(R).rbx);let _ = M.write64((((R).rsp).wrapping_add(24_u64)),(R).rbp);let _ = M.write64((((R).rsp).wrapping_add(32_u64)),(R).rsi);let _ = M.write64((((R).rsp).wrapping_add(8_u64)),(R).rcx);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).rdi);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).r12);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).r13);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).r14);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).r15);let _ = {(R).r15 = M.read64((((R).rsp).wrapping_add(88_u64))); (R).r15};let _ = {(R).r11 = (((6442490249_i64 as u64)).wrapping_sub(39305_u64)); (R).r11};let _ = {(R).r12 = M.read64((((R).rsp).wrapping_add(96_u64))); (R).r12};let _ = {T = (((((R).rbp as u32)) ^ (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rbp = ((T as u32) as u64); (R).rbp};let _ = {(R).r14 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r14};let _ = {(R).r10 = (((((R).rdx as u32) as i32) as i64) as u64); (R).r10};let _ = {(R).rax = (((((R).r9 as u32) as i32) as i64) as u64); (R).rax};let _ = {(R).r9 = ((((R).rax).wrapping_mul(4_u64))); (R).r9};let _ = {(R).rsi = (M.read32(((((R).r9).wrapping_add((R).r11)).wrapping_add(61640_u64))) as u64); (R).rsi};let _ = {(R).rdi = (M.read32(((((R).r9).wrapping_add((R).r11)).wrapping_add(61680_u64))) as u64); (R).rdi};let _ = {T = M.addflags((((R).rsi as u32) as u64),(((R).r10 as u32) as u64),32_i32); T};let _ = {(R).rsi = ((T as u32) as u64); (R).rsi};let _ = M.write32(((R).r15),((R).r10 as u32));let _ = {T = M.addflags((((R).rdi as u32) as u64),(((R).r8 as u32) as u64),32_i32); T};let _ = {(R).rdi = ((T as u32) as u64); (R).rdi};let _ = M.write32(((R).r12),((R).r8 as u32));let _ = {(R).r9 = (((R).rbp as u32) as u64); (R).r9};let _ = {(R).rdx = M.read64((((R).rcx).wrapping_add(24_u64))); (R).rdx};let _ = {T = (((((R).r10 as u32)) & (((R).r10 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1322; } else { break 'b1321; }
}
let _ = {T = M.subflags((((R).r10 as u32) as u64),(M.read32((((R).rdx).wrapping_add(36_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b1317; } else { break 'b1316; }
}
let _ = {T = (((((R).r8 as u32)) & (((R).r8 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1311; } else { break 'b1310; }
}
let _ = {T = M.subflags((((R).r8 as u32) as u64),(M.read32((((R).rdx).wrapping_add(40_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b1306; } else { break 'b1305; }
}
let _ = {(R).r8 = (((((((R).r8 as u32) as i32) as i64)).wrapping_mul(((M.read32((((R).rdx).wrapping_add(32_u64))) as i32) as i64)) as u32) as u64); (R).r8};let _ = {(R).rcx = (((((R).r8 as u32) as i32) as i64) as u64); (R).rcx};let _ = {(R).r9 = (((R).rcx).wrapping_add((((R).r10).wrapping_mul(8_u64)))); (R).r9};let _ = {T = M.addflags((R).r9,M.read64((((R).rdx).wrapping_add(24_u64))),64_i32); T};let _ = {(R).r9 = T; (R).r9};let _ = {(R).r10 = (R).rbp; (R).r10};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1289; } else { break 'b1288; }
}
let _ = {(R).r10 = (R).rbp; (R).r10};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1289; } else { break 'b1288; }
}
let _ = {(R).r10 = (R).rbp; (R).r10};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1289; } else { break 'b1288; }
}
let _ = {(R).r10 = (R).rbp; (R).r10};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1289; } else { break 'b1288; }
}
let _ = {(R).r10 = (R).rbp; (R).r10};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1289; } else { break 'b1288; }
}
let _ = {T = M.subflags((((R).rsi as u32) as u64),(M.read32((((R).rdx).wrapping_add(36_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b1284; } else { break 'b1283; }
}
let _ = {T = (((((R).rdi as u32)) & (((R).rdi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1278; } else { break 'b1277; }
}
let _ = {T = M.subflags((((R).rdi as u32) as u64),(M.read32((((R).rdx).wrapping_add(40_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b1273; } else { break 'b1272; }
}
let _ = {(R).rax = (((R).rdi as u32) as u64); (R).rax};let _ = {(R).rax = (((((((R).rax as u32) as i32) as i64)).wrapping_mul(((M.read32((((R).rdx).wrapping_add(32_u64))) as i32) as i64)) as u32) as u64); (R).rax};let _ = {(R).rcx = (((((R).rax as u32) as i32) as i64) as u64); (R).rcx};let _ = {(R).rax = (((((R).rsi as u32) as i32) as i64) as u64); (R).rax};let _ = {(R).r10 = (((R).rcx).wrapping_add((((R).rax).wrapping_mul(8_u64)))); (R).r10};let _ = {T = M.addflags((R).r10,M.read64((((R).rdx).wrapping_add(24_u64))),64_i32); T};let _ = {(R).r10 = T; (R).r10};let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).rcx = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).rcx};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).rcx as u32));let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1246; } else { break 'b1245; }
}
let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).rcx = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).rcx};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).rcx as u32));let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1246; } else { break 'b1245; }
}
let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).rcx = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).rcx};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).rcx as u32));let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1246; } else { break 'b1245; }
}
let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).rcx = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).rcx};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).rcx as u32));let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1246; } else { break 'b1245; }
}
let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).rcx = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).rcx};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).rcx as u32));let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1246; } else { break 'b1245; }
}
let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | ((((!(M).zf) as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | ((((!(M).zf) as u8)) as u64)); (R).r11};let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1230; } else { break 'b1229; }
}
let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1224; } else { break 'b1223; }
}
let _ = {(R).rax = ((M.read16((((R).r10).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r9).wrapping_add(2_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b1217; } else { break 'b1216; }
}
let _ = {(R).rax = ((M.read16((((R).r10).wrapping_add(6_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r9).wrapping_add(6_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b1210; } else { break 'b1209; }
}
let _ = {(R).rax = ((M.read16((((R).r10).wrapping_add(4_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r9).wrapping_add(4_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b1203; } else { break 'b1202; }
}
let _ = {(R).rax = ((M.read16(((R).r10)) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16(((R).r9)) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b1196; } else { break 'b1195; }
}
let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {(R).r8 = (((R).r14 as u32) as u64); (R).r8};let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1185; } else { break 'b1184; }
}
let _ = {(R).r8 = (((((R).r8 as u32))).wrapping_shl((((7_u64) & (63_i32 as u64))) as u32) as u64); (R).r8};let _ = {T = (((((R).r8 as u32)) & (((R).r8 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | ((((!(M).sf) as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1165; } else { break 'b1164; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {(R).r8 = (((((R).r8 as u32))).wrapping_shl((((7_u64) & (63_i32 as u64))) as u32) as u64); (R).r8};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1165; } else { break 'b1164; }
}
let _ = {T = (((((R).r8 as u32)) & (((R).r8 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | ((((!(M).sf) as u8)) as u64)); (R).r11};let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1149; } else { break 'b1148; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1149; } else { break 'b1148; }
}
let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1143; } else { break 'b1142; }
}
let _ = {(R).rax = ((M.read16((((R).r10).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {(R).rcx = ((M.read16((((R).r9).wrapping_add(2_u64))) as u32) as u64); (R).rcx};let _ = {T = M.subflags((((R).rcx as u32) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = {(R).rcx = ((T as u32) as u64); (R).rcx};let _ = {(R).rax = (((R).rcx as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r8 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b1120; } else { break 'b1119; }
}
let _ = {(R).rcx = ((M.read16((((R).r10).wrapping_add(6_u64))) as u32) as u64); (R).rcx};let _ = {(R).rax = ((M.read16((((R).r9).wrapping_add(6_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rcx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r8 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b1099; } else { break 'b1098; }
}
let _ = {(R).rcx = ((M.read16((((R).r10).wrapping_add(4_u64))) as u32) as u64); (R).rcx};let _ = {(R).rax = ((M.read16((((R).r9).wrapping_add(4_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rcx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r8 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b1078; } else { break 'b1077; }
}
let _ = {(R).rax = ((M.read16(((R).r10)) as u32) as u64); (R).rax};let _ = {(R).rcx = ((M.read16(((R).r9)) as u32) as u64); (R).rcx};let _ = {T = M.subflags((((R).rcx as u32) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = {(R).rcx = ((T as u32) as u64); (R).rcx};let _ = {(R).rax = (((R).rcx as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r8 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b1055; } else { break 'b1054; }
}
let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1038; } else { break 'b1037; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1031; } else { break 'b1030; }
}
'l1030: loop {
'b455: {
'b568: {
'b562: {
'b537: {
'b516: {
'b495: {
'b474: {
'b473: {
'b494: {
'b515: {
'b536: {
'b561: {
'b567: {
'b677: {
'b671: {
'b646: {
'b625: {
'b604: {
'b581: {
'b580: {
'b603: {
'b624: {
'b645: {
'b670: {
'b676: {
'b786: {
'b780: {
'b755: {
'b734: {
'b713: {
'b690: {
'b689: {
'b712: {
'b733: {
'b754: {
'b779: {
'b785: {
'b929: {
'b829: {
'b823: {
'b816: {
'b809: {
'b802: {
'b795: {
'b794: {
'b801: {
'b808: {
'b815: {
'b822: {
'b828: {
'b876: {
'b870: {
'b863: {
'b856: {
'b849: {
'b842: {
'b841: {
'b848: {
'b855: {
'b862: {
'b869: {
'b875: {
'b923: {
'b917: {
'b910: {
'b903: {
'b896: {
'b889: {
'b888: {
'b895: {
'b902: {
'b909: {
'b916: {
'b922: {
'b928: {
'b964: {
'b959: {
'b953: {
'b948: {
'b947: {
'b952: {
'b958: {
'b963: {
'b997: {
'b992: {
'b986: {
'b981: {
'b980: {
'b985: {
'b991: {
'b996: {
'b1024: {
let _ = {T = ((((((R).rax as u8)) as i32) & ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b1025; } else { break 'b1024; }
}
let _ = {T = M.addflags((M.read32(((R).r15)) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = M.write32(((R).r15),(T as u32));let _ = {T = M.addflags((((R).rdi as u32) as u64),(((R).rcx as u32) as u64),32_i32); T};let _ = {(R).rdi = ((T as u32) as u64); (R).rdi};let _ = {T = M.addflags((M.read32(((R).r12)) as u64),(((R).rcx as u32) as u64),32_i32); T};let _ = M.write32(((R).r12),(T as u32));let _ = {T = M.addflags((((R).rsi as u32) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = {(R).rsi = ((T as u32) as u64); (R).rsi};let _ = {(R).rcx = M.read64((((R).rsp).wrapping_add(48_u64))); (R).rcx};let _ = {(R).r8 = (R).rbp; (R).r8};let _ = {(R).r11 = (((M.read32(((R).r15)) as i32) as i64) as u64); (R).r11};let _ = {(R).rax = (M.read32(((R).r12)) as u64); (R).rax};let _ = {(R).rdx = M.read64((((R).rcx).wrapping_add(24_u64))); (R).rdx};let _ = {T = (((((R).r11 as u32)) & (((R).r11 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b997; } else { break 'b996; }
}
let _ = {T = M.subflags((((R).r11 as u32) as u64),(M.read32((((R).rdx).wrapping_add(36_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b992; } else { break 'b991; }
}
let _ = {T = (((((R).rax as u32)) & (((R).rax as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b986; } else { break 'b985; }
}
let _ = {T = M.subflags((((R).rax as u32) as u64),(M.read32((((R).rdx).wrapping_add(40_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b981; } else { break 'b980; }
}
let _ = {(R).rax = (((((((R).rax as u32) as i32) as i64)).wrapping_mul(((M.read32((((R).rdx).wrapping_add(32_u64))) as i32) as i64)) as u32) as u64); (R).rax};let _ = {(R).rcx = (((((R).rax as u32) as i32) as i64) as u64); (R).rcx};let _ = {(R).r8 = (((R).rcx).wrapping_add((((R).r11).wrapping_mul(8_u64)))); (R).r8};let _ = {T = M.addflags((R).r8,M.read64((((R).rdx).wrapping_add(24_u64))),64_i32); T};let _ = {(R).r8 = T; (R).r8};let _ = {(R).rcx = (R).rbp; (R).rcx};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b964; } else { break 'b963; }
}
let _ = {(R).rcx = (R).rbp; (R).rcx};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b964; } else { break 'b963; }
}
let _ = {(R).rcx = (R).rbp; (R).rcx};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b964; } else { break 'b963; }
}
let _ = {(R).rcx = (R).rbp; (R).rcx};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b964; } else { break 'b963; }
}
let _ = {(R).rcx = (R).rbp; (R).rcx};let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b964; } else { break 'b963; }
}
let _ = {T = M.subflags((((R).rsi as u32) as u64),(M.read32((((R).rdx).wrapping_add(36_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b959; } else { break 'b958; }
}
let _ = {T = (((((R).rdi as u32)) & (((R).rdi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b953; } else { break 'b952; }
}
let _ = {T = M.subflags((((R).rdi as u32) as u64),(M.read32((((R).rdx).wrapping_add(40_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b948; } else { break 'b947; }
}
let _ = {(R).rax = (((R).rdi as u32) as u64); (R).rax};let _ = {(R).rax = (((((((R).rax as u32) as i32) as i64)).wrapping_mul(((M.read32((((R).rdx).wrapping_add(32_u64))) as i32) as i64)) as u32) as u64); (R).rax};let _ = {(R).rcx = (((((R).rax as u32) as i32) as i64) as u64); (R).rcx};let _ = {(R).rax = (((((R).rsi as u32) as i32) as i64) as u64); (R).rax};let _ = {(R).rcx = (((R).rcx).wrapping_add((((R).rax).wrapping_mul(8_u64)))); (R).rcx};let _ = {T = M.addflags((R).rcx,M.read64((((R).rdx).wrapping_add(24_u64))),64_i32); T};let _ = {(R).rcx = T; (R).rcx};let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b929; } else { break 'b928; }
}
let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b929; } else { break 'b928; }
}
let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b929; } else { break 'b928; }
}
let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b929; } else { break 'b928; }
}
let _ = {T = (((((R).r14 as u32)) & (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b929; } else { break 'b928; }
}
let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b923; } else { break 'b922; }
}
let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b917; } else { break 'b916; }
}
let _ = {(R).rax = ((M.read16((((R).r8).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r9).wrapping_add(2_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b910; } else { break 'b909; }
}
let _ = {(R).rax = ((M.read16((((R).r8).wrapping_add(6_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r9).wrapping_add(6_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b903; } else { break 'b902; }
}
let _ = {(R).rax = ((M.read16((((R).r8).wrapping_add(4_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r9).wrapping_add(4_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b896; } else { break 'b895; }
}
let _ = {(R).rax = ((M.read16(((R).r8)) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16(((R).r9)) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b889; } else { break 'b888; }
}
let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b876; } else { break 'b875; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b876; } else { break 'b875; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b876; } else { break 'b875; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b876; } else { break 'b875; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b876; } else { break 'b875; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b876; } else { break 'b875; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b876; } else { break 'b875; }
}
let _ = {T = (((R).rcx) & ((R).rcx)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b870; } else { break 'b869; }
}
let _ = {(R).rax = ((M.read16((((R).rcx).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r10).wrapping_add(2_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b863; } else { break 'b862; }
}
let _ = {(R).rax = ((M.read16((((R).rcx).wrapping_add(6_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r10).wrapping_add(6_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b856; } else { break 'b855; }
}
let _ = {(R).rax = ((M.read16((((R).rcx).wrapping_add(4_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r10).wrapping_add(4_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b849; } else { break 'b848; }
}
let _ = {(R).rax = ((M.read16(((R).rcx)) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16(((R).r10)) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b842; } else { break 'b841; }
}
let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b829; } else { break 'b828; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b829; } else { break 'b828; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b829; } else { break 'b828; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b829; } else { break 'b828; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b829; } else { break 'b828; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b829; } else { break 'b828; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b829; } else { break 'b828; }
}
let _ = {T = (((R).rcx) & ((R).rcx)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b823; } else { break 'b822; }
}
let _ = {(R).rax = ((M.read16((((R).rcx).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r8).wrapping_add(2_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b816; } else { break 'b815; }
}
let _ = {(R).rax = ((M.read16((((R).rcx).wrapping_add(6_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r8).wrapping_add(6_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b809; } else { break 'b808; }
}
let _ = {(R).rax = ((M.read16((((R).rcx).wrapping_add(4_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16((((R).r8).wrapping_add(4_u64))) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b802; } else { break 'b801; }
}
let _ = {(R).rax = ((M.read16(((R).rcx)) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read16(((R).r8)) as u64),(((R).rax as u16) as u64),16_i32); T};
if (!(M).zf) { break 'b795; } else { break 'b794; }
}
let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b786; } else { break 'b785; }
}
let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b780; } else { break 'b779; }
}
let _ = {(R).rdx = ((M.read16((((R).r8).wrapping_add(2_u64))) as u32) as u64); (R).rdx};let _ = {(R).r11 = (((R).r14 as u32) as u64); (R).r11};let _ = {(R).rax = ((M.read16((((R).r9).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).r11 = (((((R).r11 as u32))).wrapping_shl((((7_u64) & (63_i32 as u64))) as u32) as u64); (R).r11};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r11 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b755; } else { break 'b754; }
}
let _ = {(R).rdx = ((M.read16((((R).r8).wrapping_add(6_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read16((((R).r9).wrapping_add(6_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r11 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b734; } else { break 'b733; }
}
let _ = {(R).rdx = ((M.read16((((R).r8).wrapping_add(4_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read16((((R).r9).wrapping_add(4_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r11 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b713; } else { break 'b712; }
}
let _ = {(R).rax = ((M.read16(((R).r8)) as u32) as u64); (R).rax};let _ = {(R).rdx = ((M.read16(((R).r9)) as u32) as u64); (R).rdx};let _ = {T = M.subflags((((R).rdx as u32) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = {(R).rdx = ((T as u32) as u64); (R).rdx};let _ = {(R).rax = (((R).rdx as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r11 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b690; } else { break 'b689; }
}
let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b677; } else { break 'b676; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b677; } else { break 'b676; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b677; } else { break 'b676; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b677; } else { break 'b676; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b677; } else { break 'b676; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b677; } else { break 'b676; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) ^ ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rbx = ((((R).rbx & (!255_u64))) | (((T as u8)) as u64)); (R).rbx};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b677; } else { break 'b676; }
}
let _ = {T = (((R).rcx) & ((R).rcx)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b671; } else { break 'b670; }
}
let _ = {(R).rdx = ((M.read16((((R).rcx).wrapping_add(2_u64))) as u32) as u64); (R).rdx};let _ = {(R).r9 = (((R).r14 as u32) as u64); (R).r9};let _ = {(R).rax = ((M.read16((((R).r10).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).r9 = (((((R).r9 as u32))).wrapping_shl((((7_u64) & (63_i32 as u64))) as u32) as u64); (R).r9};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r9 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b646; } else { break 'b645; }
}
let _ = {(R).rdx = ((M.read16((((R).rcx).wrapping_add(6_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read16((((R).r10).wrapping_add(6_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r9 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b625; } else { break 'b624; }
}
let _ = {(R).rdx = ((M.read16((((R).rcx).wrapping_add(4_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read16((((R).r10).wrapping_add(4_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r9 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b604; } else { break 'b603; }
}
let _ = {(R).rax = ((M.read16(((R).rcx)) as u32) as u64); (R).rax};let _ = {(R).rdx = ((M.read16(((R).r10)) as u32) as u64); (R).rdx};let _ = {T = M.subflags((((R).rdx as u32) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = {(R).rdx = ((T as u32) as u64); (R).rdx};let _ = {(R).rax = (((R).rdx as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r9 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b581; } else { break 'b580; }
}
let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b568; } else { break 'b567; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b568; } else { break 'b567; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b568; } else { break 'b567; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b568; } else { break 'b567; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b568; } else { break 'b567; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b568; } else { break 'b567; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b568; } else { break 'b567; }
}
let _ = {T = (((R).rcx) & ((R).rcx)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b562; } else { break 'b561; }
}
let _ = {(R).rdx = ((M.read16((((R).rcx).wrapping_add(2_u64))) as u32) as u64); (R).rdx};let _ = {(R).r9 = (((R).r14 as u32) as u64); (R).r9};let _ = {(R).rax = ((M.read16((((R).r8).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).r9 = (((((R).r9 as u32))).wrapping_shl((((7_u64) & (63_i32 as u64))) as u32) as u64); (R).r9};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r9 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b537; } else { break 'b536; }
}
let _ = {(R).rdx = ((M.read16((((R).rcx).wrapping_add(6_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read16((((R).r8).wrapping_add(6_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r9 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b516; } else { break 'b515; }
}
let _ = {(R).rdx = ((M.read16((((R).rcx).wrapping_add(4_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read16((((R).r8).wrapping_add(4_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r9 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b495; } else { break 'b494; }
}
let _ = {(R).rdx = ((M.read16(((R).rcx)) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read16(((R).r8)) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).r9 as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b474; } else { break 'b473; }
}
let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {(R).rcx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rcx};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b455; } else { break 'b454; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1031; } else { continue 'l1030; }
}
}
let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b449; } else { break 'b448; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b449; } else { break 'b448; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b449; } else { break 'b448; }
}

if (!(M).zf) { break 'b449; } else { break 'b448; }
}
let _ = {(R).rax = ((1_u64 as u32) as u64); (R).rax};let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b441; } else { break 'b440; }
}
let _ = {(R).rbp = (M.read32((((R).rsp).wrapping_add(80_u64))) as u64); (R).rbp};let _ = {(R).rax = ((1_u64 as u32) as u64); (R).rax};let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b441; } else { break 'b440; }
}
let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b435; } else { break 'b434; }
}
let _ = {(R).rbp = (((R).rax as u32) as u64); (R).rbp};let _ = {T = ((((((R).rbx as u8)) as i32) & ((((R).rbx as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b435; } else { break 'b434; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((2_u64 as u32) as u64); (R).rax};
if (M).zf { break 'b427; } else { break 'b426; }
}
let _ = {(R).rax = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rax};let _ = {T = M.subflags((M.read32(((R).r15)) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = M.write32(((R).r15),(T as u32));let _ = {T = M.subflags((M.read32(((R).r12)) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = M.write32(((R).r12),(T as u32));let _ = {(R).rax = (((R).rbp as u32) as u64); (R).rax};let _ = {(R).rbp = M.read64((((R).rsp).wrapping_add(64_u64))); (R).rbp};let _ = {(R).rbx = M.read64((((R).rsp).wrapping_add(56_u64))); (R).rbx};let _ = {(R).rsi = M.read64((((R).rsp).wrapping_add(72_u64))); (R).rsi};let _ = {(R).r15 = M.read64((R).rsp); (R).r15};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r14 = M.read64((R).rsp); (R).r14};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r13 = M.read64((R).rsp); (R).r13};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r12 = M.read64((R).rsp); (R).r12};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).rdi = M.read64((R).rsp); (R).rdi};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};return ((R).rax as *mut u16);
}
let _ = {(R).rbp = (((R).rax as u32) as u64); (R).rbp};let _ = {(R).rax = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rax};let _ = {T = M.subflags((M.read32(((R).r15)) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = M.write32(((R).r15),(T as u32));let _ = {T = M.subflags((M.read32(((R).r12)) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = M.write32(((R).r12),(T as u32));let _ = {(R).rax = (((R).rbp as u32) as u64); (R).rax};let _ = {(R).rbp = M.read64((((R).rsp).wrapping_add(64_u64))); (R).rbp};let _ = {(R).rbx = M.read64((((R).rsp).wrapping_add(56_u64))); (R).rbx};let _ = {(R).rsi = M.read64((((R).rsp).wrapping_add(72_u64))); (R).rsi};let _ = {(R).r15 = M.read64((R).rsp); (R).r15};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r14 = M.read64((R).rsp); (R).r14};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r13 = M.read64((R).rsp); (R).r13};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r12 = M.read64((R).rsp); (R).r12};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).rdi = M.read64((R).rsp); (R).rdi};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};return ((R).rax as *mut u16);
}
let _ = {(R).rax = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rax};let _ = {T = M.subflags((M.read32(((R).r15)) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = M.write32(((R).r15),(T as u32));let _ = {T = M.subflags((M.read32(((R).r12)) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = M.write32(((R).r12),(T as u32));let _ = {(R).rax = (((R).rbp as u32) as u64); (R).rax};let _ = {(R).rbp = M.read64((((R).rsp).wrapping_add(64_u64))); (R).rbp};let _ = {(R).rbx = M.read64((((R).rsp).wrapping_add(56_u64))); (R).rbx};let _ = {(R).rsi = M.read64((((R).rsp).wrapping_add(72_u64))); (R).rsi};let _ = {(R).r15 = M.read64((R).rsp); (R).r15};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r14 = M.read64((R).rsp); (R).r14};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r13 = M.read64((R).rsp); (R).r13};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r12 = M.read64((R).rsp); (R).r12};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).rdi = M.read64((R).rsp); (R).rdi};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};return ((R).rax as *mut u16);
}
pub(super) unsafe fn EdgeWalker8Exact(mut state: *mut RenderState, mut x: i32, mut y: i32, mut dir1: i32, mut dir2: u32, mut out_x: *mut i32, mut out_y: *mut i32, mut threshold: i32) -> *mut u8 {
let mut R: Regs = Regs::default();
let mut M: Memory = Memory::default();
let mut T: u64 = 0;
let mut args: [u64; 4] = [0; 4];
let mut i: u64 = 0;
'b420: {
'b412: {
'b411: {
'b419: {
'b426: {
'b425: {
'b434: {
'b433: {
'b1010: {
'b1004: {
'b439: {
'b998: {
'b1003: {
'b1009: {
'b1117: {
'b1111: {
'b1088: {
'b1067: {
'b1046: {
'b1023: {
'b1022: {
'b1045: {
'b1066: {
'b1087: {
'b1110: {
'b1116: {
'b1133: {
'b1132: {
'b1149: {
'b1148: {
'b1208: {
'b1192: {
'b1186: {
'b1179: {
'b1172: {
'b1165: {
'b1158: {
'b1157: {
'b1164: {
'b1171: {
'b1178: {
'b1185: {
'b1191: {
'b1207: {
'b1251: {
'b1246: {
'b1240: {
'b1235: {
'b1234: {
'b1239: {
'b1245: {
'b1250: {
'b1284: {
'b1279: {
'b1273: {
'b1268: {
'b1267: {
'b1272: {
'b1278: {
'b1283: {
'b1: {
'b1350: {
R = Regs::default();M = Memory::default();T = (0_i32 as u64);let _ = {(M).state = state; (M).state};let _ = {(M).world = (*state).src_world; (M).world};let _ = {(R).rcx = (state as u64); (R).rcx};let _ = {(R).rdx = ((x as u32) as u64); (R).rdx};let _ = {(R).r8 = ((y as u32) as u64); (R).r8};let _ = {(R).r9 = ((dir1 as u32) as u64); (R).r9};let _ = {(R).rsp = (KSTACK).wrapping_add((2048_i32 as u64)); (R).rsp};let _ = M.write64((R).rsp,16045690984833335023_u64);args = [(dir2 as u64), (out_x as u64), (out_y as u64), ((threshold as u32) as u64)];i = (0_i32 as u64);
if (i < ((std::mem::size_of::<[u64; 4]>() as u64) / (std::mem::size_of::<u64>() as u64))) { break 'b1350; } else { break 'b1; }
}
'l1350: loop {
let _ = M.write64((((R).rsp).wrapping_add((40_i32 as u64))).wrapping_add((i).wrapping_mul((8_i32 as u64))),(*((args).as_mut_ptr() as *mut u64).wrapping_offset(i as isize)));let _ = {let old=i; i=(i).wrapping_add(1); i};
if (i < ((std::mem::size_of::<[u64; 4]>() as u64) / (std::mem::size_of::<u64>() as u64))) { continue 'l1350; } else { break 'b1; }
}
}
let _ = M.write64((((R).rsp).wrapping_add(16_u64)),(R).rbx);let _ = M.write64((((R).rsp).wrapping_add(24_u64)),(R).rbp);let _ = M.write64((((R).rsp).wrapping_add(32_u64)),(R).rsi);let _ = M.write64((((R).rsp).wrapping_add(8_u64)),(R).rcx);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).rdi);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).r12);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).r13);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).r14);let _ = {(R).rsp = (((R).rsp).wrapping_sub((8_i32 as u64))) as u64; (R).rsp};let _ = M.write64((R).rsp,(R).r15);let _ = {(R).r15 = M.read64((((R).rsp).wrapping_add(88_u64))); (R).r15};let _ = {(R).r11 = (((6442491481_i64 as u64)).wrapping_sub(40537_u64)); (R).r11};let _ = {(R).r12 = M.read64((((R).rsp).wrapping_add(96_u64))); (R).r12};let _ = {T = (((((R).r14 as u32)) ^ (((R).r14 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).r14 = ((T as u32) as u64); (R).r14};let _ = {(R).rbx = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).rbx};let _ = {(R).r10 = (((((R).rdx as u32) as i32) as i64) as u64); (R).r10};let _ = {(R).rax = (((((R).r9 as u32) as i32) as i64) as u64); (R).rax};let _ = {(R).r9 = ((((R).rax).wrapping_mul(4_u64))); (R).r9};let _ = {(R).rbp = (M.read32(((((R).r9).wrapping_add((R).r11)).wrapping_add(61640_u64))) as u64); (R).rbp};let _ = {(R).rsi = (M.read32(((((R).r9).wrapping_add((R).r11)).wrapping_add(61680_u64))) as u64); (R).rsi};let _ = {T = M.addflags((((R).rbp as u32) as u64),(((R).r10 as u32) as u64),32_i32); T};let _ = {(R).rbp = ((T as u32) as u64); (R).rbp};let _ = M.write32(((R).r15),((R).r10 as u32));let _ = {T = M.addflags((((R).rsi as u32) as u64),(((R).r8 as u32) as u64),32_i32); T};let _ = {(R).rsi = ((T as u32) as u64); (R).rsi};let _ = M.write32(((R).r12),((R).r8 as u32));let _ = {(R).r9 = (((R).r14 as u32) as u64); (R).r9};let _ = {(R).rdx = M.read64((((R).rcx).wrapping_add(16_u64))); (R).rdx};let _ = {T = (((((R).r10 as u32)) & (((R).r10 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1284; } else { break 'b1283; }
}
let _ = {T = M.subflags((((R).r10 as u32) as u64),(M.read32((((R).rdx).wrapping_add(36_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b1279; } else { break 'b1278; }
}
let _ = {T = (((((R).r8 as u32)) & (((R).r8 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1273; } else { break 'b1272; }
}
let _ = {T = M.subflags((((R).r8 as u32) as u64),(M.read32((((R).rdx).wrapping_add(40_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b1268; } else { break 'b1267; }
}
let _ = {(R).r8 = (((((((R).r8 as u32) as i32) as i64)).wrapping_mul(((M.read32((((R).rdx).wrapping_add(32_u64))) as i32) as i64)) as u32) as u64); (R).r8};let _ = {(R).rcx = (((((R).r8 as u32) as i32) as i64) as u64); (R).rcx};let _ = {(R).r9 = (((R).rcx).wrapping_add((((R).r10).wrapping_mul(4_u64)))); (R).r9};let _ = {T = M.addflags((R).r9,M.read64((((R).rdx).wrapping_add(24_u64))),64_i32); T};let _ = {(R).r9 = T; (R).r9};let _ = {(R).r10 = (R).r14; (R).r10};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1251; } else { break 'b1250; }
}
let _ = {(R).r10 = (R).r14; (R).r10};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1251; } else { break 'b1250; }
}
let _ = {(R).r10 = (R).r14; (R).r10};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1251; } else { break 'b1250; }
}
let _ = {(R).r10 = (R).r14; (R).r10};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1251; } else { break 'b1250; }
}
let _ = {(R).r10 = (R).r14; (R).r10};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1251; } else { break 'b1250; }
}
let _ = {T = M.subflags((((R).rbp as u32) as u64),(M.read32((((R).rdx).wrapping_add(36_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b1246; } else { break 'b1245; }
}
let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b1240; } else { break 'b1239; }
}
let _ = {T = M.subflags((((R).rsi as u32) as u64),(M.read32((((R).rdx).wrapping_add(40_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b1235; } else { break 'b1234; }
}
let _ = {(R).rax = (((R).rsi as u32) as u64); (R).rax};let _ = {(R).rax = (((((((R).rax as u32) as i32) as i64)).wrapping_mul(((M.read32((((R).rdx).wrapping_add(32_u64))) as i32) as i64)) as u32) as u64); (R).rax};let _ = {(R).rcx = (((((R).rax as u32) as i32) as i64) as u64); (R).rcx};let _ = {(R).rax = (((((R).rbp as u32) as i32) as i64) as u64); (R).rax};let _ = {(R).r10 = (((R).rcx).wrapping_add((((R).rax).wrapping_mul(4_u64)))); (R).r10};let _ = {T = M.addflags((R).r10,M.read64((((R).rdx).wrapping_add(24_u64))),64_i32); T};let _ = {(R).r10 = T; (R).r10};let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).r8 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).r8};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).r8 as u32));let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1208; } else { break 'b1207; }
}
let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).r8 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).r8};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).r8 as u32));let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1208; } else { break 'b1207; }
}
let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).r8 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).r8};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).r8 as u32));let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1208; } else { break 'b1207; }
}
let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).r8 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).r8};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).r8 as u32));let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1208; } else { break 'b1207; }
}
let _ = {(R).rax = (((M.read32((((R).rsp).wrapping_add(80_u64))) as i32) as i64) as u64); (R).rax};let _ = {(R).r8 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61680_u64))) as u64); (R).r8};let _ = {(R).r13 = (M.read32(((((R).r11).wrapping_add((((R).rax).wrapping_mul(4_u64)))).wrapping_add(61640_u64))) as u64); (R).r13};let _ = M.write32((((R).rsp).wrapping_add(104_u64)),((R).r8 as u32));let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b1208; } else { break 'b1207; }
}
let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | ((((!(M).zf) as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | ((((!(M).zf) as u8)) as u64)); (R).r11};let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1192; } else { break 'b1191; }
}
let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1186; } else { break 'b1185; }
}
let _ = {(R).rax = ((M.read8((((R).r10).wrapping_add(1_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r9).wrapping_add(1_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b1179; } else { break 'b1178; }
}
let _ = {(R).rax = ((M.read8((((R).r10).wrapping_add(3_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r9).wrapping_add(3_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b1172; } else { break 'b1171; }
}
let _ = {(R).rax = ((M.read8((((R).r10).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r9).wrapping_add(2_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b1165; } else { break 'b1164; }
}
let _ = {(R).rax = ((M.read8(((R).r10)) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8(((R).r9)) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b1158; } else { break 'b1157; }
}
let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1149; } else { break 'b1148; }
}
let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | ((((!(M).sf) as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1133; } else { break 'b1132; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1133; } else { break 'b1132; }
}
let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | ((((!(M).sf) as u8)) as u64)); (R).r11};let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1117; } else { break 'b1116; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1117; } else { break 'b1116; }
}
let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b1111; } else { break 'b1110; }
}
let _ = {(R).rax = ((M.read8((((R).r10).wrapping_add(1_u64))) as u32) as u64); (R).rax};let _ = {(R).rcx = ((M.read8((((R).r9).wrapping_add(1_u64))) as u32) as u64); (R).rcx};let _ = {T = M.subflags((((R).rcx as u32) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = {(R).rcx = ((T as u32) as u64); (R).rcx};let _ = {(R).rax = (((R).rcx as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b1088; } else { break 'b1087; }
}
let _ = {(R).rcx = ((M.read8((((R).r10).wrapping_add(3_u64))) as u32) as u64); (R).rcx};let _ = {(R).rax = ((M.read8((((R).r9).wrapping_add(3_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rcx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b1067; } else { break 'b1066; }
}
let _ = {(R).rcx = ((M.read8((((R).r10).wrapping_add(2_u64))) as u32) as u64); (R).rcx};let _ = {(R).rax = ((M.read8((((R).r9).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rcx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b1046; } else { break 'b1045; }
}
let _ = {(R).rax = ((M.read8(((R).r10)) as u32) as u64); (R).rax};let _ = {(R).rcx = ((M.read8(((R).r9)) as u32) as u64); (R).rcx};let _ = {T = M.subflags((((R).rcx as u32) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = {(R).rcx = ((T as u32) as u64); (R).rcx};let _ = {(R).rax = (((R).rcx as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b1023; } else { break 'b1022; }
}
let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1010; } else { break 'b1009; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1004; } else { break 'b1003; }
}
'l1003: loop {
'b440: {
'b549: {
'b543: {
'b522: {
'b501: {
'b480: {
'b459: {
'b458: {
'b479: {
'b500: {
'b521: {
'b542: {
'b548: {
'b654: {
'b648: {
'b627: {
'b606: {
'b585: {
'b562: {
'b561: {
'b584: {
'b605: {
'b626: {
'b647: {
'b653: {
'b759: {
'b753: {
'b732: {
'b711: {
'b690: {
'b667: {
'b666: {
'b689: {
'b710: {
'b731: {
'b752: {
'b758: {
'b902: {
'b802: {
'b796: {
'b789: {
'b782: {
'b775: {
'b768: {
'b767: {
'b774: {
'b781: {
'b788: {
'b795: {
'b801: {
'b849: {
'b843: {
'b836: {
'b829: {
'b822: {
'b815: {
'b814: {
'b821: {
'b828: {
'b835: {
'b842: {
'b848: {
'b896: {
'b890: {
'b883: {
'b876: {
'b869: {
'b862: {
'b861: {
'b868: {
'b875: {
'b882: {
'b889: {
'b895: {
'b901: {
'b937: {
'b932: {
'b926: {
'b921: {
'b920: {
'b925: {
'b931: {
'b936: {
'b970: {
'b965: {
'b959: {
'b954: {
'b953: {
'b958: {
'b964: {
'b969: {
'b997: {
let _ = {T = ((((((R).rax as u8)) as i32) & ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b998; } else { break 'b997; }
}
let _ = {T = M.addflags((M.read32(((R).r15)) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = M.write32(((R).r15),(T as u32));let _ = {T = M.addflags((((R).rsi as u32) as u64),(((R).r8 as u32) as u64),32_i32); T};let _ = {(R).rsi = ((T as u32) as u64); (R).rsi};let _ = {T = M.addflags((M.read32(((R).r12)) as u64),(((R).r8 as u32) as u64),32_i32); T};let _ = M.write32(((R).r12),(T as u32));let _ = {T = M.addflags((((R).rbp as u32) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = {(R).rbp = ((T as u32) as u64); (R).rbp};let _ = {(R).rcx = M.read64((((R).rsp).wrapping_add(48_u64))); (R).rcx};let _ = {(R).r8 = (R).r14; (R).r8};let _ = {(R).r11 = (((M.read32(((R).r15)) as i32) as i64) as u64); (R).r11};let _ = {(R).rax = (M.read32(((R).r12)) as u64); (R).rax};let _ = {(R).rdx = M.read64((((R).rcx).wrapping_add(16_u64))); (R).rdx};let _ = {T = (((((R).r11 as u32)) & (((R).r11 as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b970; } else { break 'b969; }
}
let _ = {T = M.subflags((((R).r11 as u32) as u64),(M.read32((((R).rdx).wrapping_add(36_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b965; } else { break 'b964; }
}
let _ = {T = (((((R).rax as u32)) & (((R).rax as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b959; } else { break 'b958; }
}
let _ = {T = M.subflags((((R).rax as u32) as u64),(M.read32((((R).rdx).wrapping_add(40_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b954; } else { break 'b953; }
}
let _ = {(R).rax = (((((((R).rax as u32) as i32) as i64)).wrapping_mul(((M.read32((((R).rdx).wrapping_add(32_u64))) as i32) as i64)) as u32) as u64); (R).rax};let _ = {(R).rcx = (((((R).rax as u32) as i32) as i64) as u64); (R).rcx};let _ = {(R).r8 = (((R).rcx).wrapping_add((((R).r11).wrapping_mul(4_u64)))); (R).r8};let _ = {T = M.addflags((R).r8,M.read64((((R).rdx).wrapping_add(24_u64))),64_i32); T};let _ = {(R).r8 = T; (R).r8};let _ = {(R).rcx = (R).r14; (R).rcx};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b937; } else { break 'b936; }
}
let _ = {(R).rcx = (R).r14; (R).rcx};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b937; } else { break 'b936; }
}
let _ = {(R).rcx = (R).r14; (R).rcx};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b937; } else { break 'b936; }
}
let _ = {(R).rcx = (R).r14; (R).rcx};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b937; } else { break 'b936; }
}
let _ = {(R).rcx = (R).r14; (R).rcx};let _ = {T = (((((R).rbp as u32)) & (((R).rbp as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b937; } else { break 'b936; }
}
let _ = {T = M.subflags((((R).rbp as u32) as u64),(M.read32((((R).rdx).wrapping_add(36_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b932; } else { break 'b931; }
}
let _ = {T = (((((R).rsi as u32)) & (((R).rsi as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (M).sf { break 'b926; } else { break 'b925; }
}
let _ = {T = M.subflags((((R).rsi as u32) as u64),(M.read32((((R).rdx).wrapping_add(40_u64))) as u64),32_i32); T};
if (((M).sf as i32) == ((M).of as i32)) { break 'b921; } else { break 'b920; }
}
let _ = {(R).rax = (((R).rsi as u32) as u64); (R).rax};let _ = {(R).rax = (((((((R).rax as u32) as i32) as i64)).wrapping_mul(((M.read32((((R).rdx).wrapping_add(32_u64))) as i32) as i64)) as u32) as u64); (R).rax};let _ = {(R).rcx = (((((R).rax as u32) as i32) as i64) as u64); (R).rcx};let _ = {(R).rax = (((((R).rbp as u32) as i32) as i64) as u64); (R).rax};let _ = {(R).rcx = (((R).rcx).wrapping_add((((R).rax).wrapping_mul(4_u64)))); (R).rcx};let _ = {T = M.addflags((R).rcx,M.read64((((R).rdx).wrapping_add(24_u64))),64_i32); T};let _ = {(R).rcx = T; (R).rcx};let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b902; } else { break 'b901; }
}
let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b902; } else { break 'b901; }
}
let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b902; } else { break 'b901; }
}
let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b902; } else { break 'b901; }
}
let _ = {T = (((((R).rbx as u32)) & (((R).rbx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);
if (!(M).zf) { break 'b902; } else { break 'b901; }
}
let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b896; } else { break 'b895; }
}
let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b890; } else { break 'b889; }
}
let _ = {(R).rax = ((M.read8((((R).r8).wrapping_add(1_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r9).wrapping_add(1_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b883; } else { break 'b882; }
}
let _ = {(R).rax = ((M.read8((((R).r8).wrapping_add(3_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r9).wrapping_add(3_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b876; } else { break 'b875; }
}
let _ = {(R).rax = ((M.read8((((R).r8).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r9).wrapping_add(2_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b869; } else { break 'b868; }
}
let _ = {(R).rax = ((M.read8(((R).r8)) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8(((R).r9)) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b862; } else { break 'b861; }
}
let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b849; } else { break 'b848; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b849; } else { break 'b848; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b849; } else { break 'b848; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b849; } else { break 'b848; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b849; } else { break 'b848; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b849; } else { break 'b848; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b849; } else { break 'b848; }
}
let _ = {T = (((R).rcx) & ((R).rcx)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b843; } else { break 'b842; }
}
let _ = {(R).rax = ((M.read8((((R).rcx).wrapping_add(1_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r10).wrapping_add(1_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b836; } else { break 'b835; }
}
let _ = {(R).rax = ((M.read8((((R).rcx).wrapping_add(3_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r10).wrapping_add(3_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b829; } else { break 'b828; }
}
let _ = {(R).rax = ((M.read8((((R).rcx).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r10).wrapping_add(2_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b822; } else { break 'b821; }
}
let _ = {(R).rax = ((M.read8(((R).rcx)) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8(((R).r10)) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b815; } else { break 'b814; }
}
let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b802; } else { break 'b801; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b802; } else { break 'b801; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b802; } else { break 'b801; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b802; } else { break 'b801; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b802; } else { break 'b801; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b802; } else { break 'b801; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b802; } else { break 'b801; }
}
let _ = {T = (((R).rcx) & ((R).rcx)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b796; } else { break 'b795; }
}
let _ = {(R).rax = ((M.read8((((R).rcx).wrapping_add(1_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r8).wrapping_add(1_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b789; } else { break 'b788; }
}
let _ = {(R).rax = ((M.read8((((R).rcx).wrapping_add(3_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r8).wrapping_add(3_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b782; } else { break 'b781; }
}
let _ = {(R).rax = ((M.read8((((R).rcx).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8((((R).r8).wrapping_add(2_u64))) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b775; } else { break 'b774; }
}
let _ = {(R).rax = ((M.read8(((R).rcx)) as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read8(((R).r8)) as u64),(((R).rax as u8) as u64),8_i32); T};
if (!(M).zf) { break 'b768; } else { break 'b767; }
}
let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = (((R).r9) & ((R).r9)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b759; } else { break 'b758; }
}
let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b753; } else { break 'b752; }
}
let _ = {(R).rdx = ((M.read8((((R).r8).wrapping_add(1_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r9).wrapping_add(1_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b732; } else { break 'b731; }
}
let _ = {(R).rdx = ((M.read8((((R).r8).wrapping_add(3_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r9).wrapping_add(3_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b711; } else { break 'b710; }
}
let _ = {(R).rdx = ((M.read8((((R).r8).wrapping_add(2_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r9).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b690; } else { break 'b689; }
}
let _ = {(R).rax = ((M.read8(((R).r8)) as u32) as u64); (R).rax};let _ = {(R).rdx = ((M.read8(((R).r9)) as u32) as u64); (R).rdx};let _ = {T = M.subflags((((R).rdx as u32) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = {(R).rdx = ((T as u32) as u64); (R).rdx};let _ = {(R).rax = (((R).rdx as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b667; } else { break 'b666; }
}
let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b654; } else { break 'b653; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b654; } else { break 'b653; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b654; } else { break 'b653; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b654; } else { break 'b653; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b654; } else { break 'b653; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b654; } else { break 'b653; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) ^ ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rdi = ((((R).rdi & (!255_u64))) | (((T as u8)) as u64)); (R).rdi};let _ = {T = (((R).r10) & ((R).r10)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b654; } else { break 'b653; }
}
let _ = {T = (((R).rcx) & ((R).rcx)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b648; } else { break 'b647; }
}
let _ = {(R).rdx = ((M.read8((((R).rcx).wrapping_add(1_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r10).wrapping_add(1_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b627; } else { break 'b626; }
}
let _ = {(R).rdx = ((M.read8((((R).rcx).wrapping_add(3_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r10).wrapping_add(3_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b606; } else { break 'b605; }
}
let _ = {(R).rdx = ((M.read8((((R).rcx).wrapping_add(2_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r10).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b585; } else { break 'b584; }
}
let _ = {(R).rax = ((M.read8(((R).rcx)) as u32) as u64); (R).rax};let _ = {(R).rdx = ((M.read8(((R).r10)) as u32) as u64); (R).rdx};let _ = {T = M.subflags((((R).rdx as u32) as u64),(((R).rax as u32) as u64),32_i32); T};let _ = {(R).rdx = ((T as u32) as u64); (R).rdx};let _ = {(R).rax = (((R).rdx as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b562; } else { break 'b561; }
}
let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b549; } else { break 'b548; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b549; } else { break 'b548; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b549; } else { break 'b548; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b549; } else { break 'b548; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b549; } else { break 'b548; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b549; } else { break 'b548; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) ^ ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).r11 = ((((R).r11 & (!255_u64))) | (((T as u8)) as u64)); (R).r11};let _ = {T = (((R).r8) & ((R).r8)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b549; } else { break 'b548; }
}
let _ = {T = (((R).rcx) & ((R).rcx)); T};let _ = M.logicflags(T,64_i32);
if (M).zf { break 'b543; } else { break 'b542; }
}
let _ = {(R).rdx = ((M.read8((((R).rcx).wrapping_add(1_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r8).wrapping_add(1_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b522; } else { break 'b521; }
}
let _ = {(R).rdx = ((M.read8((((R).rcx).wrapping_add(3_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r8).wrapping_add(3_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b501; } else { break 'b500; }
}
let _ = {(R).rdx = ((M.read8((((R).rcx).wrapping_add(2_u64))) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8((((R).r8).wrapping_add(2_u64))) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b480; } else { break 'b479; }
}
let _ = {(R).rdx = ((M.read8(((R).rcx)) as u32) as u64); (R).rdx};let _ = {(R).rax = ((M.read8(((R).r8)) as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {(R).rdx = ((if (((((R).rax as u32) & 2147483648_u32)) != 0) { 4294967295_u32 } else { 0_u32 }) as u64); (R).rdx};let _ = {T = (((((R).rax as u32)) ^ (((R).rdx as u32))) as u64); T};let _ = M.logicflags(T,32_i32);let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rdx as u32) as u64),32_i32); T};let _ = {(R).rax = ((T as u32) as u64); (R).rax};let _ = {T = M.subflags((((R).rax as u32) as u64),(((R).rbx as u32) as u64),32_i32); T};
if ((!(M).zf) && ((((M).sf as i32) == ((M).of as i32)))) { break 'b459; } else { break 'b458; }
}
let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((1_u64 as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).rax as u8)) as i32) ^ ((((R).rax as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((((R).rax & (!255_u64))) | (((T as u8)) as u64)); (R).rax};let _ = {(R).r9 = (R).r8; (R).r9};let _ = {(R).r8 = (M.read32((((R).rsp).wrapping_add(104_u64))) as u64); (R).r8};let _ = {(R).r10 = (R).rcx; (R).r10};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b440; } else { break 'b439; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b1004; } else { continue 'l1003; }
}
}
let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b434; } else { break 'b433; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b434; } else { break 'b433; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b434; } else { break 'b433; }
}

if (!(M).zf) { break 'b434; } else { break 'b433; }
}
let _ = {(R).rax = ((1_u64 as u32) as u64); (R).rax};let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b426; } else { break 'b425; }
}
let _ = {(R).r14 = (M.read32((((R).rsp).wrapping_add(80_u64))) as u64); (R).r14};let _ = {(R).rax = ((1_u64 as u32) as u64); (R).rax};let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (M).zf { break 'b426; } else { break 'b425; }
}
let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b420; } else { break 'b419; }
}
let _ = {(R).r14 = (((R).rax as u32) as u64); (R).r14};let _ = {T = ((((((R).rdi as u8)) as i32) & ((((R).rdi as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);
if (!(M).zf) { break 'b420; } else { break 'b419; }
}
let _ = {T = ((((((R).r11 as u8)) as i32) & ((((R).r11 as u8)) as i32)) as u64); T};let _ = M.logicflags(T,8_i32);let _ = {(R).rax = ((2_u64 as u32) as u64); (R).rax};
if (M).zf { break 'b412; } else { break 'b411; }
}
let _ = {T = M.subflags((M.read32(((R).r15)) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = M.write32(((R).r15),(T as u32));let _ = {(R).rax = (((R).r14 as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read32(((R).r12)) as u64),(((R).r8 as u32) as u64),32_i32); T};let _ = M.write32(((R).r12),(T as u32));let _ = {(R).rbx = M.read64((((R).rsp).wrapping_add(56_u64))); (R).rbx};let _ = {(R).rbp = M.read64((((R).rsp).wrapping_add(64_u64))); (R).rbp};let _ = {(R).rsi = M.read64((((R).rsp).wrapping_add(72_u64))); (R).rsi};let _ = {(R).r15 = M.read64((R).rsp); (R).r15};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r14 = M.read64((R).rsp); (R).r14};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r13 = M.read64((R).rsp); (R).r13};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r12 = M.read64((R).rsp); (R).r12};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).rdi = M.read64((R).rsp); (R).rdi};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};return ((R).rax as *mut u8);
}
let _ = {(R).r14 = (((R).rax as u32) as u64); (R).r14};let _ = {T = M.subflags((M.read32(((R).r15)) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = M.write32(((R).r15),(T as u32));let _ = {(R).rax = (((R).r14 as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read32(((R).r12)) as u64),(((R).r8 as u32) as u64),32_i32); T};let _ = M.write32(((R).r12),(T as u32));let _ = {(R).rbx = M.read64((((R).rsp).wrapping_add(56_u64))); (R).rbx};let _ = {(R).rbp = M.read64((((R).rsp).wrapping_add(64_u64))); (R).rbp};let _ = {(R).rsi = M.read64((((R).rsp).wrapping_add(72_u64))); (R).rsi};let _ = {(R).r15 = M.read64((R).rsp); (R).r15};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r14 = M.read64((R).rsp); (R).r14};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r13 = M.read64((R).rsp); (R).r13};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r12 = M.read64((R).rsp); (R).r12};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).rdi = M.read64((R).rsp); (R).rdi};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};return ((R).rax as *mut u8);
}
let _ = {T = M.subflags((M.read32(((R).r15)) as u64),(((R).r13 as u32) as u64),32_i32); T};let _ = M.write32(((R).r15),(T as u32));let _ = {(R).rax = (((R).r14 as u32) as u64); (R).rax};let _ = {T = M.subflags((M.read32(((R).r12)) as u64),(((R).r8 as u32) as u64),32_i32); T};let _ = M.write32(((R).r12),(T as u32));let _ = {(R).rbx = M.read64((((R).rsp).wrapping_add(56_u64))); (R).rbx};let _ = {(R).rbp = M.read64((((R).rsp).wrapping_add(64_u64))); (R).rbp};let _ = {(R).rsi = M.read64((((R).rsp).wrapping_add(72_u64))); (R).rsi};let _ = {(R).r15 = M.read64((R).rsp); (R).r15};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r14 = M.read64((R).rsp); (R).r14};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r13 = M.read64((R).rsp); (R).r13};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).r12 = M.read64((R).rsp); (R).r12};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};let _ = {(R).rdi = M.read64((R).rsp); (R).rdi};let _ = {(R).rsp = (((R).rsp).wrapping_add((8_i32 as u64))) as u64; (R).rsp};return ((R).rax as *mut u8);
}
pub(super) unsafe fn InterpExecutor16(mut state: *mut RenderState, mut param_2: i32, mut param_3: i32, mut param_4: i32, mut param_5: *mut u16, mut param_6: i32, mut param_7: i32, mut param_8: *mut u16, mut evaluator: *mut Eval, mut param_10: i8, mut param_11: i32) -> () {
let mut iVar7: i32 = 0;
let mut cVar6: i8 = 0;
let mut fVar4: f32 = 0.0;
let mut fVar3: f32 = 0.0;
let mut local_68: [u16; 4] = [0; 4];
let mut param_5_arr: [u16; 4] = [0; 4];
let mut param_8_arr: [u16; 4] = [0; 4];
let mut uVar14: u32 = 0;
let mut iVar16: i32 = 0;
let mut iVar12: i32 = 0;
let mut dx_step: i32 = 0;
let mut dy_step: i32 = 0;
let mut iVar12_loop: i32 = 0;
let mut t: f32 = 0.0;
let mut fVar19: f32 = 0.0;
let mut fVar2: f32 = 0.0;
let mut puVar17: *mut u16 = std::ptr::null_mut();
let mut ppuVar15: *mut u16 = std::ptr::null_mut();
let mut src: *mut World = std::ptr::null_mut();
let mut dst: *mut World = std::ptr::null_mut();
let mut uVar8: u16 = 0;
let mut uVar9: u16 = 0;
let mut uVar10: u16 = 0;
let mut uVar11: u16 = 0;
let mut dst_eq_src: bool = false;
'b1: {
'b53: {
'b56: {
'b55: {
iVar7 = param_11;cVar6 = param_10;fVar4 = DAT_18000d1f4;fVar3 = DAT_18000d1f0;let _ = {(*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize)) = (*(param_5).wrapping_offset(0_i32 as isize)); (*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize))};let _ = {(*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize)) = (*(param_5).wrapping_offset(1_i32 as isize)); (*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize))};let _ = {(*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize)) = (*(param_5).wrapping_offset(2_i32 as isize)); (*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize))};let _ = {(*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize)) = (*(param_5).wrapping_offset(3_i32 as isize)); (*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize)) = (*(param_8).wrapping_offset(0_i32 as isize)); (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize)) = (*(param_8).wrapping_offset(1_i32 as isize)); (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize)) = (*(param_8).wrapping_offset(2_i32 as isize)); (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize)) = (*(param_8).wrapping_offset(3_i32 as isize)); (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize))};let _ = {uVar14 = (((((param_4).wrapping_sub(param_7))).wrapping_shr(31_i32 as u32)) as u32); uVar14};iVar16 = (((((param_4).wrapping_sub(param_7)) ^ (uVar14 as i32)))).wrapping_sub((uVar14 as i32));let _ = {uVar14 = (((((param_3).wrapping_sub(param_6))).wrapping_shr(31_i32 as u32)) as u32); uVar14};iVar12 = (((((param_3).wrapping_sub(param_6)) ^ (uVar14 as i32)))).wrapping_sub((uVar14 as i32));dx_step = (*((DAT_18000f0c8).as_ptr() as *mut i32).wrapping_offset((param_2 as i64) as isize));dy_step = (*((DAT_18000f0f0).as_ptr() as *mut i32).wrapping_offset((param_2 as i64) as isize));
if (iVar16 < iVar12) { break 'b56; } else { break 'b55; }
}
iVar12_loop = 0_i32;
if ((1_i32).wrapping_neg() < iVar16) { break 'b53; } else { break 'b1; }
}
let _ = {iVar16 = iVar12; iVar16};iVar12_loop = 0_i32;
if ((1_i32).wrapping_neg() < iVar16) { break 'b53; } else { break 'b1; }
}
'l53: loop {
'b7: {
'b8: {
'b11: {
'b10: {
'b24: {
'b16: {
'b29: {
'b35: {
'b34: {
'b37: {
'b39: {
'b38: {
'b44: {
'b43: {
'b47: {
'b46: {
'b51: {
'b52: {

if (iVar16 > 0_i32) { break 'b51; } else { break 'b52; }
}
let _ = {t = 0.0_f32; t};fVar19 = (*evaluator).evaluate(t);fVar2 = fVar4;
if (fVar19 <= fVar4) { break 'b47; } else { break 'b46; }
}
let _ = {t = ((iVar12_loop as f32) / (iVar16 as f32)); t};fVar19 = (*evaluator).evaluate(t);fVar2 = fVar4;
if (fVar19 <= fVar4) { break 'b47; } else { break 'b46; }
}
let _ = {fVar19 = 0.0_f32; fVar19};
if (0.0_f32 <= fVar2) { break 'b44; } else { break 'b43; }
}
let _ = {fVar2 = fVar19; fVar2};let _ = {fVar19 = 0.0_f32; fVar19};
if (0.0_f32 <= fVar2) { break 'b44; } else { break 'b43; }
}
puVar17 = (std::ptr::null_mut::<u8>() as *mut u16);ppuVar15 = (std::ptr::null_mut::<u8>() as *mut u16);src = (*state).src_world;
if (!((((((param_3 < 0_i32)) || (((*src).width <= param_3))) || ((param_4 < 0_i32))) || (((*src).height <= param_4))))) { break 'b39; } else { break 'b38; }
}
let _ = {fVar19 = fVar2; fVar19};puVar17 = (std::ptr::null_mut::<u8>() as *mut u16);ppuVar15 = (std::ptr::null_mut::<u8>() as *mut u16);src = (*state).src_world;
if (!((((((param_3 < 0_i32)) || (((*src).width <= param_3))) || ((param_4 < 0_i32))) || (((*src).height <= param_4))))) { break 'b39; } else { break 'b38; }
}

if ((puVar17 != (std::ptr::null_mut::<u8>() as *mut u16)) || (param_3 >= 0_i32)) { break 'b37; } else { break 'b34; }
}
let _ = {puVar17 = ((((((*src).data as *mut u8)).wrapping_offset(((((param_4).wrapping_mul((*src).rowbytes)) as i64) as isize))).wrapping_offset((((param_3 as i64)).wrapping_mul((8_i32 as i64)) as isize))) as *mut u16); puVar17};
if ((puVar17 != (std::ptr::null_mut::<u8>() as *mut u16)) || (param_3 >= 0_i32)) { break 'b37; } else { break 'b34; }
}
dst = (*state).dst_world;
if ((((param_3 < (*dst).width)) && (((1_i32).wrapping_neg() < param_4))) && ((param_4 < (*dst).height))) { break 'b35; } else { break 'b34; }
}
uVar8 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize));uVar9 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize));uVar10 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize));uVar11 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize));
if (((cVar6 as i32) != (0_i8 as i32)) && (puVar17 != (std::ptr::null_mut::<u8>() as *mut u16))) { break 'b29; } else { break 'b16; }
}
let _ = {ppuVar15 = ((((((*dst).data as *mut u8)).wrapping_offset(((((param_4).wrapping_mul((*dst).rowbytes)) as i64) as isize))).wrapping_offset((((param_3 as i64)).wrapping_mul((8_i32 as i64)) as isize))) as *mut u16); ppuVar15};uVar8 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize));uVar9 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize));uVar10 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize));uVar11 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize));
if (((cVar6 as i32) != (0_i8 as i32)) && (puVar17 != (std::ptr::null_mut::<u8>() as *mut u16))) { break 'b29; } else { break 'b16; }
}
let _ = {uVar8 = (*(puVar17).wrapping_offset(0_i32 as isize)); uVar8};let _ = {uVar9 = (*(puVar17).wrapping_offset(1_i32 as isize)); uVar9};let _ = {uVar10 = (*(puVar17).wrapping_offset(2_i32 as isize)); uVar10};let _ = {uVar11 = (*(puVar17).wrapping_offset(3_i32 as isize)); uVar11};
if (iVar12_loop <= iVar7) { break 'b24; } else { break 'b16; }
}
let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize)) = uVar8; (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize)) = uVar9; (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize)) = uVar10; (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize)) = uVar11; (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize))};
if (((fVar4 < fVar19)) || ((fVar19 < 0.0_f32))) { break 'b11; } else { break 'b10; }
}
let _ = {uVar8 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize)); uVar8};let _ = {uVar9 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize)); uVar9};let _ = {uVar10 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize)); uVar10};let _ = {uVar11 = (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize)); uVar11};let _ = {(*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize)) = (*(puVar17).wrapping_offset(0_i32 as isize)); (*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize))};let _ = {(*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize)) = (*(puVar17).wrapping_offset(1_i32 as isize)); (*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize))};let _ = {(*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize)) = (*(puVar17).wrapping_offset(2_i32 as isize)); (*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize))};let _ = {(*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize)) = (*(puVar17).wrapping_offset(3_i32 as isize)); (*((local_68).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize)) = uVar8; (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(0_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize)) = uVar9; (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(1_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize)) = uVar10; (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(2_i32 as isize))};let _ = {(*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize)) = uVar11; (*((param_5_arr).as_mut_ptr() as *mut u16).wrapping_offset(3_i32 as isize))};
if (((fVar4 < fVar19)) || ((fVar19 < 0.0_f32))) { break 'b11; } else { break 'b10; }
}
dst_eq_src = (((((((ppuVar15 != (std::ptr::null_mut::<u8>() as *mut u16)) && (puVar17 != (std::ptr::null_mut::<u8>() as *mut u16))) && (((*(ppuVar15).wrapping_offset(1_i32 as isize)) as i32) == ((*(puVar17).wrapping_offset(1_i32 as isize)) as i32))) && (((*(ppuVar15).wrapping_offset(3_i32 as isize)) as i32) == ((*(puVar17).wrapping_offset(3_i32 as isize)) as i32))) && (((*(ppuVar15).wrapping_offset(2_i32 as isize)) as i32) == ((*(puVar17).wrapping_offset(2_i32 as isize)) as i32))) && (((*(ppuVar15).wrapping_offset(0_i32 as isize)) as i32) == ((*(puVar17).wrapping_offset(0_i32 as isize)) as i32))));
if (!dst_eq_src) { break 'b7; } else { break 'b8; }
}
let _ = {fVar19 = 0.0_f32; fVar19};dst_eq_src = (((((((ppuVar15 != (std::ptr::null_mut::<u8>() as *mut u16)) && (puVar17 != (std::ptr::null_mut::<u8>() as *mut u16))) && (((*(ppuVar15).wrapping_offset(1_i32 as isize)) as i32) == ((*(puVar17).wrapping_offset(1_i32 as isize)) as i32))) && (((*(ppuVar15).wrapping_offset(3_i32 as isize)) as i32) == ((*(puVar17).wrapping_offset(3_i32 as isize)) as i32))) && (((*(ppuVar15).wrapping_offset(2_i32 as isize)) as i32) == ((*(puVar17).wrapping_offset(2_i32 as isize)) as i32))) && (((*(ppuVar15).wrapping_offset(0_i32 as isize)) as i32) == ((*(puVar17).wrapping_offset(0_i32 as isize)) as i32))));
if (!dst_eq_src) { break 'b7; } else { break 'b8; }
}
let _ = AlphaBlend16((local_68).as_mut_ptr() as *mut u16, (fVar4 - fVar19), (param_5_arr).as_mut_ptr() as *mut u16, fVar19, ppuVar15);let _ = {param_3 = ((param_3).wrapping_add(dx_step)) as i32; param_3};let _ = {let old=iVar12_loop; iVar12_loop=(iVar12_loop).wrapping_add(1); old};let _ = {param_4 = ((param_4).wrapping_add(dy_step)) as i32; param_4};
if (iVar12_loop <= iVar16) { continue 'l53; } else { break 'b1; }
}
let _ = AlphaBlend16((local_68).as_mut_ptr() as *mut u16, (fVar4 - fVar19), (param_5_arr).as_mut_ptr() as *mut u16, fVar19, (param_8_arr).as_mut_ptr() as *mut u16);let _ = AlphaBlend16((param_8_arr).as_mut_ptr() as *mut u16, fVar3, (if (ppuVar15 != std::ptr::null_mut()) { ppuVar15 } else { (param_8_arr).as_mut_ptr() as *mut u16 }), fVar3, ppuVar15);let _ = {param_3 = ((param_3).wrapping_add(dx_step)) as i32; param_3};let _ = {let old=iVar12_loop; iVar12_loop=(iVar12_loop).wrapping_add(1); old};let _ = {param_4 = ((param_4).wrapping_add(dy_step)) as i32; param_4};
if (iVar12_loop <= iVar16) { continue 'l53; } else { break 'b1; }
}
}
return ;
}
pub(super) unsafe fn InterpExecutor8(mut state: *mut RenderState, mut param_2: i32, mut param_3: i32, mut param_4: i32, mut param_5: *mut u8, mut param_6: i32, mut param_7: i32, mut param_8: *mut u8, mut evaluator: *mut Eval, mut param_10: i8, mut param_11: i32) -> () {
let mut trace_x: i32 = 0;
let mut trace_y: i32 = 0;
let mut tracing: bool = false;
let mut start_x: i32 = 0;
let mut start_y: i32 = 0;
let mut iVar8: i32 = 0;
let mut cVar7: i8 = 0;
let mut fVar5: f32 = 0.0;
let mut fVar4: f32 = 0.0;
let mut local_res18: [u8; 4] = [0; 4];
let mut local_res10: [u8; 4] = [0; 4];
let mut param_7_arr: [u8; 4] = [0; 4];
let mut uVar14: u32 = 0;
let mut iVar16: i32 = 0;
let mut iVar13: i32 = 0;
let mut iVar1: i32 = 0;
let mut local_res20: i32 = 0;
let mut iVar13_loop: i32 = 0;
let mut t: f32 = 0.0;
let mut fVar19: f32 = 0.0;
let mut fVar3: f32 = 0.0;
let mut pbVar17: *mut u8 = std::ptr::null_mut();
let mut pbVar15: *mut u8 = std::ptr::null_mut();
let mut src: *mut World = std::ptr::null_mut();
let mut dst: *mut World = std::ptr::null_mut();
let mut bVar9: u8 = 0;
let mut bVar10: u8 = 0;
let mut bVar11: u8 = 0;
let mut bVar12: u8 = 0;
let mut dst_eq_src: bool = false;
'b1: {
'b53: {
'b56: {
'b55: {
tracing = false;start_x = param_3;
start_y = param_4;iVar8 = param_11;cVar7 = param_10;fVar5 = DAT_18000d1f4;fVar4 = DAT_18000d1f0;let _ = {(*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize)) = (*(param_5).wrapping_offset(0_i32 as isize)); (*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize))};let _ = {(*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize)) = (*(param_5).wrapping_offset(1_i32 as isize)); (*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize))};let _ = {(*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize)) = (*(param_5).wrapping_offset(2_i32 as isize)); (*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize))};let _ = {(*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize)) = (*(param_5).wrapping_offset(3_i32 as isize)); (*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize)) = (*(param_8).wrapping_offset(0_i32 as isize)); (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize)) = (*(param_8).wrapping_offset(1_i32 as isize)); (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize)) = (*(param_8).wrapping_offset(2_i32 as isize)); (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize)) = (*(param_8).wrapping_offset(3_i32 as isize)); (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize))};let _ = {uVar14 = (((((param_4).wrapping_sub(param_7))).wrapping_shr(31_i32 as u32)) as u32); uVar14};iVar16 = (((((param_4).wrapping_sub(param_7)) ^ (uVar14 as i32)))).wrapping_sub((uVar14 as i32));let _ = {uVar14 = (((((param_3).wrapping_sub(param_6))).wrapping_shr(31_i32 as u32)) as u32); uVar14};iVar13 = (((((param_3).wrapping_sub(param_6)) ^ (uVar14 as i32)))).wrapping_sub((uVar14 as i32));iVar1 = (*((DAT_18000f0c8).as_ptr() as *mut i32).wrapping_offset((param_2 as i64) as isize));local_res20 = (*((DAT_18000f0f0).as_ptr() as *mut i32).wrapping_offset((param_2 as i64) as isize));
if (iVar16 < iVar13) { break 'b56; } else { break 'b55; }
}
iVar13_loop = 0_i32;
if ((1_i32).wrapping_neg() < iVar16) { break 'b53; } else { break 'b1; }
}
let _ = {iVar16 = iVar13; iVar16};iVar13_loop = 0_i32;
if ((1_i32).wrapping_neg() < iVar16) { break 'b53; } else { break 'b1; }
}
'l53: loop {
'b7: {
'b8: {
'b11: {
'b10: {
'b24: {
'b16: {
'b29: {
'b33: {
'b32: {
'b35: {
'b37: {
'b36: {
'b42: {
'b41: {
'b45: {
'b44: {
'b48: {
'b47: {
'b51: {
'b52: {

if (iVar16 > 0_i32) { break 'b51; } else { break 'b52; }
}
let _ = {t = 0.0_f32; t};fVar19 = (*evaluator).evaluate(t);
if ((tracing && (param_3 == trace_x)) && (param_4 == trace_y)) { break 'b48; } else { break 'b47; }
}
let _ = {t = ((iVar13_loop as f32) / (iVar16 as f32)); t};fVar19 = (*evaluator).evaluate(t);
if ((tracing && (param_3 == trace_x)) && (param_4 == trace_y)) { break 'b48; } else { break 'b47; }
}
fVar3 = fVar5;
if (fVar19 <= fVar5) { break 'b45; } else { break 'b44; }
}
let _ = ();fVar3 = fVar5;
if (fVar19 <= fVar5) { break 'b45; } else { break 'b44; }
}
let _ = {fVar19 = 0.0_f32; fVar19};
if (0.0_f32 <= fVar3) { break 'b42; } else { break 'b41; }
}
let _ = {fVar3 = fVar19; fVar3};let _ = {fVar19 = 0.0_f32; fVar19};
if (0.0_f32 <= fVar3) { break 'b42; } else { break 'b41; }
}
pbVar17 = (std::ptr::null_mut::<u8>() as *mut u8);pbVar15 = (std::ptr::null_mut::<u8>() as *mut u8);src = (*state).src_world;
if (!((((((param_3 < 0_i32)) || (((*src).width <= param_3))) || ((param_4 < 0_i32))) || (((*src).height <= param_4))))) { break 'b37; } else { break 'b36; }
}
let _ = {fVar19 = fVar3; fVar19};pbVar17 = (std::ptr::null_mut::<u8>() as *mut u8);pbVar15 = (std::ptr::null_mut::<u8>() as *mut u8);src = (*state).src_world;
if (!((((((param_3 < 0_i32)) || (((*src).width <= param_3))) || ((param_4 < 0_i32))) || (((*src).height <= param_4))))) { break 'b37; } else { break 'b36; }
}

if ((pbVar17 != (std::ptr::null_mut::<u8>() as *mut u8)) || (param_3 >= 0_i32)) { break 'b35; } else { break 'b32; }
}
let _ = {pbVar17 = ((((*src).data as *mut u8)).wrapping_offset(((((param_4).wrapping_mul((*src).rowbytes)) as i64) as isize))).wrapping_offset((((param_3 as i64)).wrapping_mul((4_i32 as i64)) as isize)); pbVar17};
if ((pbVar17 != (std::ptr::null_mut::<u8>() as *mut u8)) || (param_3 >= 0_i32)) { break 'b35; } else { break 'b32; }
}
dst = (*state).dst_world;
if ((((param_3 < (*dst).width)) && (((1_i32).wrapping_neg() < param_4))) && ((param_4 < (*dst).height))) { break 'b33; } else { break 'b32; }
}
bVar9 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize));
bVar10 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize));bVar11 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize));
bVar12 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize));
if (((cVar7 as i32) != (0_i8 as i32)) && (pbVar17 != (std::ptr::null_mut::<u8>() as *mut u8))) { break 'b29; } else { break 'b16; }
}
let _ = {pbVar15 = ((((*dst).data as *mut u8)).wrapping_offset(((((param_4).wrapping_mul((*dst).rowbytes)) as i64) as isize))).wrapping_offset((((param_3 as i64)).wrapping_mul((4_i32 as i64)) as isize)); pbVar15};bVar9 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize));
bVar10 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize));bVar11 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize));
bVar12 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize));
if (((cVar7 as i32) != (0_i8 as i32)) && (pbVar17 != (std::ptr::null_mut::<u8>() as *mut u8))) { break 'b29; } else { break 'b16; }
}
let _ = {bVar9 = (*(pbVar17).wrapping_offset(0_i32 as isize)); bVar9};let _ = {bVar10 = (*(pbVar17).wrapping_offset(1_i32 as isize)); bVar10};let _ = {bVar11 = (*(pbVar17).wrapping_offset(2_i32 as isize)); bVar11};let _ = {bVar12 = (*(pbVar17).wrapping_offset(3_i32 as isize)); bVar12};
if (iVar13_loop <= iVar8) { break 'b24; } else { break 'b16; }
}
let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize)) = bVar9; (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize)) = bVar10; (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize)) = bVar11; (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize)) = bVar12; (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize))};
if (((fVar5 < fVar19)) || ((fVar19 < 0.0_f32))) { break 'b11; } else { break 'b10; }
}
let _ = {bVar9 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize)); bVar9};let _ = {bVar10 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize)); bVar10};let _ = {bVar11 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize)); bVar11};let _ = {bVar12 = (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize)); bVar12};let _ = {(*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize)) = (*(pbVar17).wrapping_offset(0_i32 as isize)); (*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize))};let _ = {(*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize)) = (*(pbVar17).wrapping_offset(1_i32 as isize)); (*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize))};let _ = {(*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize)) = (*(pbVar17).wrapping_offset(2_i32 as isize)); (*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize))};let _ = {(*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize)) = (*(pbVar17).wrapping_offset(3_i32 as isize)); (*((local_res18).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize)) = bVar9; (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(0_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize)) = bVar10; (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(1_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize)) = bVar11; (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(2_i32 as isize))};let _ = {(*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize)) = bVar12; (*((local_res10).as_mut_ptr() as *mut u8).wrapping_offset(3_i32 as isize))};
if (((fVar5 < fVar19)) || ((fVar19 < 0.0_f32))) { break 'b11; } else { break 'b10; }
}
dst_eq_src = (((((((pbVar15 != (std::ptr::null_mut::<u8>() as *mut u8)) && (pbVar17 != (std::ptr::null_mut::<u8>() as *mut u8))) && (((*(pbVar15).wrapping_offset(1_i32 as isize)) as i32) == ((*(pbVar17).wrapping_offset(1_i32 as isize)) as i32))) && (((*(pbVar15).wrapping_offset(3_i32 as isize)) as i32) == ((*(pbVar17).wrapping_offset(3_i32 as isize)) as i32))) && (((*(pbVar15).wrapping_offset(2_i32 as isize)) as i32) == ((*(pbVar17).wrapping_offset(2_i32 as isize)) as i32))) && (((*(pbVar15).wrapping_offset(0_i32 as isize)) as i32) == ((*(pbVar17).wrapping_offset(0_i32 as isize)) as i32))));
if (!dst_eq_src) { break 'b7; } else { break 'b8; }
}
let _ = {fVar19 = 0.0_f32; fVar19};dst_eq_src = (((((((pbVar15 != (std::ptr::null_mut::<u8>() as *mut u8)) && (pbVar17 != (std::ptr::null_mut::<u8>() as *mut u8))) && (((*(pbVar15).wrapping_offset(1_i32 as isize)) as i32) == ((*(pbVar17).wrapping_offset(1_i32 as isize)) as i32))) && (((*(pbVar15).wrapping_offset(3_i32 as isize)) as i32) == ((*(pbVar17).wrapping_offset(3_i32 as isize)) as i32))) && (((*(pbVar15).wrapping_offset(2_i32 as isize)) as i32) == ((*(pbVar17).wrapping_offset(2_i32 as isize)) as i32))) && (((*(pbVar15).wrapping_offset(0_i32 as isize)) as i32) == ((*(pbVar17).wrapping_offset(0_i32 as isize)) as i32))));
if (!dst_eq_src) { break 'b7; } else { break 'b8; }
}
let _ = AlphaBlend8((local_res18).as_mut_ptr() as *mut u8, (fVar5 - fVar19), (local_res10).as_mut_ptr() as *mut u8, fVar19, pbVar15);let _ = {param_3 = ((param_3).wrapping_add(iVar1)) as i32; param_3};let _ = {let old=iVar13_loop; iVar13_loop=(iVar13_loop).wrapping_add(1); old};let _ = {param_4 = ((param_4).wrapping_add(local_res20)) as i32; param_4};
if (iVar13_loop <= iVar16) { continue 'l53; } else { break 'b1; }
}
let _ = AlphaBlend8((local_res18).as_mut_ptr() as *mut u8, (fVar5 - fVar19), (local_res10).as_mut_ptr() as *mut u8, fVar19, (param_7_arr).as_mut_ptr() as *mut u8);let _ = AlphaBlend8((param_7_arr).as_mut_ptr() as *mut u8, fVar4, (if (pbVar15 != std::ptr::null_mut()) { pbVar15 } else { (param_7_arr).as_mut_ptr() as *mut u8 }), fVar4, pbVar15);let _ = {param_3 = ((param_3).wrapping_add(iVar1)) as i32; param_3};let _ = {let old=iVar13_loop; iVar13_loop=(iVar13_loop).wrapping_add(1); old};let _ = {param_4 = ((param_4).wrapping_add(local_res20)) as i32; param_4};
if (iVar13_loop <= iVar16) { continue 'l53; } else { break 'b1; }
}
}
return ;
}
pub(super) unsafe fn ScanlinePixel8_KeyMask(mut refconV: *mut (), mut arg1: i32, mut arg2: i32, mut inP: *mut Pixel8, mut outP: *mut Pixel8) -> i32 {
let mut state: *mut RenderState = std::ptr::null_mut();
let mut key_r: u8 = 0;
let mut key_g: u8 = 0;
let mut key_b: u8 = 0;
'b6: {
'b2: {
state = (refconV as *mut RenderState);key_r = (((((*state).key_rg_packed as u32) & 255_u32)) as u8);key_g = (((((*state).key_rg_packed as i32)).wrapping_shr(8_i32 as u32)) as u8);key_b = ((*state).key_b as u8);
if ((((((inP != (std::ptr::null_mut::<u8>() as *mut Pixel8)) && (outP != (std::ptr::null_mut::<u8>() as *mut Pixel8))) && (((*inP).alpha as i32) == ((*state).key_a as i32))) && (((*inP).red as i32) == (key_r as i32))) && (((*inP).green as i32) == (key_g as i32))) && (((*inP).blue as i32) == (key_b as i32))) { break 'b6; } else { break 'b2; }
}
return PF_Err_NONE;
}
let _ = {(*outP).alpha = (0_i32 as u8); (*outP).alpha};let _ = {(*outP).red = key_r; (*outP).red};let _ = {(*outP).green = key_g; (*outP).green};let _ = {(*outP).blue = key_b; (*outP).blue};return PF_Err_NONE;
}
pub(super) unsafe fn ScanlinePixel16_KeyMask(mut refconV: *mut (), mut arg1: i32, mut arg2: i32, mut inP: *mut Pixel16, mut outP: *mut Pixel16) -> i32 {
let mut state: *mut RenderState = std::ptr::null_mut();
'b6: {
'b2: {
state = (refconV as *mut RenderState);
if ((((((inP != (std::ptr::null_mut::<u8>() as *mut Pixel16)) && (outP != (std::ptr::null_mut::<u8>() as *mut Pixel16))) && (((*inP).alpha as i32) == ((*state).key16_a as i32))) && (((*inP).red as i32) == ((*state).key16_r as i32))) && (((*inP).green as i32) == ((*state).key16_g as i32))) && (((*inP).blue as i32) == ((*state).key16_b as i32))) { break 'b6; } else { break 'b2; }
}
return PF_Err_NONE;
}
let _ = {(*outP).alpha = (0_i32 as u16); (*outP).alpha};let _ = {(*outP).red = (*state).key16_r; (*outP).red};let _ = {(*outP).green = (*state).key16_g; (*outP).green};let _ = {(*outP).blue = (*state).key16_b; (*outP).blue};return PF_Err_NONE;
}
