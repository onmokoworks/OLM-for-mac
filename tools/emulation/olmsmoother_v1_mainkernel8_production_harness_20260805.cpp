#include <cstdint>
#include <cstring>
#include <new>
#define OLMSMOOTHER_TEST_HOOKS 1
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

extern "C" {
struct MainCapture8 {
	int32_t direction, start_x, start_y, color_a_index;
	int32_t end_x, end_y, color_b_index, evaluator_kind;
	int32_t use_source, leading_span;
	uint32_t fields[4];
};
struct NaturalMainCall8 { int32_t args12[12]; };
struct TouchingExecutorCall8 {
	int32_t center_x, center_y;
	int32_t args11[11];
	int32_t evaluator_kind;
	uint32_t fields[4];
};
}

static const uint8_t *g_pixels[9];
static MainCapture8 *g_captures;
static int g_capture_count;
static int g_capture_capacity;
static TouchingExecutorCall8 *g_touching_calls;
static int g_touching_count, g_touching_capacity;
static int g_touching_x, g_touching_y, g_center_x, g_center_y;
static uint8_t *g_source_base;
static int g_source_rowbytes;

static int pixel_index(const uint8_t *pixel)
{
	for (int index = 0; index < 9; ++index) {
		if (g_pixels[index] == pixel) return index;
	}
	return -1;
}

static void capture_executor(RenderState *, int direction, int start_x, int start_y,
                             const uint8_t *color_a, int end_x, int end_y,
                             const uint8_t *color_b, LinearEvalBase *evaluator,
                             char use_source, int leading_span)
{
	if (g_capture_count >= g_capture_capacity) return;
	MainCapture8 &capture = g_captures[g_capture_count++];
	std::memset(&capture, 0, sizeof(capture));
	capture.direction = direction;
	capture.start_x = start_x;
	capture.start_y = start_y;
	capture.color_a_index = pixel_index(color_a);
	capture.end_x = end_x;
	capture.end_y = end_y;
	capture.color_b_index = pixel_index(color_b);
	capture.use_source = static_cast<unsigned char>(use_source);
	capture.leading_span = leading_span;
	if (dynamic_cast<LinearOffsetFunction*>(evaluator)) capture.evaluator_kind = 0;
	else if (dynamic_cast<LinearOffsetOneValue*>(evaluator)) capture.evaluator_kind = 1;
	else if (dynamic_cast<LinearOffsetZeroOneValue*>(evaluator)) capture.evaluator_kind = 2;
	else if (dynamic_cast<LinearOffsetZeroValue*>(evaluator)) capture.evaluator_kind = 3;
	else if (dynamic_cast<LinearThreeOffsetFunction*>(evaluator)) capture.evaluator_kind = 4;
	else capture.evaluator_kind = -1;
	std::memcpy(capture.fields, &evaluator->offset, sizeof(capture.fields));
}

static int evaluator_kind(LinearEvalBase *evaluator)
{
	if (dynamic_cast<LinearOffsetFunction*>(evaluator)) return 0;
	if (dynamic_cast<LinearOffsetOneValue*>(evaluator)) return 1;
	if (dynamic_cast<LinearOffsetZeroOneValue*>(evaluator)) return 2;
	if (dynamic_cast<LinearOffsetZeroValue*>(evaluator)) return 3;
	if (dynamic_cast<LinearThreeOffsetFunction*>(evaluator)) return 4;
	return -1;
}

