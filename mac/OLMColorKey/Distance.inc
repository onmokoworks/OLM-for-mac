// AEX city-block/chessboard scan cap and first nonseed (0x5c90 / 0x66f0).
static constexpr float kDistanceCap = 4000.0f, kFirstNonseed = 3999.0f;
// Port EDT sentinels; finite stand-ins for absent sites and parabola boundaries.
static constexpr float kSquaredDistanceInfinity = 1.0e9f, kEnvelopeInfinity = 1.0e20f;
// Included by OLMColorKey.cpp; preserves the single translation unit.
static std::vector<float> L1DistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, float dx = 1.0f, float dy = 1.0f)
{
	// Native city-block/chessboard scans cap the plane at 4000 and
	// initialize the first nonseed to cap - 1, even when there are no seeds.
	std::vector<float> d((size_t)w * (size_t)h, kDistanceCap);
	for (A_long i = 0; i < w * h; ++i) {
		if (mask[i]) d[i] = 0.0f;
	}
	if (!mask[0]) d[0] = kFirstNonseed;
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const A_long i = y * w + x;
			if (x > 0) d[i] = std::min(d[i], d[i - 1] + dx);
			if (y > 0) d[i] = std::min(d[i], d[i - w] + dy);
		}
	}
	for (A_long x = w - 2; x >= 0; --x) {
		const A_long i = (h - 1) * w + x;
		d[i] = std::min(d[i], d[i + 1] + dx);
	}
	// 0x5c90..0x5cfe: the cached output pointer still denotes x+1
	// when MINSS reads it. XMM6 carries the candidate, not the stored minimum.
	for (A_long y = h - 2; y >= 0; --y) {
		A_long i = y * w + w - 1;
		float right = std::min(kDistanceCap, d[i + w] + dy);
		d[i] = std::min(d[i], right);
		for (A_long x = w - 2; x >= 0; --x) {
			i = y * w + x;
			right = std::min(kDistanceCap, std::min(std::min(d[i + w], d[i + 1]) + dy, right + dx));
			d[i] = std::min(d[i], right);
		}
	}
	return d;
}

static std::vector<float> ChessboardDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, const std::vector<float> *initial = nullptr, float dx = 1.0f, float dy = 1.0f)
{
	if (w == 1) {
		// FUN_1800066f0/6e20/7550 visits both row edges even for one column.
		// Its x=1/-1 float pointers alias the next/previous contiguous row.
		// Reproduce that scan in bounded storage with the zeroed native scratch
		// plane; the ordinary eight-neighbor transform gives different results.
		std::vector<float> d = initial && initial->size() == (size_t)h
            ? *initial : std::vector<float>((size_t)h, 0.0f);
		d[0] = mask[0] ? 0.0f : kFirstNonseed;
		auto read = [&](A_long y) { return y >= 0 && y < h ? d[(size_t)y] : 0.0f; };
		for (A_long y = 1; y < h; ++y) {
			float left = mask[(size_t)y] ? 0.0f : std::min(kDistanceCap, std::min(read(y - 1), read(y)) + dy);
			d[(size_t)y] = mask[(size_t)y] ? 0.0f :
			    std::min(kDistanceCap, std::min(left + dx, std::min(read(y - 1), read(y - 2)) + dy));
		}
		for (A_long y = h - 2; y >= 0; --y) {
			float right = std::min(read(y + 1), read(y)) + dy;
			d[(size_t)y] = std::min(read(y), right);
			float left = std::min(std::min(read(y + 1), read(y + 2)), read(y)) + dy;
			d[(size_t)y] = std::min(read(y), std::min(left, right + dx));
		}
		return d;
	}

	// Native city-block/chessboard scans cap the plane at 4000 and
	// initialize the first nonseed to cap - 1, even when there are no seeds.
	std::vector<float> d((size_t)w * (size_t)h, kDistanceCap);
	for (A_long i = 0; i < w * h; ++i) {
		if (mask[i]) d[i] = 0.0f;
	}
	if (!mask[0]) d[0] = kFirstNonseed;
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			A_long i = y * w + x;
			if (x > 0) d[i] = std::min(d[i], d[i - 1] + dx);
			if (y > 0) d[i] = std::min(d[i], d[i - w] + dy);
			if (x > 0 && y > 0) d[i] = std::min(d[i], d[i - w - 1] + dy);
			if (x + 1 < w && y > 0) d[i] = std::min(d[i], d[i - w + 1] + dy);
		}
	}
	for (A_long x = w - 2; x >= 0; --x) {
		const A_long i = (h - 1) * w + x;
		d[i] = std::min(d[i], d[i + 1] + dx);
	}
	// 0x6be0..0x6dad carries the candidate in XMM6 before MINSS with
	// the current pixel, and the cached output pointer still denotes x+1.
	// Carrying the stored minimum changes asymmetric steps.
	for (A_long y = h - 2; y >= 0; --y) {
		A_long i = y * w + w - 1;
		float right = std::min(kDistanceCap, std::min(d[i + w], d[i + w - 1]) + dy);
		d[i] = std::min(d[i], right);
		for (A_long x = w - 2; x >= 0; --x) {
			i = y * w + x;
			float below = std::min(d[i + w], d[i + w + 1]);
			if (x > 0) below = std::min(below, d[i + w - 1]);
			right = std::min(kDistanceCap, std::min(std::min(below, d[i + 1]) + dy, right + dx));
			d[i] = std::min(d[i], right);
		}
	}
	return d;
}

