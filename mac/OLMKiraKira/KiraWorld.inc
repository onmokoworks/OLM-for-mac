// Included by OLMKiraKira.cpp inside its anonymous namespace.
// Refusal attribution for the fuzz campaign. When OLM_REFUSAL_TRACE names a
// file, each failing admission guard appends "function:tag". The file is only
// opened on a refusal, and the returned error code and all output bytes are
// identical whether or not tracing is enabled.
static PF_Err KiraRefusal(const char *function, const char *tag, int line, PF_Err err)
{
	const char *path = std::getenv("OLM_REFUSAL_TRACE");
	if (path && path[0]) {
		const int handle = ::open(path, O_WRONLY | O_CREAT | O_APPEND, 0666);
		if (handle >= 0) {
			char entry[384];
			const int length = std::snprintf(entry, sizeof(entry), "%s:%s@%d\n", function, tag, line);
			if (length > 0) {
				const ssize_t written = ::write(handle, entry, (std::size_t)length);
				(void)written;
			}
			::close(handle);
		}
	}
	return err;
}

#define OLM_KIRA_REFUSAL(tag) KiraRefusal(__func__, tag, __LINE__, PF_Err_BAD_CALLBACK_PARAM)
#define OLM_KIRA_ERROR(tag, code) KiraRefusal(__func__, tag, __LINE__, code)



static void KiraDiagnosticLog(const char *format, ...)
{
	const char *path = std::getenv("OLMKIRAKIRA_DIAGNOSTIC_LOG");
	if (!path || !*path || !format) return;
	FILE *file = std::fopen(path, "a");
	if (!file) return;
	va_list arguments;
	va_start(arguments, format);
	std::vfprintf(file, format, arguments);
	va_end(arguments);
	std::fputc('\n', file);
	std::fclose(file);
}

static void KiraDiagnosticWorld(const char *label, const PF_EffectWorld *world)
{
	if (!world) {
		KiraDiagnosticLog("world %s null", label ? label : "?");
		return;
	}
	KiraDiagnosticLog(
		"world %s data=%p width=%ld height=%ld rowbytes=%ld origin=%ld,%ld "
		"extent=%ld,%ld,%ld,%ld flags=%lu",
		label ? label : "?", world->data,
		(long)world->width, (long)world->height, (long)world->rowbytes,
		(long)world->origin_x, (long)world->origin_y,
		(long)world->extent_hint.left, (long)world->extent_hint.top,
		(long)world->extent_hint.right, (long)world->extent_hint.bottom,
		(unsigned long)world->world_flags);
}

constexpr float kFd90RayEpsilon = 0.001f;

struct FloatRGBA {
	float r = 0.0f;
	float g = 0.0f;
	float b = 0.0f;
	float a = 0.0f;
};

struct KiraKiraDebugPoint {
	A_long x = 0;
	A_long y = 0;
};

struct KiraKiraDebugConfig {
	const char *dump_path = nullptr;
	std::vector<KiraKiraDebugPoint> points;
};

static float Clamp01(float v)
{
	return std::min(1.0f, std::max(0.0f, v));
}

