// ============================================================================
// InterpExecutor16 — literal port of FUN_180005f60.
//
// Loop body (Win disasm 0x180006090):
//   for (i = 0; i <= iVar16; ++i) {
//     t = (iVar16 > 0) ? (float)i / (float)iVar16 : 0.0f;       // implicit XMM1
//     weight = curve.eval(t);  // virtual call, returns float
//     weight = clamp(weight, 0, 1);
//     ... blend using weight
//   }
// param_5 = "color A", param_8 = "color B" (start-end pixels for blending).
// ============================================================================
static void
InterpExecutor16(RenderState *state, int param_2, int param_3, int param_4,
                 const uint16_t *param_5, int param_6, int param_7,
                 const uint16_t *param_8, LinearEvalBase *evaluator,
                 char param_10, int param_11)
{
#ifdef OLMSMOOTHER_TEST_HOOKS
	if (g_interp_executor16_test_hook != nullptr) {
		g_interp_executor16_test_hook(state,param_2,param_3,param_4,param_5,
		                              param_6,param_7,param_8,evaluator,param_10,param_11);
		return;
	}
#endif
	int iVar7  = param_11;
	char cVar6 = param_10;
	float fVar4 = DAT_18000d1f4;
	float fVar3 = DAT_18000d1f0;

	uint16_t local_68[4];
	uint16_t param_5_arr[4];
	uint16_t param_8_arr[4];
	local_68[0] = param_5[0]; local_68[1] = param_5[1];
	local_68[2] = param_5[2]; local_68[3] = param_5[3];
	param_5_arr[0] = param_8[0]; param_5_arr[1] = param_8[1];
	param_5_arr[2] = param_8[2]; param_5_arr[3] = param_8[3];

	uint32_t uVar14;
	uVar14 = (uint32_t)((param_4 - param_7) >> 31);
	int iVar16 = (int)((param_4 - param_7) ^ (int)uVar14) - (int)uVar14;
	uVar14 = (uint32_t)((param_3 - param_6) >> 31);
	int iVar12 = (int)((param_3 - param_6) ^ (int)uVar14) - (int)uVar14;
	int dx_step = DAT_18000f0c8[(int64_t)param_2];
	int dy_step = DAT_18000f0f0[(int64_t)param_2];
	if (iVar16 < iVar12) iVar16 = iVar12;
	int iVar12_loop = 0;

	if (-1 < iVar16) {
		do {
			float t;
			if (iVar16 > 0) {
				t = (float)iVar12_loop / (float)iVar16;
			} else {
				t = 0.0f;
			}
			float fVar19 = evaluator->Evaluate(t);
			float fVar2 = fVar4;
			if (fVar19 <= fVar4) fVar2 = fVar19;
			fVar19 = 0.0f;
			if (0.0f <= fVar2) fVar19 = fVar2;
			uint16_t *puVar17 = nullptr;
			uint16_t *ppuVar15 = nullptr;
			PF_EffectWorld *src = state->src_world;
			if (!((param_3 < 0) || (src->width <= param_3) ||
			      (param_4 < 0) || (src->height <= param_4))) {
				puVar17 = (uint16_t*)((uint8_t*)src->data + (int64_t)(param_4 * src->rowbytes) +
				                      (int64_t)param_3 * 8);
			}
			if (puVar17 != nullptr || param_3 >= 0) {
				PF_EffectWorld *dst = state->dst_world;
				if ((param_3 < dst->width) && (-1 < param_4) && (param_4 < dst->height)) {
					ppuVar15 = (uint16_t*)((uint8_t*)dst->data + (int64_t)(param_4 * dst->rowbytes) +
					                       (int64_t)param_3 * 8);
				}
			}
			uint16_t uVar8 = param_5_arr[0];
			uint16_t uVar9 = param_5_arr[1];
			uint16_t uVar10 = param_5_arr[2];
			uint16_t uVar11 = param_5_arr[3];
			if (cVar6 != '\0' && puVar17 != nullptr) {
				uVar8 = puVar17[0];
				uVar9 = puVar17[1];
				uVar10 = puVar17[2];
				uVar11 = puVar17[3];
				if (iVar12_loop <= iVar7) {
					uVar8 = param_5_arr[0];
					uVar9 = param_5_arr[1];
					uVar10 = param_5_arr[2];
					uVar11 = param_5_arr[3];
					local_68[0] = puVar17[0];
					local_68[1] = puVar17[1];
					local_68[2] = puVar17[2];
					local_68[3] = puVar17[3];
				}
			}
			param_5_arr[0] = uVar8; param_5_arr[1] = uVar9;
			param_5_arr[2] = uVar10; param_5_arr[3] = uVar11;
			if ((fVar4 < fVar19) || (fVar19 < 0.0f)) fVar19 = 0.0f;

			bool dst_eq_src = (ppuVar15 != nullptr && puVar17 != nullptr &&
			                   ppuVar15[1] == puVar17[1] &&
			                   ppuVar15[3] == puVar17[3] &&
			                   ppuVar15[2] == puVar17[2] &&
			                   ppuVar15[0] == puVar17[0]);
			if (!dst_eq_src) {
				AlphaBlend16(local_68, fVar4 - fVar19, param_5_arr, fVar19, param_8_arr);
				AlphaBlend16(param_8_arr, fVar3, ppuVar15 ? ppuVar15 : param_8_arr, fVar3, ppuVar15);
			} else {
				AlphaBlend16(local_68, fVar4 - fVar19, param_5_arr, fVar19, ppuVar15);
			}
			param_3 += dx_step;
			iVar12_loop++;
			param_4 += dy_step;
		} while (iVar12_loop <= iVar16);
	}
}

