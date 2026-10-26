// Optional point diagnostics; included after RadialMath.inc.
struct RadialBlurDebugPoint {
	A_long x = 0;
	A_long y = 0;
};

struct RadialBlurDebugConfig {
	const char *dump_path = nullptr;
	std::vector<RadialBlurDebugPoint> points;
	bool force_scalar_producer = false;
};

static std::vector<RadialBlurDebugPoint> ParseRadialBlurDebugPoints(const char *spec)
{
	std::vector<RadialBlurDebugPoint> points;
	if (!spec || !*spec) return points;
	const char *cursor = spec;
	while (*cursor) {
		int x = -1;
		int y = -1;
		int consumed = 0;
		if (std::sscanf(cursor, "%d,%d%n", &x, &y, &consumed) == 2 && consumed > 0) {
			points.push_back({(A_long)x, (A_long)y});
			cursor += consumed;
			while (*cursor == ';' || *cursor == ' ' || *cursor == '\t' || *cursor == '\n' || *cursor == '\r') ++cursor;
		} else {
			break;
		}
	}
	return points;
}

static RadialBlurDebugConfig LoadRadialBlurDebugConfig()
{
	RadialBlurDebugConfig config;
	config.dump_path = std::getenv("OLMRADIALBLUR_DEBUG_DUMP_PATH");
	config.points = ParseRadialBlurDebugPoints(std::getenv("OLMRADIALBLUR_DEBUG_POINTS"));
	const char *force_scalar = std::getenv("OLMRADIALBLUR_FORCE_SCALAR_PRODUCER");
	config.force_scalar_producer = force_scalar && (*force_scalar == '1' || *force_scalar == 'y' || *force_scalar == 'Y');
	if (!config.dump_path || !*config.dump_path || config.points.empty()) {
		config.dump_path = nullptr;
		config.points.clear();
	}
	return config;
}

static bool RadialBlurDebugHasPoint(const RadialBlurDebugConfig &debug, A_long x, A_long y)
{
	for (const RadialBlurDebugPoint &point : debug.points) {
		if (point.x == x && point.y == y) return true;
	}
	return false;
}

static void DumpRadialBlurDebugPoint(
	const RadialBlurDebugConfig &debug,
	const char *kind,
	A_long width,
	A_long height,
	A_long x,
	A_long y,
	float radius_index,
	float angle_index,
	float fx,
	float fy,
	A_long sample_x0,
	A_long sample_x1,
	A_long sample_y0,
	A_long sample_y1,
	const float sample_rgba[4],
	const A_u_char sample_u8[4],
	float alpha,
	float validity_alpha,
	float brightness_gain,
	const float accum_rgba[4],
	const float normalized_rgba[4],
	const float cell_valid[4],
	const float cell_alpha[4],
	const float cell_rgb[4][3],
	const float src_cell_rgba[4][4])
{
	if (!debug.dump_path || !RadialBlurDebugHasPoint(debug, x, y)) return;
	FILE *fp = std::fopen(debug.dump_path, "a");
	if (!fp) return;
	std::fprintf(
		fp,
		"OLMRADIALBLUR_DEBUG_POINT kind=%s w=%d h=%d x=%d y=%d "
		"radius_index=%.9g angle_index=%.9g fx=%.9g fy=%.9g "
		"indices=(%d,%d,%d,%d) "
		"sample_rgba=(%.9g,%.9g,%.9g,%.9g) sample_rgba_hex=(%a,%a,%a,%a) "
		"sample_u8=(%u,%u,%u,%u) "
		"alpha=%.9g alpha_hex=%a validity_alpha=%.9g validity_alpha_hex=%a "
		"brightness_gain=%.9g "
		"accum_rgba=(%.9g,%.9g,%.9g,%.9g) accum_rgba_hex=(%a,%a,%a,%a) "
		"normalized_rgba=(%.9g,%.9g,%.9g,%.9g) normalized_rgba_hex=(%a,%a,%a,%a) "
		"cell_valid=(%.9g,%.9g,%.9g,%.9g) "
		"cell_alpha=(%.9g,%.9g,%.9g,%.9g) "
		"cell_rgb=((%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g)) "
		"src_cell_rgba=((%.9g,%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g,%.9g),(%.9g,%.9g,%.9g,%.9g))\n",
		kind,
		(int)width,
		(int)height,
		(int)x,
		(int)y,
		radius_index,
		angle_index,
		fx,
		fy,
		(int)sample_x0,
		(int)sample_x1,
		(int)sample_y0,
		(int)sample_y1,
		sample_rgba[0], sample_rgba[1], sample_rgba[2], sample_rgba[3],
		(double)sample_rgba[0], (double)sample_rgba[1], (double)sample_rgba[2], (double)sample_rgba[3],
		(unsigned int)sample_u8[0], (unsigned int)sample_u8[1], (unsigned int)sample_u8[2], (unsigned int)sample_u8[3],
		alpha,
		(double)alpha,
		validity_alpha,
		(double)validity_alpha,
		brightness_gain,
		accum_rgba[0], accum_rgba[1], accum_rgba[2], accum_rgba[3],
		(double)accum_rgba[0], (double)accum_rgba[1], (double)accum_rgba[2], (double)accum_rgba[3],
		normalized_rgba[0], normalized_rgba[1], normalized_rgba[2], normalized_rgba[3],
		(double)normalized_rgba[0], (double)normalized_rgba[1], (double)normalized_rgba[2], (double)normalized_rgba[3],
		cell_valid[0], cell_valid[1], cell_valid[2], cell_valid[3],
		cell_alpha[0], cell_alpha[1], cell_alpha[2], cell_alpha[3],
		cell_rgb[0][0], cell_rgb[0][1], cell_rgb[0][2],
		cell_rgb[1][0], cell_rgb[1][1], cell_rgb[1][2],
		cell_rgb[2][0], cell_rgb[2][1], cell_rgb[2][2],
		cell_rgb[3][0], cell_rgb[3][1], cell_rgb[3][2],
		src_cell_rgba[0][0], src_cell_rgba[0][1], src_cell_rgba[0][2], src_cell_rgba[0][3],
		src_cell_rgba[1][0], src_cell_rgba[1][1], src_cell_rgba[1][2], src_cell_rgba[1][3],
		src_cell_rgba[2][0], src_cell_rgba[2][1], src_cell_rgba[2][2], src_cell_rgba[2][3],
		src_cell_rgba[3][0], src_cell_rgba[3][1], src_cell_rgba[3][2], src_cell_rgba[3][3]);
	std::fclose(fp);
}