static void capture_touching_executor(RenderState *, int direction, int start_x, int start_y,
	                                  const uint8_t *color_a, int end_x, int end_y,
	                                  const uint8_t *color_b, LinearEvalBase *evaluator,
	                                  char use_source, int leading_span)
{
	const int step_x = DAT_18000f0c8[direction];
	const int step_y = DAT_18000f0f0[direction];
	const int length_x = start_x > end_x ? start_x - end_x : end_x - start_x;
	const int length_y = start_y > end_y ? start_y - end_y : end_y - start_y;
	const int length = length_x > length_y ? length_x : length_y;
	bool touches = false;
	int x = start_x, y = start_y;
	for (int index = 0; index <= length; ++index, x += step_x, y += step_y) {
		if (x == g_touching_x && y == g_touching_y) { touches = true; break; }
	}
	if (!touches) return;
	const int index = g_touching_count++;
	if (index >= g_touching_capacity) return;
	TouchingExecutorCall8 &capture = g_touching_calls[index];
	std::memset(&capture, 0, sizeof(capture));
	capture.center_x = g_center_x; capture.center_y = g_center_y;
	const auto pixel_xy = [](const uint8_t *pixel, int &px, int &py) {
		const int64_t offset = pixel - g_source_base;
		py = static_cast<int>(offset / g_source_rowbytes);
		px = static_cast<int>((offset % g_source_rowbytes) / 4);
	};
	int color_a_x, color_a_y, color_b_x, color_b_y;
	pixel_xy(color_a, color_a_x, color_a_y);
	pixel_xy(color_b, color_b_x, color_b_y);
	int32_t values[11] = {direction, start_x, start_y, color_a_x, color_a_y,
	                      end_x, end_y, color_b_x, color_b_y,
	                      static_cast<unsigned char>(use_source), leading_span};
	std::memcpy(capture.args11, values, sizeof(values));
	capture.evaluator_kind = evaluator_kind(evaluator);
	std::memcpy(capture.fields, &evaluator->offset, sizeof(capture.fields));
}

extern "C" int olmsmoother_run_mainkernel8_production(
    const int32_t *args12, const uint8_t *neighborhood_argb,
    MainCapture8 *captures, int capacity)
{
	uint8_t pixels[9][4];
	uintptr_t neighborhood[9];
	for (int index = 0; index < 9; ++index) {
		std::memcpy(pixels[index], neighborhood_argb + index * 4, 4);
		g_pixels[index] = pixels[index];
		neighborhood[index] = reinterpret_cast<uintptr_t>(pixels[index]);
	}
	RenderState state{};
	g_captures = captures;
	g_capture_count = 0;
	g_capture_capacity = capacity;
	g_interp_executor8_test_hook = capture_executor;
	MainInterpKernel8(&state, neighborhood,
	                  args12[0], args12[1], args12[2], args12[3],
	                  static_cast<char>(args12[4]), static_cast<char>(args12[5]),
	                  args12[6], args12[7], args12[8], args12[9],
	                  args12[10], args12[11]);
	g_interp_executor8_test_hook = nullptr;
	return g_capture_count;
}

extern "C" void olmsmoother_run_executor8_production(
    uint8_t *source, uint8_t *destination, int32_t width, int32_t height,
    int32_t rowbytes, const int32_t *args11, int32_t evaluator_kind,
    const uint32_t *field_bits)
{
	PF_EffectWorld src{}, dst{};
	src.data = source; src.width = width; src.height = height; src.rowbytes = rowbytes;
	dst.data = destination; dst.width = width; dst.height = height; dst.rowbytes = rowbytes;
	RenderState state{};
	state.src_world = &src;
	state.dst_world = &dst;
	float fields[4];
	std::memcpy(fields, field_bits, sizeof(fields));
	alignas(16) uint8_t evaluator_storage[64];
	LinearEvalBase *evaluator = nullptr;
	switch (evaluator_kind) {
		case 0: evaluator = new (evaluator_storage) LinearOffsetFunction(fields[0], fields[1]); break;
		case 1: evaluator = new (evaluator_storage) LinearOffsetOneValue(fields[0], fields[1], fields[2]); break;
		case 2: evaluator = new (evaluator_storage) LinearOffsetZeroOneValue(fields[0], fields[1], fields[2], fields[3]); break;
		case 3: evaluator = new (evaluator_storage) LinearOffsetZeroValue(fields[0], fields[1], fields[2]); break;
		case 4: evaluator = new (evaluator_storage) LinearThreeOffsetFunction(fields[0], fields[1], fields[2], fields[3]); break;
		default: return;
	}
	const uint8_t *color_a = source + static_cast<int64_t>(args11[4]) * rowbytes + args11[3] * 4;
	const uint8_t *color_b = source + static_cast<int64_t>(args11[8]) * rowbytes + args11[7] * 4;
	g_interp_executor8_test_hook = nullptr;
	InterpExecutor8(&state, args11[0], args11[1], args11[2], color_a,
	                args11[5], args11[6], color_b, evaluator,
	                static_cast<char>(args11[9]), args11[10]);
}