// ============================================================================
// InterpExecutor8 — literal port of FUN_180006270 (twin of InterpExecutor16).
// ============================================================================
static void
InterpExecutor8(RenderState *state, int param_2, int param_3, int param_4,
                const uint8_t *param_5, int param_6, int param_7,
                const uint8_t *param_8, LinearEvalBase *evaluator,
                char param_10, int param_11)
{
#ifdef OLMSMOOTHER_TEST_HOOKS
	if (g_interp_executor8_test_hook != nullptr) {
		g_interp_executor8_test_hook(state, param_2, param_3, param_4,
		                            param_5, param_6, param_7, param_8,
		                            evaluator, param_10, param_11);
		return;
	}
#endif
	int trace_x, trace_y;
	const bool tracing = trace_xy_enabled(&trace_x, &trace_y);
	const int start_x = param_3, start_y = param_4;
	int iVar8  = param_11;
	char cVar7 = param_10;
	float fVar5 = DAT_18000d1f4;
	float fVar4 = DAT_18000d1f0;

	uint8_t local_res18[4];
	uint8_t local_res10[4];
	uint8_t param_7_arr[4];
	local_res18[0] = param_5[0]; local_res18[1] = param_5[1];
	local_res18[2] = param_5[2]; local_res18[3] = param_5[3];
	local_res10[0] = param_8[0]; local_res10[1] = param_8[1];
	local_res10[2] = param_8[2]; local_res10[3] = param_8[3];

	uint32_t uVar14;
	uVar14 = (uint32_t)((param_4 - param_7) >> 31);
	int iVar16 = (int)((param_4 - param_7) ^ (int)uVar14) - (int)uVar14;
	uVar14 = (uint32_t)((param_3 - param_6) >> 31);
	int iVar13 = (int)((param_3 - param_6) ^ (int)uVar14) - (int)uVar14;
	int iVar1 = DAT_18000f0c8[(int64_t)param_2];
	int local_res20 = DAT_18000f0f0[(int64_t)param_2];
	if (iVar16 < iVar13) iVar16 = iVar13;
	int iVar13_loop = 0;

	if (-1 < iVar16) {
		do {
			float t;
			if (iVar16 > 0) {
				t = (float)iVar13_loop / (float)iVar16;
			} else {
				t = 0.0f;
			}
			float fVar19 = evaluator->Evaluate(t);
			if (tracing && param_3 == trace_x && param_4 == trace_y) {
				fprintf(stderr,
				        "[exec8] dir=%d start=(%d,%d) end_hint=(%d,%d) i=%d/%d t=%.6f eval=%.6f "
				        "iVar8=%d cVar7=%d src5=[%u,%u,%u,%u] src8=[%u,%u,%u,%u] "
				        "curve{ofs=%.6f v0=%.6f v1=%.6f v2=%.6f}\n",
				        param_2, start_x, start_y, param_6, param_7,
				        iVar13_loop, iVar16, t, fVar19, iVar8, (int)cVar7,
				        param_5[0], param_5[1], param_5[2], param_5[3],
				        param_8[0], param_8[1], param_8[2], param_8[3],
				        evaluator->offset, evaluator->v0, evaluator->v1, evaluator->v2);
			}
			float fVar3 = fVar5;
			if (fVar19 <= fVar5) fVar3 = fVar19;
			fVar19 = 0.0f;
			if (0.0f <= fVar3) fVar19 = fVar3;
			uint8_t *pbVar17 = nullptr;
			uint8_t *pbVar15 = nullptr;
			PF_EffectWorld *src = state->src_world;
			if (!((param_3 < 0) || (src->width <= param_3) ||
			      (param_4 < 0) || (src->height <= param_4))) {
				pbVar17 = (uint8_t*)src->data + (int64_t)(param_4 * src->rowbytes) +
				          (int64_t)param_3 * 4;
			}
			if (pbVar17 != nullptr || param_3 >= 0) {
				PF_EffectWorld *dst = state->dst_world;
				if ((param_3 < dst->width) && (-1 < param_4) && (param_4 < dst->height)) {
					pbVar15 = (uint8_t*)dst->data + (int64_t)(param_4 * dst->rowbytes) +
					          (int64_t)param_3 * 4;
				}
			}
			uint8_t bVar9 = local_res10[0], bVar10 = local_res10[1];
			uint8_t bVar11 = local_res10[2], bVar12 = local_res10[3];
			if (cVar7 != '\0' && pbVar17 != nullptr) {
				bVar9 = pbVar17[0]; bVar10 = pbVar17[1];
				bVar11 = pbVar17[2]; bVar12 = pbVar17[3];
				if (iVar13_loop <= iVar8) {
					bVar9 = local_res10[0]; bVar10 = local_res10[1];
					bVar11 = local_res10[2]; bVar12 = local_res10[3];
					local_res18[0] = pbVar17[0]; local_res18[1] = pbVar17[1];
					local_res18[2] = pbVar17[2]; local_res18[3] = pbVar17[3];
				}
			}
			local_res10[0] = bVar9; local_res10[1] = bVar10;
			local_res10[2] = bVar11; local_res10[3] = bVar12;
			if ((fVar5 < fVar19) || (fVar19 < 0.0f)) fVar19 = 0.0f;

			bool dst_eq_src = (pbVar15 != nullptr && pbVar17 != nullptr &&
			                   pbVar15[1] == pbVar17[1] &&
			                   pbVar15[3] == pbVar17[3] &&
			                   pbVar15[2] == pbVar17[2] &&
			                   pbVar15[0] == pbVar17[0]);
			if (!dst_eq_src) {
				AlphaBlend8(local_res18, fVar5 - fVar19, local_res10, fVar19, param_7_arr);
				AlphaBlend8(param_7_arr, fVar4, pbVar15 ? pbVar15 : param_7_arr, fVar4, pbVar15);
			} else {
				AlphaBlend8(local_res18, fVar5 - fVar19, local_res10, fVar19, pbVar15);
			}
			param_3 += iVar1;
			iVar13_loop++;
			param_4 += local_res20;
		} while (iVar13_loop <= iVar16);
	}
}