static inline float EdtSquare(float x)
{
	return x * x;
}

static std::vector<float> Edt1D(const std::vector<float> &f, A_long n, float step = 1.0f)
{
	std::vector<A_long> sites;
	sites.reserve((size_t)n);
	for (A_long i = 0; i < n; ++i) {
		if (f[(size_t)i] < kSquaredDistanceInfinity * 0.5f) sites.push_back(i);
	}
	std::vector<float> d((size_t)n, kSquaredDistanceInfinity);
	if (sites.empty()) return d;

	std::vector<A_long> envelope_sites(sites.size());
	std::vector<float> breakpoints(sites.size() + 1);
	A_long envelope_index = 0;
	envelope_sites[0] = sites[0];
	breakpoints[0] = -kEnvelopeInfinity;
	breakpoints[1] = kEnvelopeInfinity;
	for (size_t site_index = 1; site_index < sites.size(); ++site_index) {
		A_long query = sites[site_index];
		float intersection = 0.0f;
		while (true) {
			A_long vk = envelope_sites[(size_t)envelope_index];
			intersection = ((f[(size_t)query] + (EdtSquare((float)query) * step * step)) -
			     (f[(size_t)vk] + (EdtSquare((float)vk) * step * step))) /
			    (2.0f * (float)(query - vk) * step) * (1.0f / step);
			if (intersection > breakpoints[(size_t)envelope_index]) break;
			if (envelope_index == 0) break;
			--envelope_index;
		}
		if (intersection <= breakpoints[(size_t)envelope_index]) {
			envelope_index = 0;
		} else {
			++envelope_index;
		}
		envelope_sites[(size_t)envelope_index] = query;
		breakpoints[(size_t)envelope_index] = intersection;
		breakpoints[(size_t)envelope_index + 1] = kEnvelopeInfinity;
	}
	envelope_index = 0;
	for (A_long query = 0; query < n; ++query) {
		while (breakpoints[(size_t)envelope_index + 1] < (float)query) ++envelope_index;
		A_long vk = envelope_sites[(size_t)envelope_index];
		d[(size_t)query] = (EdtSquare((float)(query - vk)) * step * step) + f[(size_t)vk];
	}
	return d;
}

static std::vector<float> EuclideanSquaredDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, float dx = 1.0f, float dy = 1.0f)
{
	std::vector<float> tmp((size_t)w * (size_t)h);
	std::vector<float> f((size_t)std::max(w, h));
	for (A_long x = 0; x < w; ++x) {
		for (A_long y = 0; y < h; ++y) f[(size_t)y] = mask[(size_t)y * (size_t)w + (size_t)x] ? 0.0f : kSquaredDistanceInfinity;
		std::vector<float> col = Edt1D(f, h, dy);
		for (A_long y = 0; y < h; ++y) tmp[(size_t)y * (size_t)w + (size_t)x] = col[(size_t)y];
	}
	std::vector<float> out((size_t)w * (size_t)h);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) f[(size_t)x] = tmp[(size_t)y * (size_t)w + (size_t)x];
		std::vector<float> row = Edt1D(f, w, dx);
		for (A_long x = 0; x < w; ++x) out[(size_t)y * (size_t)w + (size_t)x] = row[(size_t)x];
	}
	return out;
}

static std::vector<float> EuclideanDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, float dx = 1.0f, float dy = 1.0f)
{
	std::vector<float> out = EuclideanSquaredDistanceTo(mask, w, h, dx, dy);
	for (float &value : out) value = std::sqrt(value);
	return out;
}

static std::vector<float> MatteDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, A_long distance_type, float dx = 1.0f, float dy = 1.0f)
{
	if (distance_type == 1) return ChessboardDistanceTo(mask, w, h, nullptr, dx, dy);
	if (distance_type == 3) return EuclideanDistanceTo(mask, w, h, dx, dy);
	return L1DistanceTo(mask, w, h, dx, dy);
}

static std::vector<float> EdgeBlurDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, A_long distance_type, float dx = 1.0f, float dy = 1.0f)
{
	return MatteDistanceTo(mask, w, h, distance_type, dx, dy);
}

static std::vector<u_char> Boundary8(const std::vector<u_char> &mask, A_long w, A_long h)
{
	std::vector<u_char> out((size_t)w * (size_t)h, 0);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const A_long i = y * w + x;
			if (!mask[(size_t)i]) continue;
			bool all_inside = true;
			for (A_long dy = -1; dy <= 1; ++dy) {
				for (A_long dx = -1; dx <= 1; ++dx) {
					if (dx == 0 && dy == 0) continue;
					A_long nx = ClampValue<A_long>(x + dx, 0, w - 1);
					A_long ny = ClampValue<A_long>(y + dy, 0, h - 1);
					all_inside = all_inside && mask[(size_t)ny * (size_t)w + (size_t)nx] != 0;
				}
			}
			out[(size_t)i] = all_inside ? 0 : 1;
		}
	}
	return out;
}