extern "C" int olmsmoother_collect_natural_main_calls_production(
    uint8_t *source, int32_t width, int32_t height, int32_t rowbytes,
    const int32_t *centers_xy, int32_t center_count,
    NaturalMainCall8 *calls, int32_t capacity)
{
	PF_EffectWorld src{}, dst{};
	src.data = source; src.width = width; src.height = height; src.rowbytes = rowbytes;
	dst = src;
	RenderState state{};
	state.tolerance_lo = 6; state.tolerance_hi = 6;
	state.src_world = &src; state.dst_world = &dst;
	state.tolerance = 6; state.threshold = 6;
	const int directions[4] = {5, 3, 1, 7};
	int count = 0;
	for (int center = 0; center < center_count; ++center) {
		const int x = centers_xy[center * 2];
		const int y = centers_xy[center * 2 + 1];
		uintptr_t neighborhood[9];
		NeighborExtract8(x, y, &state, neighborhood);
		for (int direction : directions) {
			if (Classifier8(&state, x, y, neighborhood, direction) != 1) continue;
			uint32_t mode, p9x, p9y, p11x, p11y, p13x, p13y;
			uint8_t flag_a, flag_b;
			SubHandler8(&state, neighborhood, x, y, direction,
			            &mode, &flag_a, &flag_b, &p9x, &p9y,
			            &p11x, &p11y, &p13x, &p13y);
			if (p9x == p11x && p9y == p11y) continue;
			if (count < capacity) {
				int32_t *out = calls[count].args12;
				out[0]=x; out[1]=y; out[2]=direction; out[3]=(int32_t)mode;
				out[4]=(int32_t)flag_a; out[5]=(int32_t)flag_b;
				out[6]=(int32_t)p9x; out[7]=(int32_t)p9y;
				out[8]=(int32_t)p11x; out[9]=(int32_t)p11y;
				out[10]=(int32_t)p13x; out[11]=(int32_t)p13y;
			}
			++count;
		}
	}
	return count;
}

extern "C" void olmsmoother_query_natural_subhandler_production(
    uint8_t *source, int32_t width, int32_t height, int32_t rowbytes,
    int32_t x, int32_t y, int32_t direction, int32_t *result10)
{
	PF_EffectWorld src{}, dst{};
	src.data = source; src.width = width; src.height = height; src.rowbytes = rowbytes;
	dst = src;
	RenderState state{};
	state.tolerance_lo = 6; state.tolerance_hi = 6;
	state.src_world = &src; state.dst_world = &dst;
	state.tolerance = 6; state.threshold = 6;
	uintptr_t neighborhood[9];
	NeighborExtract8(x, y, &state, neighborhood);
	const int scan_type = Classifier8(&state, x, y, neighborhood, direction);
	result10[0] = scan_type;
	if (scan_type != 1) return;
	uint32_t mode, p9x, p9y, p11x, p11y, p13x, p13y;
	uint8_t flag_a, flag_b;
	SubHandler8(&state, neighborhood, x, y, direction,
	            &mode, &flag_a, &flag_b, &p9x, &p9y,
	            &p11x, &p11y, &p13x, &p13y);
	result10[1]=(int32_t)mode; result10[2]=(int32_t)flag_a; result10[3]=(int32_t)flag_b;
	result10[4]=(int32_t)p9x; result10[5]=(int32_t)p9y;
	result10[6]=(int32_t)p11x; result10[7]=(int32_t)p11y;
	result10[8]=(int32_t)p13x; result10[9]=(int32_t)p13y;
}

extern "C" uintptr_t olmsmoother_run_edgewalker8_production(
    uint8_t *source, int32_t width, int32_t height, int32_t rowbytes,
    int32_t x, int32_t y, int32_t direction1, int32_t direction2,
    int32_t threshold, int32_t *out_x, int32_t *out_y)
{
	PF_EffectWorld src{};
	src.data = source; src.width = width; src.height = height; src.rowbytes = rowbytes;
	RenderState state{};
	state.tolerance_lo = threshold; state.tolerance_hi = threshold;
	state.src_world = &src; state.threshold = threshold;
	return reinterpret_cast<uintptr_t>(
	    EdgeWalker8(&state, x, y, direction1, direction2, out_x, out_y, threshold));
}