// ============================================================================
// Per-pixel scanline callbacks — match the structure of FUN_180009470 (16-bit)
// and FUN_1800095b0 (8-bit) literally:
//   1. Build 9-neighbor pointer table (FUN_180003ff0 / 180004220)
//   2. For each direction in {5, 3, 1, 7}: classify, then dispatch
//   3. Return success
// Since Classifier* returns 0 in this stage, no work is done and outP==inP.
// ============================================================================
static PF_Err
ScanlinePixel16_Main(void *refconV, A_long x, A_long y,
                     PF_Pixel16 *inP, PF_Pixel16 *outP)
{
	RenderState *state = (RenderState*)refconV;
	uintptr_t neigh[10];
	(void)inP; (void)outP;  // pre-copied in RenderEntryChain; kernel writes to dst_world.

	NeighborExtract16((int)x, (int)y, state, neigh);

	int32_t st;
	st = Classifier16(state, (uint32_t)x, (uint32_t)y, neigh, 5);
	DispatchDirection16(state, neigh, (uint32_t)x, (uint32_t)y, 5, st);
	st = Classifier16(state, (uint32_t)x, (uint32_t)y, neigh, 3);
	DispatchDirection16(state, neigh, (uint32_t)x, (uint32_t)y, 3, st);
	st = Classifier16(state, (uint32_t)x, (uint32_t)y, neigh, 1);
	DispatchDirection16(state, neigh, (uint32_t)x, (uint32_t)y, 1, st);
	st = Classifier16(state, (uint32_t)x, (uint32_t)y, neigh, 7);
	DispatchDirection16(state, neigh, (uint32_t)x, (uint32_t)y, 7, st);
	return PF_Err_NONE;
}

