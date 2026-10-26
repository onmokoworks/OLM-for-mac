// World payload validation and optional diagnostic capture; included by OLMRadialBlur.cpp.
static bool RadialPayloadSpan(const PF_EffectWorld *world,
	                          std::uintptr_t *begin,
	                          std::uintptr_t *end)
{
	if (!world || !world->data || !begin || !end || world->rowbytes <= 0 ||
		world->height <= 0) return false;
	const std::size_t rowbytes = static_cast<std::size_t>(world->rowbytes);
	const std::size_t height = static_cast<std::size_t>(world->height);
	if (rowbytes > std::numeric_limits<std::size_t>::max() / height) return false;
	const std::size_t bytes = rowbytes * height;
	const std::uintptr_t first = reinterpret_cast<std::uintptr_t>(world->data);
	if (bytes > std::numeric_limits<std::uintptr_t>::max() - first) return false;
	*begin = first;
	*end = first + bytes;
	return true;
}

static bool RadialPayloadsDisjoint(const PF_EffectWorld *first,
	                               const PF_EffectWorld *second)
{
	std::uintptr_t first_begin = 0, first_end = 0, second_begin = 0, second_end = 0;
	return RadialPayloadSpan(first, &first_begin, &first_end) &&
		RadialPayloadSpan(second, &second_begin, &second_end) &&
		(first_end <= second_begin || second_end <= first_begin);
}

static bool RadialActiveRowBytes(short bitdepth, A_long width, std::size_t *bytes)
{
	if (!bytes || width <= 0) return false;
	std::size_t pixel_bytes = 0;
	switch (bitdepth) {
	case 8: pixel_bytes = sizeof(PF_Pixel8); break;
	case 16: pixel_bytes = sizeof(PF_Pixel16); break;
	case 32: pixel_bytes = sizeof(PF_PixelFloat); break;
	default: return false;
	}
	const std::size_t w = static_cast<std::size_t>(width);
	if (w > std::numeric_limits<std::size_t>::max() / pixel_bytes) return false;
	*bytes = w * pixel_bytes;
	return true;
}

static void DeletePreRenderData(void *data)
{
	delete reinterpret_cast<PreRenderData *>(data);
}

#if defined(OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE)
// Diagnostic builds only. The destination directory must already exist and
// be explicitly injected through OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE_DIR.
// Fixed filenames intentionally make concurrent/repeated capture ambiguous
// and therefore fail closed rather than silently mixing render invocations.
static PF_Err CaptureDiagnosticPF32World(
	const char *stage,
	const PF_EffectWorld *world,
	const OLMRadialBlurInfo &info,
	short bitdepth)
{
	const char *directory = std::getenv("OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE_DIR");
	if (!directory || !directory[0] || !stage || !world || !world->data || bitdepth != 32 ||
		world->width != 1920 || world->height != 1080 ||
		world->rowbytes < world->width * (A_long)sizeof(PF_PixelFloat) ||
		info.blur_type != 1 || info.center_x != 960.0 || info.center_y != 540.0 ||
		info.outer_strength != 1717 || info.outer_offset_mode != 1 || info.outer_offset != 0 ||
		info.outer_edge_fade != 0 || info.inner_strength != 0 || info.inner_offset_mode != 1 ||
		info.inner_offset != 0 || info.inner_edge_fade != 0 || info.repeat_border == FALSE ||
		info.ratio != 1.0 || info.angle_deg != 0.0 || info.quality != 5.0 ||
		info.brightness_gain != 1.0 || info.size_variation != 0.0 ||
		info.noise_variation != 0.0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	char raw_path[4096];
	char metadata_path[4096];
	const int raw_length = std::snprintf(raw_path, sizeof(raw_path), "%s/%s.argb128.rows", directory, stage);
	const int metadata_length = std::snprintf(metadata_path, sizeof(metadata_path), "%s/%s.json", directory, stage);
	if (raw_length <= 0 || raw_length >= (int)sizeof(raw_path) ||
		metadata_length <= 0 || metadata_length >= (int)sizeof(metadata_path)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	auto exists = [](const char *path) {
		FILE *file = std::fopen(path, "rb");
		if (!file) return false;
		std::fclose(file);
		return true;
	};
	if (exists(raw_path) || exists(metadata_path)) return PF_Err_BAD_CALLBACK_PARAM;
	FILE *raw = std::fopen(raw_path, "wb");
	if (!raw) return PF_Err_INTERNAL_STRUCT_DAMAGED;
	const A_u_char *row = reinterpret_cast<const A_u_char *>(world->data);
	bool write_ok = true;
	for (A_long y = 0; y < world->height; ++y) {
		if (std::fwrite(row, 1, (size_t)world->rowbytes, raw) != (size_t)world->rowbytes) {
			write_ok = false;
			break;
		}
		row += world->rowbytes;
	}
	write_ok = std::fclose(raw) == 0 && write_ok;
	if (!write_ok) return PF_Err_INTERNAL_STRUCT_DAMAGED;
	FILE *metadata = std::fopen(metadata_path, "wb");
	if (!metadata) return PF_Err_INTERNAL_STRUCT_DAMAGED;
	const int count = std::fprintf(metadata,
		"{\n  \"schema\": \"olmradialblur-pf32-world-capture/1\",\n"
		"  \"stage\": \"%s\",\n  \"pixel_format\": \"PF_PixelFormat_ARGB128\",\n"
		"  \"channel_memory_order\": \"ARGB\",\n  \"row_storage\": \"full_positive_rowbytes_including_padding\",\n"
		"  \"width\": %d,\n  \"height\": %d,\n  \"rowbytes\": %d,\n"
		"  \"extent_hint\": [%d, %d, %d, %d],\n  \"raw_bytes\": %lld\n}\n",
		stage, (int)world->width, (int)world->height, (int)world->rowbytes,
		(int)world->extent_hint.left, (int)world->extent_hint.top,
		(int)world->extent_hint.right, (int)world->extent_hint.bottom,
		(long long)world->rowbytes * world->height);
	const bool metadata_ok = count > 0 && std::fclose(metadata) == 0;
	return metadata_ok ? PF_Err_NONE : PF_Err_INTERNAL_STRUCT_DAMAGED;
}
#endif