extern "C" void olmsmoother_run_althandler8_production(
	uint8_t *source, uint8_t *destination, int32_t width, int32_t height,
	int32_t rowbytes, int32_t tolerance, int32_t x, int32_t y,
	int32_t direction, int32_t scan_type)
{
	PF_EffectWorld src{}, dst{};
	src.data = source; src.width = width; src.height = height; src.rowbytes = rowbytes;
	dst.data = destination; dst.width = width; dst.height = height; dst.rowbytes = rowbytes;
	RenderState state{};
	state.tolerance_lo = tolerance; state.tolerance_hi = tolerance;
	state.tolerance = tolerance; state.threshold = tolerance;
	state.src_world = &src; state.dst_world = &dst;
	uintptr_t neighborhood[9];
	NeighborExtract8(x, y, &state, neighborhood);
	AltHandler8(&state, neighborhood, x, y, static_cast<uint32_t>(direction), scan_type);
}

extern "C" void olmsmoother_run_keymask8_production(
	uint8_t key_red, uint8_t key_green, uint8_t key_blue,
	const uint8_t *input_argb, uint8_t *output_argb)
{
	RenderState state{};
	state.key_a = 0;
	state.key_rg_packed = static_cast<uint16_t>(key_red) |
	                      static_cast<uint16_t>(key_green << 8);
	state.key_b = key_blue;
	ScanlinePixel8_KeyMask(&state, 0, 0,
	                       reinterpret_cast<PF_Pixel8*>(const_cast<uint8_t*>(input_argb)),
	                       reinterpret_cast<PF_Pixel8*>(output_argb));
}

extern "C" int olmsmoother_run_classifier8_production(
	uint8_t *source, int32_t width, int32_t height, int32_t rowbytes,
	int32_t tolerance, int32_t x, int32_t y, int32_t direction)
{
	PF_EffectWorld src{};
	src.data = source; src.width = width; src.height = height; src.rowbytes = rowbytes;
	RenderState state{};
	state.tolerance_lo = tolerance; state.tolerance_hi = tolerance;
	state.tolerance = tolerance; state.threshold = tolerance;
	state.src_world = &src;
	uintptr_t neighborhood[9];
	NeighborExtract8(x, y, &state, neighborhood);
	return Classifier8(&state, x, y, neighborhood, static_cast<uint32_t>(direction));
}

extern "C" int olmsmoother_collect_executor_calls_touching_production(
	uint8_t *source, int32_t width, int32_t height, int32_t rowbytes,
	int32_t tolerance, int32_t target_x, int32_t target_y,
	TouchingExecutorCall8 *calls, int32_t capacity)
{
	PF_EffectWorld src{}, dst{};
	src.data = source; src.width = width; src.height = height; src.rowbytes = rowbytes;
	dst = src;
	RenderState state{};
	state.tolerance_lo = tolerance; state.tolerance_hi = tolerance;
	state.tolerance = tolerance; state.threshold = tolerance;
	state.src_world = &src; state.dst_world = &dst;
	g_touching_calls = calls; g_touching_count = 0; g_touching_capacity = capacity;
	g_touching_x = target_x; g_touching_y = target_y;
	g_source_base = source; g_source_rowbytes = rowbytes;
	g_interp_executor8_test_hook = capture_touching_executor;
	const int directions[4] = {5, 3, 1, 7};
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			g_center_x = x; g_center_y = y;
			uintptr_t neighborhood[9];
			NeighborExtract8(x, y, &state, neighborhood);
			for (int direction : directions) {
				const int scan_type = Classifier8(&state, x, y, neighborhood, direction);
				DispatchDirection8(&state, neighborhood, x, y, direction, scan_type);
			}
		}
	}
	g_interp_executor8_test_hook = nullptr;
	return g_touching_count;
}