static PF_Err
ScanlinePixel8_Main(void *refconV, A_long x, A_long y,
                    PF_Pixel8 *inP, PF_Pixel8 *outP)
{
	RenderState *state = (RenderState*)refconV;
	uintptr_t neigh[10];
	(void)inP; (void)outP;

	NeighborExtract8((int)x, (int)y, state, neigh);

	int tx, ty;
	const bool tr = trace_xy_enabled(&tx, &ty) && (int)x == tx && (int)y == ty;
	int32_t st;
	st = Classifier8(state, (uint32_t)x, (uint32_t)y, neigh, 5);
	if (tr) fprintf(stderr, "[cls8] (%d,%d) dir=5 scan_type=%d\n", (int)x, (int)y, st);
	DispatchDirection8(state, neigh, (uint32_t)x, (uint32_t)y, 5, st);
	st = Classifier8(state, (uint32_t)x, (uint32_t)y, neigh, 3);
	if (tr) fprintf(stderr, "[cls8] (%d,%d) dir=3 scan_type=%d\n", (int)x, (int)y, st);
	DispatchDirection8(state, neigh, (uint32_t)x, (uint32_t)y, 3, st);
	st = Classifier8(state, (uint32_t)x, (uint32_t)y, neigh, 1);
	if (tr) fprintf(stderr, "[cls8] (%d,%d) dir=1 scan_type=%d\n", (int)x, (int)y, st);
	DispatchDirection8(state, neigh, (uint32_t)x, (uint32_t)y, 1, st);
	st = Classifier8(state, (uint32_t)x, (uint32_t)y, neigh, 7);
	if (tr) fprintf(stderr, "[cls8] (%d,%d) dir=7 scan_type=%d\n", (int)x, (int)y, st);
	DispatchDirection8(state, neigh, (uint32_t)x, (uint32_t)y, 7, st);
	return PF_Err_NONE;
}

// LAB_1800026e0 — PF8 key-mask callback. The temporary destination world is
// pre-copied from the source; this callback changes only an exact ARGB key
// match, replacing it with the same RGB and alpha zero.
static PF_Err
ScanlinePixel8_KeyMask(void *refconV, A_long /*x*/, A_long /*y*/,
                       PF_Pixel8 *inP, PF_Pixel8 *outP)
{
	RenderState *state = (RenderState*)refconV;
	const uint8_t key_r = (uint8_t)(state->key_rg_packed & 0xffu);
	const uint8_t key_g = (uint8_t)(state->key_rg_packed >> 8);
	const uint8_t key_b = (uint8_t)state->key_b;
	if (inP != nullptr && outP != nullptr &&
	    inP->alpha == state->key_a && inP->red == key_r &&
	    inP->green == key_g && inP->blue == key_b) {
		outP->alpha = 0;
		outP->red = key_r;
		outP->green = key_g;
		outP->blue = key_b;
	}
	return PF_Err_NONE;
}