static std::vector<KiraKiraDebugPoint> ParseKiraKiraDebugPoints(const char *spec)
{
	std::vector<KiraKiraDebugPoint> points;
	if (!spec || !*spec) return points;
	const char *p = spec;
	while (*p) {
		int x = -1;
		int y = -1;
		int consumed = 0;
		if (std::sscanf(p, "%d,%d%n", &x, &y, &consumed) == 2 && consumed > 0) {
			points.push_back({ (A_long)x, (A_long)y });
			p += consumed;
			while (*p == ';' || *p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') ++p;
		} else {
			break;
		}
	}
	return points;
}

static KiraKiraDebugConfig LoadKiraKiraDebugConfig()
{
	KiraKiraDebugConfig config;
	config.dump_path = std::getenv("OLMKIRAKIRA_DEBUG_DUMP_PATH");
	config.points = ParseKiraKiraDebugPoints(std::getenv("OLMKIRAKIRA_DEBUG_POINTS"));
	if (!config.dump_path || !*config.dump_path || config.points.empty()) {
		config.dump_path = nullptr;
		config.points.clear();
	}
	return config;
}

static bool KiraKiraDebugHasPoint(const KiraKiraDebugConfig &debug, A_long x, A_long y)
{
	for (const KiraKiraDebugPoint &point : debug.points) {
		if (point.x == x && point.y == y) return true;
	}
	return false;
}

static void KiraKiraDebugDumpPoint(
	const KiraKiraDebugConfig &debug,
	short bitdepth,
	A_long width,
	A_long height,
	A_long x,
	A_long y,
	const FloatRGBA &src,
	const FloatRGBA &glow_normalized,
	float glow_alpha_after_opacity,
	const FloatRGBA &out_prequantized)
{
	if (!debug.dump_path || !KiraKiraDebugHasPoint(debug, x, y)) return;
	FILE *fp = std::fopen(debug.dump_path, "a");
	if (!fp) return;
	const A_u_char out8r = static_cast<A_u_char>(std::lround(Clamp01(out_prequantized.r) * 255.0f));
	const A_u_char out8g = static_cast<A_u_char>(std::lround(Clamp01(out_prequantized.g) * 255.0f));
	const A_u_char out8b = static_cast<A_u_char>(std::lround(Clamp01(out_prequantized.b) * 255.0f));
	const A_u_char out8a = static_cast<A_u_char>(std::lround(Clamp01(out_prequantized.a) * 255.0f));
	std::fprintf(
		fp,
		"OLMKIRAKIRA_DEBUG_POINT bitdepth=%d w=%d h=%d x=%d y=%d "
		"src=(%.9g,%.9g,%.9g,%.9g) src_hex=(%a,%a,%a,%a) "
		"glow_norm=(%.9g,%.9g,%.9g,%.9g) glow_norm_hex=(%a,%a,%a,%a) "
		"glow_alpha_after_opacity=%.9g glow_alpha_after_opacity_hex=%a "
		"out_prequantized=(%.9g,%.9g,%.9g,%.9g) out_prequantized_hex=(%a,%a,%a,%a) "
		"out_u8=(%u,%u,%u,%u)\n",
		(int)bitdepth,
		(int)width,
		(int)height,
		(int)x,
		(int)y,
		src.r, src.g, src.b, src.a,
		(double)src.r, (double)src.g, (double)src.b, (double)src.a,
		glow_normalized.r, glow_normalized.g, glow_normalized.b, glow_normalized.a,
		(double)glow_normalized.r, (double)glow_normalized.g, (double)glow_normalized.b, (double)glow_normalized.a,
		glow_alpha_after_opacity,
		(double)glow_alpha_after_opacity,
		out_prequantized.r, out_prequantized.g, out_prequantized.b, out_prequantized.a,
		(double)out_prequantized.r, (double)out_prequantized.g, (double)out_prequantized.b, (double)out_prequantized.a,
		(unsigned int)out8r,
		(unsigned int)out8g,
		(unsigned int)out8b,
		(unsigned int)out8a
	);
	std::fclose(fp);
}

static int Reflect101Index(int i, int n)
{
	if (n <= 1) return 0;
	while (i < 0 || i >= n) {
		if (i < 0) i = -i;
		if (i >= n) i = 2 * n - i - 2;
	}
	return i;
}

static A_long AexRotatedExtent(A_long major, A_long minor, float abs_major, float abs_minor)
{
	return olm::kirakira::rotated_extent(major, minor, abs_major, abs_minor);
}

// PF worlds describe rows in bytes. Copy through an aligned local value:
// the AEX address helpers (1812309f0/a20/a50) add y*rowbytes+x*sizeof(pixel),
// and its readers/writers use unaligned scalar loads/stores. Host padding is
// not a C++ PixelT array and need not preserve PixelT alignment.
template <typename PixelT>
static PixelT LoadWorldPixel(const PF_EffectWorld *world, A_long x, A_long y)
{
	const size_t offset = static_cast<size_t>(y) *
		static_cast<size_t>(world->rowbytes) + static_cast<size_t>(x) * sizeof(PixelT);
	PixelT pixel;
	std::memcpy(&pixel, reinterpret_cast<const unsigned char *>(world->data) + offset,
		sizeof(pixel));
	return pixel;
}

template <typename PixelT>
static void StoreWorldPixel(PF_EffectWorld *world, A_long x, A_long y, const PixelT &pixel)
{
	const size_t offset = static_cast<size_t>(y) *
		static_cast<size_t>(world->rowbytes) + static_cast<size_t>(x) * sizeof(PixelT);
	std::memcpy(reinterpret_cast<unsigned char *>(world->data) + offset, &pixel,
		sizeof(pixel));
}

template <typename PixelT>
struct PixelTraits;

template <>
struct PixelTraits<PF_Pixel8> {
	static FloatRGBA Read(const PF_Pixel8 &p) {
		// The typed Windows owners materialize a FLOAT32 reciprocal once and
		// multiply each byte lane.  Division is mathematically equivalent but
		// differs by one ULP for a bounded set of byte values.
		constexpr float kByteToFloat = 1.0f / 255.0f;
		return {
			p.red * kByteToFloat,
			p.green * kByteToFloat,
			p.blue * kByteToFloat,
			p.alpha * kByteToFloat
		};
	}
	static PF_Pixel8 Write(const FloatRGBA &p) {
		PF_Pixel8 out;
		out.alpha = static_cast<A_u_char>(std::lround(Clamp01(p.a) * 255.0f));
		out.red   = static_cast<A_u_char>(std::lround(Clamp01(p.r) * 255.0f));
		out.green = static_cast<A_u_char>(std::lround(Clamp01(p.g) * 255.0f));
		out.blue  = static_cast<A_u_char>(std::lround(Clamp01(p.b) * 255.0f));
		return out;
	}
	static PF_Pixel8 WriteAexTruncate(const FloatRGBA &p) {
		PF_Pixel8 out;
		out.alpha = static_cast<A_u_char>(olm::kirakira::truncate_merge2_channel(p.a, 255.0f));
		out.red   = static_cast<A_u_char>(olm::kirakira::truncate_merge2_channel(p.r, 255.0f));
		out.green = static_cast<A_u_char>(olm::kirakira::truncate_merge2_channel(p.g, 255.0f));
		out.blue  = static_cast<A_u_char>(olm::kirakira::truncate_merge2_channel(p.b, 255.0f));
		return out;
	}
};

template <>
struct PixelTraits<PF_Pixel16> {
	static FloatRGBA Read(const PF_Pixel16 &p) {
		return {
			p.red / static_cast<float>(PF_MAX_CHAN16),
			p.green / static_cast<float>(PF_MAX_CHAN16),
			p.blue / static_cast<float>(PF_MAX_CHAN16),
			p.alpha / static_cast<float>(PF_MAX_CHAN16)
		};
	}
	static PF_Pixel16 Write(const FloatRGBA &p) {
		PF_Pixel16 out;
		out.alpha = static_cast<A_u_short>(std::lround(Clamp01(p.a) * PF_MAX_CHAN16));
		out.red   = static_cast<A_u_short>(std::lround(Clamp01(p.r) * PF_MAX_CHAN16));
		out.green = static_cast<A_u_short>(std::lround(Clamp01(p.g) * PF_MAX_CHAN16));
		out.blue  = static_cast<A_u_short>(std::lround(Clamp01(p.b) * PF_MAX_CHAN16));
		return out;
	}
	static PF_Pixel16 WriteAexTruncate(const FloatRGBA &p) {
		PF_Pixel16 out;
		out.alpha = static_cast<A_u_short>(olm::kirakira::truncate_merge2_channel(p.a, 32768.0f));
		out.red   = static_cast<A_u_short>(olm::kirakira::truncate_merge2_channel(p.r, 32768.0f));
		out.green = static_cast<A_u_short>(olm::kirakira::truncate_merge2_channel(p.g, 32768.0f));
		out.blue  = static_cast<A_u_short>(olm::kirakira::truncate_merge2_channel(p.b, 32768.0f));
		return out;
	}
};

template <>
struct PixelTraits<PF_PixelFloat> {
	static FloatRGBA Read(const PF_PixelFloat &p) {
		return {p.red, p.green, p.blue, p.alpha};
	}
	static PF_PixelFloat Write(const FloatRGBA &p) {
		PF_PixelFloat out;
		out.alpha = Clamp01(p.a);
		out.red   = Clamp01(p.r);
		out.green = Clamp01(p.g);
		out.blue  = Clamp01(p.b);
		return out;
	}
	static PF_PixelFloat WriteAexTruncate(const FloatRGBA &p) { return Write(p); }
};

static size_t PixelSizeForFormat(PF_PixelFormat format)
{
	switch (format) {
		case PF_PixelFormat_ARGB32:  return sizeof(PF_Pixel8);
		case PF_PixelFormat_ARGB64:  return sizeof(PF_Pixel16);
		case PF_PixelFormat_ARGB128: return sizeof(PF_PixelFloat);
		default: return 0;
	}
}

static short BitDepthForFormat(PF_PixelFormat format)
{
	switch (format) {
		case PF_PixelFormat_ARGB32:  return 8;
		case PF_PixelFormat_ARGB64:  return 16;
		case PF_PixelFormat_ARGB128: return 32;
		default: return 0;
	}
}

static PF_Err GetKiraPixelFormats(
	PF_InData *in_data,
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	PF_PixelFormat *input_format,
	PF_PixelFormat *output_format)
{
	if (!in_data || !input || !output || !input_format || !output_format ||
		!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
		!in_data->pica_basicP->ReleaseSuite) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const void *suite_ptr = nullptr;
	PF_Err err = PF_Err_NONE;
	bool acquired = false;
	try {
		const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
			kPFWorldSuite, kPFWorldSuiteVersion2, &suite_ptr);
		if (acquire_err != kSPNoError) {
			err = static_cast<PF_Err>(acquire_err);
		} else {
			acquired = true;
			const PF_WorldSuite2 *world_suite =
				reinterpret_cast<const PF_WorldSuite2 *>(suite_ptr);
			if (!world_suite || !world_suite->PF_GetPixelFormat) {
				err = PF_Err_BAD_CALLBACK_PARAM;
			} else {
				err = world_suite->PF_GetPixelFormat(input, input_format);
				if (!err) err = world_suite->PF_GetPixelFormat(output, output_format);
			}
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	if (acquired) {
		try {
			const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
				kPFWorldSuite, kPFWorldSuiteVersion2);
			if (!err && release_err != kSPNoError) {
				err = static_cast<PF_Err>(release_err);
			}
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = PF_Err_OUT_OF_MEMORY;
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
	return err;
}

static bool WorldLayoutIsSafe(const PF_EffectWorld *world, size_t pixel_size)
{
	if (!world || !world->data || pixel_size == 0 ||
		world->width <= 0 || world->height <= 0 || world->rowbytes <= 0) {
		return false;
	}
	const int64_t active_rowbytes =
		static_cast<int64_t>(world->width) * static_cast<int64_t>(pixel_size);
	if (active_rowbytes <= 0 ||
		active_rowbytes > static_cast<int64_t>(world->rowbytes)) {
		return false;
	}
	// Byte copies admit unaligned bases and arbitrary positive byte strides.
	const uint64_t last_row_offset =
		static_cast<uint64_t>(world->height - 1) *
		static_cast<uint64_t>(world->rowbytes);
	const uintptr_t begin = reinterpret_cast<uintptr_t>(world->data);
	const uint64_t available = static_cast<uint64_t>(UINTPTR_MAX - begin);
	return last_row_offset <= available &&
		static_cast<uint64_t>(active_rowbytes) <= available - last_row_offset;
}

static PF_Err ValidateWorldPair(
	PF_InData *in_data,
	PF_OutData *out_data,
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	short declared_bitdepth,
	PF_PixelFormat *format_out,
	bool smart_geometry = false)
{
	if (!in_data || !out_data || !input || !output || !format_out)
		return OLM_KIRA_REFUSAL("world-null-argument");
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	PF_Err err = GetKiraPixelFormats(
		in_data, input, output, &input_format, &output_format);
	if (err) return err;
	if (input_format != output_format) return OLM_KIRA_REFUSAL("world-format-mismatch");
	const size_t pixel_size = PixelSizeForFormat(input_format);
	const short format_bitdepth = BitDepthForFormat(input_format);
	if (!pixel_size || !format_bitdepth ||
		(declared_bitdepth != 0 && declared_bitdepth != format_bitdepth) ||
		(!smart_geometry && (input->width != output->width || input->height != output->height)) ||
		!WorldLayoutIsSafe(input, pixel_size) ||
		!WorldLayoutIsSafe(output, pixel_size)) {
		return OLM_KIRA_REFUSAL("world-layout-unsafe");
	}
	const uint64_t pixel_count = static_cast<uint64_t>(input->width) *
		static_cast<uint64_t>(input->height);
	if (pixel_count > static_cast<uint64_t>(SIZE_MAX / sizeof(FloatRGBA)))
		return OLM_KIRA_ERROR("world-allocation-overflow", PF_Err_OUT_OF_MEMORY);
	*format_out = input_format;
	return PF_Err_NONE;
}