#ifndef NDEBUG
template<typename SampleFn>
static void DumpRadialBlurCoordinateRawBits(
	const RadialBlurDebugConfig &debug,
	A_long width,
	A_long height,
	A_long x,
	A_long y,
	float production_radius_raw,
	float production_angle_raw,
	float production_radius_index,
	float production_angle_index,
	float production_radius_fraction,
	float production_angle_fraction,
	A_long production_radius0,
	A_long production_radius1,
	A_long production_angle0,
	A_long production_angle1,
	const RadialBlurAEXCoordinateCandidate &candidate,
	A_long radius_count,
	A_long angle_count,
	const SampleFn &sample)
{
	if (!debug.dump_path || y != 0 || x < 0 || x > 31 || !RadialBlurDebugHasPoint(debug, x, y)) return;
	FILE *fp = std::fopen(debug.dump_path, "a");
	if (!fp) return;
	std::fprintf(fp,
		"OLMRADIALBLUR_DEBUG_COORD_RAW {\"kind\":\"zoom\",\"width\":%d,\"height\":%d,\"x\":%d,\"y\":%d,"
		"\"production\":{\"radius_raw_bits\":\"0x%08x\",\"angle_raw_bits\":\"0x%08x\","
		"\"radius_index_bits\":\"0x%08x\",\"angle_index_bits\":\"0x%08x\","
		"\"radius_fraction_bits\":\"0x%08x\",\"angle_fraction_bits\":\"0x%08x\","
		"\"radius_indices\":[%d,%d],\"angle_indices\":[%d,%d],\"cell_indices\":[[%d,%d],[%d,%d],[%d,%d],[%d,%d]],\"cell_rgba_bits\":[",
		(int)width, (int)height, (int)x, (int)y,
		(unsigned int)RadialF32Bits(production_radius_raw), (unsigned int)RadialF32Bits(production_angle_raw),
		(unsigned int)RadialF32Bits(production_radius_index), (unsigned int)RadialF32Bits(production_angle_index),
		(unsigned int)RadialF32Bits(production_radius_fraction), (unsigned int)RadialF32Bits(production_angle_fraction),
		(int)production_radius0, (int)production_radius1, (int)production_angle0, (int)production_angle1,
		(int)production_angle0, (int)production_radius0, (int)production_angle0, (int)production_radius1,
		(int)production_angle1, (int)production_radius0, (int)production_angle1, (int)production_radius1);
	const A_long production_cells[4][2] = {
		{production_radius0, production_angle0}, {production_radius1, production_angle0},
		{production_radius0, production_angle1}, {production_radius1, production_angle1}
	};
	for (int cell = 0; cell < 4; ++cell) {
		if (cell) std::fputc(',', fp);
		std::fprintf(fp, "[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"]",
			(unsigned int)RadialF32Bits(sample(production_cells[cell][0], production_cells[cell][1], 0)),
			(unsigned int)RadialF32Bits(sample(production_cells[cell][0], production_cells[cell][1], 1)),
			(unsigned int)RadialF32Bits(sample(production_cells[cell][0], production_cells[cell][1], 2)),
			(unsigned int)RadialF32Bits(sample(production_cells[cell][0], production_cells[cell][1], 3)));
	}
	std::fprintf(fp,
		"]},\"aex_f32_candidate\":{\"operation_bits\":{"
		"\"dy\":\"0x%08x\",\"dx\":\"0x%08x\",\"cos_dy\":\"0x%08x\",\"sin_dx\":\"0x%08x\","
		"\"ey_numerator\":\"0x%08x\",\"ey\":\"0x%08x\",\"sin_dy\":\"0x%08x\",\"cos_dx\":\"0x%08x\","
		"\"ex\":\"0x%08x\",\"ex_squared\":\"0x%08x\",\"ey_squared\":\"0x%08x\",\"radius_squared\":\"0x%08x\"},"
		"\"radius_raw_bits\":\"0x%08x\",\"angle_raw_bits\":\"0x%08x\","
		"\"radius_index_bits\":\"0x%08x\",\"angle_index_bits\":\"0x%08x\","
		"\"radius_fraction_bits\":\"0x%08x\",\"angle_fraction_bits\":\"0x%08x\","
		"\"radius_indices\":[%d,%d],\"angle_indices\":[%d,%d],\"cell_indices\":[[%d,%d],[%d,%d],[%d,%d],[%d,%d]],",
		(unsigned int)RadialF32Bits(candidate.dy), (unsigned int)RadialF32Bits(candidate.dx),
		(unsigned int)RadialF32Bits(candidate.cos_dy), (unsigned int)RadialF32Bits(candidate.sin_dx),
		(unsigned int)RadialF32Bits(candidate.ey_numerator), (unsigned int)RadialF32Bits(candidate.ey),
		(unsigned int)RadialF32Bits(candidate.sin_dy), (unsigned int)RadialF32Bits(candidate.cos_dx),
		(unsigned int)RadialF32Bits(candidate.ex), (unsigned int)RadialF32Bits(candidate.ex_squared),
		(unsigned int)RadialF32Bits(candidate.ey_squared), (unsigned int)RadialF32Bits(candidate.radius_squared),
		(unsigned int)RadialF32Bits(candidate.radius_raw), (unsigned int)RadialF32Bits(candidate.angle_raw),
		(unsigned int)RadialF32Bits(candidate.radius_index), (unsigned int)RadialF32Bits(candidate.angle_index),
		(unsigned int)RadialF32Bits(candidate.radius_fraction), (unsigned int)RadialF32Bits(candidate.angle_fraction),
		(int)candidate.radius0, (int)candidate.radius1, (int)candidate.angle0, (int)candidate.angle1,
		(int)candidate.angle0, (int)candidate.radius0, (int)candidate.angle0, (int)candidate.radius1,
		(int)candidate.angle1, (int)candidate.radius0, (int)candidate.angle1, (int)candidate.radius1);
	const bool candidate_cells_available = candidate.radius0 >= 0 && candidate.radius1 < radius_count &&
		candidate.angle0 >= 0 && candidate.angle0 < angle_count && candidate.angle1 >= 0 && candidate.angle1 < angle_count;
	std::fprintf(fp, "\"cell_values_available\":%s,\"cell_rgba_bits\":[", candidate_cells_available ? "true" : "false");
	if (candidate_cells_available) {
		const A_long candidate_cells[4][2] = {
			{candidate.radius0, candidate.angle0}, {candidate.radius1, candidate.angle0},
			{candidate.radius0, candidate.angle1}, {candidate.radius1, candidate.angle1}
		};
		for (int cell = 0; cell < 4; ++cell) {
			if (cell) std::fputc(',', fp);
			std::fprintf(fp, "[\"0x%08x\",\"0x%08x\",\"0x%08x\",\"0x%08x\"]",
				(unsigned int)RadialF32Bits(sample(candidate_cells[cell][0], candidate_cells[cell][1], 0)),
				(unsigned int)RadialF32Bits(sample(candidate_cells[cell][0], candidate_cells[cell][1], 1)),
				(unsigned int)RadialF32Bits(sample(candidate_cells[cell][0], candidate_cells[cell][1], 2)),
				(unsigned int)RadialF32Bits(sample(candidate_cells[cell][0], candidate_cells[cell][1], 3)));
		}
	}
	std::fprintf(fp, "]}}\n");
	std::fclose(fp);
}
#endif