static PF_Err
ScanlinePixel16_KeyMask(void *refconV, A_long /*x*/, A_long /*y*/,
                        PF_Pixel16 *inP, PF_Pixel16 *outP)
{
	RenderState *state = (RenderState*)refconV;
	if (inP != nullptr && outP != nullptr &&
	    inP->alpha == state->key16_a && inP->red == state->key16_r &&
	    inP->green == state->key16_g && inP->blue == state->key16_b) {
		outP->alpha = 0;
		outP->red = state->key16_r;
		outP->green = state->key16_g;
		outP->blue = state->key16_b;
	}
	return PF_Err_NONE;
}

// 32-bit float — no Win analogue.
static PF_Err
ScanlinePixelFloat_Main(void *refconV, A_long /*x*/, A_long /*y*/,
                        PF_PixelFloat *inP, PF_PixelFloat *outP)
{
	(void)refconV;
	*outP = *inP;
	return PF_Err_NONE;
}

static PF_Err
ScanlinePixelFloat_KeyMask(void *refconV, A_long /*x*/, A_long /*y*/,
                           PF_PixelFloat *inP, PF_PixelFloat *outP)
{
	(void)refconV;
	*outP = *inP;
	return PF_Err_NONE;
}

// ============================================================================
// Render entry chain — FUN_180001400 (8-bit) / FUN_1800011e0 (16-bit) literal port
// using PF_Iterate{8,16,Float} Suite. State->src_world / dst_world get set
// before each pass so the kernel-side neighbor extractor can read from them.
// ============================================================================
template <typename PixelT, typename SuiteT>
static PF_Err
RenderEntryChain(PF_InData       *in_data,
                 const char      *suite_name,
                 int32_t          suite_version,
                 PF_EffectWorld  *input,
                 PF_EffectWorld  *output,
                 RenderState     *state,
                 PF_Err         (*main_pix_fn)(void*, A_long, A_long, PixelT*, PixelT*),
                 PF_Err         (*mask_pix_fn)(void*, A_long, A_long, PixelT*, PixelT*),
                 bool             classic_extent = false)
{
	PF_Err err = PF_Err_NONE;
	(void)in_data;
	(void)suite_name;
	(void)suite_version;

	// The interpolation callbacks can write neighbouring destination pixels.
	// PF_Iterate is allowed to schedule pixels concurrently, which would make
	// those writes race and make the result dependent on host scheduling.  The
	// Windows control flow is scanline ordered, so keep this lane deterministic
	// with an explicit top-to-bottom, left-to-right traversal.
	// Original Classic passes the OUTPUT extent to both iterate calls, including
	// the key-mask pass into the source-sized temporary world (PF16 +0x12f0,
	// +0x1389; PF8 +0x1510, +0x15a9). Copies and contour reads remain world-wide.
	const A_long left = classic_extent ? output->extent_hint.left : 0;
	const A_long top = classic_extent ? output->extent_hint.top : 0;
	const A_long right = classic_extent ? output->extent_hint.right : output->width;
	const A_long bottom = classic_extent ? output->extent_hint.bottom : output->height;
	auto scan_world = [=](PF_EffectWorld *src, PF_EffectWorld *dst, void *refcon,
	                     PF_Err (*pixel_fn)(void*, A_long, A_long, PixelT*, PixelT*)) -> PF_Err {
		for (A_long y = top; y < bottom; ++y) {
			PixelT *src_row = reinterpret_cast<PixelT *>(
				reinterpret_cast<uint8_t *>(src->data) + (int64_t)y * src->rowbytes);
			PixelT *dst_row = reinterpret_cast<PixelT *>(
				reinterpret_cast<uint8_t *>(dst->data) + (int64_t)y * dst->rowbytes);
			for (A_long x = left; x < right; ++x) {
				PF_Err pixel_err = pixel_fn(refcon, x, y, src_row + x, dst_row + x);
				if (pixel_err) return pixel_err;
			}
		}
		return PF_Err_NONE;
	};

	PF_EffectWorld *pass_input = input;
	PF_EffectWorld key_world{};
	void *key_world_data = nullptr;
	state->src_world = pass_input;
	state->dst_world = output;

	// Windows allocates and pre-copies a temporary integer world before invoking
	// LAB_1800026e0 (PF8) or LAB_180002670 (PF16). PF32 has no native analogue.
	if (state->use_key &&
	    (sizeof(PixelT) == sizeof(PF_Pixel8) || sizeof(PixelT) == sizeof(PF_Pixel16))) {
		const A_long rows = input->height;
		const A_long rowbytes = input->rowbytes;
		if (rows > 0 && rowbytes > 0) {
			const size_t bytes = (size_t)rows * (size_t)rowbytes;
			key_world_data = malloc(bytes);
			if (key_world_data == nullptr) return (PF_Err)4; // PF_Err_OUT_OF_MEMORY
			memcpy(key_world_data, input->data, bytes);
			key_world = *input;
			key_world.data = static_cast<decltype(key_world.data)>(key_world_data);
			state->src_world = input;
			state->dst_world = &key_world;
				err = scan_world(input, &key_world, state, mask_pix_fn);
			if (!err) pass_input = &key_world;
		}
	}

	// 2nd pass — main interp kernel.
	if (!err) {
		state->src_world = pass_input;
		state->dst_world = output;
		// Pre-copy input → output so kernel writes (which may target neighboring
		// pixels) survive subsequent iterate steps. The callback writes outP=inP
		// for any non-classified pixel; for classified pixels the kernel writes
		// directly into output world (state->dst_world).
		{
			A_long copy_h = pass_input->height;
			if (output->height < copy_h) copy_h = output->height;
			A_long row_bytes = pass_input->width * (int)sizeof(PixelT);
			if (output->rowbytes < pass_input->rowbytes) {
				row_bytes = (output->rowbytes < row_bytes) ? output->rowbytes : row_bytes;
			} else if (pass_input->rowbytes < row_bytes) {
				row_bytes = pass_input->rowbytes;
			}
			for (A_long row = 0; row < copy_h; ++row) {
				memcpy((uint8_t*)output->data + (int64_t)row * output->rowbytes,
				       (uint8_t*)pass_input->data + (int64_t)row * pass_input->rowbytes,
				       (size_t)row_bytes);
			}
		}
		err = scan_world(pass_input, output, state, main_pix_fn);
	}

	free(key_world_data);
	return err;
}

// ----------------------------------------------------------------------------
// Build the RenderState — Win FUN_1800096f0 local_4d8 setup.
// ----------------------------------------------------------------------------
static void
BuildRenderState(PF_ParamDef *params[], short bitdepth, RenderState *state)
{
	memset(state, 0, sizeof(*state));
	state->use_key   = (uint8_t)(params[SM_USE_KEY]->u.bd.value != 0);
	state->tolerance = params[SM_TOLERANCE]->u.sd.value;
	// Both Classifier{16,8} read RAW tolerance from these fields and apply
	// `<<7` internally for 16-bit. Mirror Win local_4d0/local_4cc layout: both
	// fields hold the raw tolerance value.
	state->tolerance_lo = state->tolerance;
	state->tolerance_hi = state->tolerance;

	uint8_t a = params[SM_KEY_COLOR]->u.cd.value.alpha;
	uint8_t r = params[SM_KEY_COLOR]->u.cd.value.red;
	uint8_t g = params[SM_KEY_COLOR]->u.cd.value.green;
	uint8_t b = params[SM_KEY_COLOR]->u.cd.value.blue;

	if (bitdepth >= 16) {
		// Win widens the 8-bit color components to 15-bit at 16-bit depth.
		state->key_a         = a;
		state->key16_a       = Widen8To16(a);
		state->key16_r       = Widen8To16(r);
		state->key16_g       = Widen8To16(g);
		state->key16_b       = Widen8To16(b);
		state->threshold     = state->tolerance;
	} else {
		state->key_a         = a;
		state->key_rg_packed = (uint16_t)((g << 8) | r);
		state->key_b         = (uint16_t)b;
		state->threshold     = state->tolerance;
	}
	state->src_world = nullptr;
	state->dst_world = nullptr;
}

