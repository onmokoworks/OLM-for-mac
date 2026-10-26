// ============================================================================
// Meijster 2-pass Exact Euclidean Distance Transform
//   Reference: A. Meijster, J.B.T.M. Roerdink, W.H. Hesselink 2000.
//   Produces the SAME result as OpenCV distanceTransform(DIST_L2, DIST_MASK_PRECISE).
//
//   Input : mask[w*h] — 0 = "source" (distance 0), non-zero = "to measure"
//   Output: dst [w*h] — Euclidean distance (float) to nearest zero pixel
// ============================================================================
static inline float edt_f(long x, long i, long gi) {
	// squared distance from (x,?) to (i, g(i)); used for parabola intersections
	long d = x - i;
	return (float)(d * d + (long long)gi * gi);
}
static inline long edt_sep(long i, long u, long gi, long gu) {
	// intersection x of two parabolas at column i (g=gi) and column u (g=gu)
	long long num = (long long)u * u - (long long)i * i + (long long)gu * gu - (long long)gi * gi;
	long long den = 2 * (long long)(u - i);
	// floor division for negative numerator is fine here since u > i always
	return (long)(num / den);
}

static void meijster_edt(const u_char *mask, float *dst, long w, long h)
{
	const long INF = w + h; // upper bound
	std::vector<long> g((size_t)w * h);

	// Phase 1: column-wise vertical pass — g(x,y) = dist to nearest zero in column x
	for (long x = 0; x < w; ++x) {
		// Top-down
		g[(size_t)x] = mask[x] ? INF : 0;
		for (long y = 1; y < h; ++y) {
			size_t idx = (size_t)y * w + x;
			if (mask[idx]) {
				long prev = g[idx - w];
				g[idx] = (prev == INF) ? INF : (prev + 1);
			} else {
				g[idx] = 0;
			}
		}
		// Bottom-up
		for (long y = h - 2; y >= 0; --y) {
			size_t idx = (size_t)y * w + x;
			long below = g[idx + w];
			long cur   = g[idx];
			if (below != INF && below + 1 < cur) g[idx] = below + 1;
		}
	}

	// Phase 2: row-wise parabola envelope — F(x,y) = min over i of (x-i)^2 + g(i,y)^2
	std::vector<long> s((size_t)w), t((size_t)w);
	for (long y = 0; y < h; ++y) {
		long q = 0;
		s[0] = 0;
		t[0] = 0;
		const long *grow = &g[(size_t)y * w];

		for (long u = 1; u < w; ++u) {
			while (q >= 0 && edt_f(t[q], s[q], grow[s[q]]) > edt_f(t[q], u, grow[u])) {
				--q;
			}
			if (q < 0) {
				q = 0;
				s[0] = u;
			} else {
				long w_sep = 1 + edt_sep(s[q], u, grow[s[q]], grow[u]);
				if (w_sep < w) {
					++q;
					s[q] = u;
					t[q] = w_sep;
				}
			}
		}

		float *drow = dst + (size_t)y * w;
		for (long u = w - 1; u >= 0; --u) {
			float d2 = edt_f(u, s[q], grow[s[q]]);
			drow[u] = sqrtf(d2);
			if (u == t[q]) --q;
		}
	}
}

// ============================================================================
// Gaussian blur (separable, matches the legacy cvSmooth replicated border +
// sigma derived via cv::getGaussianKernel default:  sigma = 0.3*((ksize-1)*0.5 - 1) + 0.8
// ============================================================================
static void make_gauss_kernel_smart(std::vector<float> &k, int ksize)
{
	// Original getGaussianKernelBitExact (181285230): sigma-zero small tables,
	// otherwise symmetric double weights, normalized before conversion to float.
	if ((ksize & 1) == 0) ++ksize;
	if (ksize < 1) ksize = 1;
	if (ksize == 1) { k = {1.0f}; return; }
	if (ksize == 3) { k = {0.25f, 0.5f, 0.25f}; return; }
	if (ksize == 5) { k = {1.f/16, 4.f/16, 6.f/16, 4.f/16, 1.f/16}; return; }
	if (ksize == 7) {
		k = {2.f/64, 7.f/64, 14.f/64, 18.f/64, 14.f/64, 7.f/64, 2.f/64}; return;
	}
	if (ksize == 9) {
		k = {4.f/256, 13.f/256, 30.f/256, 51.f/256, 60.f/256,
		     51.f/256, 30.f/256, 13.f/256, 4.f/256}; return;
	}
	const double sigma = ksize * 0.15 + 0.35;
	const double factor = -0.125 / (sigma * sigma);
	const int half = ksize / 2;
	std::vector<double> weights(half);
	double sum = 0.0;
	for (int i = 0; i < half; ++i) {
		const double x = 1 - ksize + i * 2;
		weights[i] = std::exp(x * x * factor);
		sum += weights[i];
	}
	sum = sum * 2.0 + 1.0;
	const double inv = 1.0 / sum;
	k.resize(ksize);
	for (int i = 0; i < half; ++i) k[i] = k[ksize-i-1] = (float)(weights[i] * inv);
	k[half] = (float)inv;
}

static void make_gauss_kernel(std::vector<float> &k, int ksize)
{
	// Odd kernel size required
	if ((ksize & 1) == 0) ++ksize;
	if (ksize < 1) ksize = 1;
	// OpenCV uses an exact binomial kernel for the 3-tap, sigma=0 case.
	// Keeping these values literal avoids the measurable difference from the
	// generic sigma heuristic at the PF16 staging boundary.
	if (ksize == 3) {
		k = {0.25f, 0.5f, 0.25f};
		return;
	}
	double sigma = 0.3 * ((ksize - 1) * 0.5 - 1.0) + 0.8;
	double two_s2 = 2.0 * sigma * sigma;
	k.resize(ksize);
	double sum = 0;
	int half = ksize / 2;
	for (int i = 0; i < ksize; ++i) {
		double x = i - half;
		k[i] = (float)std::exp(-x * x / two_s2);
		sum += k[i];
	}
	float inv = (float)(1.0 / sum);
	for (auto &v : k) v *= inv;
}


static void gauss_blur_separable(float *mat, long w, long h, int ksize, bool smart_owner)
{
	if (ksize <= 1) return;
	std::vector<float> k;
	if (smart_owner) make_gauss_kernel_smart(k, ksize);
	else make_gauss_kernel(k, ksize);
	int half = (int)k.size() / 2;

	std::vector<float> tmp((size_t)w * h);
	if (ksize == 3) {
		for (long y = 0; y < h; ++y) {
			const float *row = mat + (size_t)y * w;
			for (long x = 0; x < w; ++x) {
				long xl = x > 0 ? x - 1 : 0;
				long xr = x + 1 < w ? x + 1 : w - 1;
				tmp[(size_t)y * w + x] = (row[xl] + row[xr]) * 0.25f + row[x] * 0.5f;
			}
		}
		for (long y = 0; y < h; ++y) {
			long yt = y > 0 ? y - 1 : 0;
			long yb = y + 1 < h ? y + 1 : h - 1;
			for (long x = 0; x < w; ++x) {
				mat[(size_t)y * w + x] =
					(tmp[(size_t)yt * w + x] + tmp[(size_t)yb * w + x]) * 0.25f +
					tmp[(size_t)y * w + x] * 0.5f;
			}
		}
		return;
	}

	// Horizontal
	for (long y = 0; y < h; ++y) {
		const float *row = mat + (size_t)y * w;
		float       *out = tmp.data() + (size_t)y * w;
		for (long x = 0; x < w; ++x) {
			if (smart_owner && w == 1) { out[x] = row[x]; continue; }
			// OpenCV SymmRowSmallFilter uses center, near pair, far pair
			// for a symmetric five-tap float kernel (N02 direct cvSmooth probe).
			if (smart_owner && ksize == 5) {
				out[x] = (row[x] * k[2] +
				    (row[std::max(0L,x-1)] + row[std::min(w-1,x+1)]) * k[3]) +
				    (row[std::max(0L,x-2)] + row[std::min(w-1,x+2)]) * k[4];
				continue;
			}
			float acc = 0;
			for (int i = -half; i <= half; ++i) {
				long xi = x + i;
				if (xi < 0) xi = 0;
				if (xi >= w) xi = w - 1;
				acc += row[xi] * k[i + half];
			}
			out[x] = acc;
		}
	}
	if (smart_owner) {
		// The original replicated-border Gaussian skips singleton axes. Its
		// symmetric column filter adds the center, then paired neighbors outward.
		if (h == 1) { std::copy(tmp.begin(), tmp.end(), mat); return; }
		for (long y = 0; y < h; ++y) {
			for (long x = 0; x < w; ++x) {
				float acc = tmp[(size_t)y*w+x] * k[half];
				for (int i = 1; i <= half; ++i) {
					const long lo = std::max(0L, y-i), hi = std::min(h-1, y+i);
					acc += (tmp[(size_t)lo*w+x] + tmp[(size_t)hi*w+x]) * k[half+i];
				}
				mat[(size_t)y*w+x] = acc;
			}
		}
		return;
	}
	// Vertical
	for (long x = 0; x < w; ++x) {
		for (long y = 0; y < h; ++y) {
			float acc = 0;
			for (int i = -half; i <= half; ++i) {
				long yi = y + i;
				if (yi < 0) yi = 0;
				if (yi >= h) yi = h - 1;
				acc += tmp[(size_t)yi * w + x] * k[i + half];
			}
			mat[(size_t)y * w + x] = acc;
		}
	}
}

// cvSmooth accepts independent horizontal and vertical Gaussian apertures.
static void gauss_blur_rect(float *mat, long w, long h, int kx, int ky)
{
	if (kx == ky) { gauss_blur_separable(mat,w,h,kx,true); return; }
	std::vector<float> a,b,tmp((size_t)w*h);
	make_gauss_kernel_smart(a,kx); make_gauss_kernel_smart(b,ky);
	for (long y=0;y<h;++y) for (long x=0;x<w;++x) {
		const float *row=mat+(size_t)y*w;
		float v=0;
		if (w==1 || kx==1) v=row[x];
		else if (kx==3) v=(row[std::max(0L,x-1)]+row[std::min(w-1,x+1)])*0.25f+row[x]*0.5f;
		else if (kx==5) v=(row[x]*a[2]+(row[std::max(0L,x-1)]+row[std::min(w-1,x+1)])*a[3])+
		    (row[std::max(0L,x-2)]+row[std::min(w-1,x+2)])*a[4];
		else for (int i=0;i<kx;++i) v+=row[std::max(0L,std::min(w-1,x+i-kx/2))]*a[i];
		tmp[(size_t)y*w+x]=v;
	}
	for (long y=0;y<h;++y) for (long x=0;x<w;++x) {
		float v=tmp[(size_t)y*w+x];
		if (h!=1 && ky!=1) {
			if (ky==3) v=(tmp[(size_t)std::max(0L,y-1)*w+x]+tmp[(size_t)std::min(h-1,y+1)*w+x])*0.25f+v*0.5f;
			else { v*=b[ky/2]; for (int i=1;i<=ky/2;++i)
				v+=(tmp[(size_t)std::max(0L,y-i)*w+x]+tmp[(size_t)std::min(h-1,y+i)*w+x])*b[ky/2+i]; }
		}
		mat[(size_t)y*w+x]=v;
	}
}

// cvSmooth mode 1 (CV_BLUR) used by Constant + Blur is a normalized box
// filter with replicated borders. Keep it separate from the Gaussian path
// used by the other interpolation modes.
// Reordering a double sum is exact when all binary32 inputs share a grid
// whose largest possible absolute kernel sum fits the 53-bit significand.
// Otherwise retain the original row-major accumulation below.
static bool box_sum_is_exact(const float *mat, size_t count, int ksize)
{
	int quantum = 0;
	double maximum = 0.0;
	for (size_t i = 0; i < count; ++i) {
		const double value = std::fabs((double)mat[i]);
		if (!std::isfinite(value)) return false;
		if (value == 0.0) continue;
		int exponent;
		std::frexp(value, &exponent);
		quantum = std::min(quantum, exponent - 24);
		maximum = std::max(maximum, value);
	}
	const std::uint64_t taps = (std::uint64_t)ksize * (std::uint64_t)ksize;
	return std::ldexp(maximum, -quantum) <= (double)((UINT64_C(1) << 53) / taps);
}

static void box_blur_exact_sum(float *mat, long w, long h, int ksize, double area, int ksize_y)
{
	const long half = ksize / 2;
	const long vertical_half = ksize_y / 2;
	std::vector<double> rows((size_t)w * h);
	for (long y = 0; y < h; ++y) {
		const float *src = mat + (size_t)y * w;
		double sum = 0.0;
		sum += (double)src[0] * half;
		for (long x = 0; x <= std::min(half, w - 1); ++x) sum += src[x];
		if (half >= w) sum += (double)src[w - 1] * (half - w + 1);
		rows[(size_t)y * w] = sum;
		for (long x = 1; x < w; ++x) {
			sum -= src[std::max(0L, x - half - 1)];
			sum += src[std::min(w - 1, x + half)];
			rows[(size_t)y * w + x] = sum;
		}
	}
	for (long x = 0; x < w; ++x) {
		double sum = 0.0;
		sum += rows[x] * vertical_half;
		for (long y = 0; y <= std::min(vertical_half, h - 1); ++y) sum += rows[(size_t)y * w + x];
		if (vertical_half >= h) sum += rows[(size_t)(h - 1) * w + x] * (vertical_half - h + 1);
		mat[x] = (float)(sum / area);
		for (long y = 1; y < h; ++y) {
			sum -= rows[(size_t)std::max(0L, y - vertical_half - 1) * w + x];
			sum += rows[(size_t)std::min(h - 1, y + vertical_half) * w + x];
			mat[(size_t)y * w + x] = (float)(sum / area);
		}
	}
}

static void box_blur_separable(float *mat, long w, long h, int ksize, bool double_area = false, bool smart_owner = false, int ksize_y = 0)
{
	if (!ksize_y) ksize_y = ksize;
	if (ksize <= 1 && ksize_y <= 1) return;
	const int half = ksize / 2;
	// Smart typed paths retain the integer kernel area in double precision.
	// Odd kernels above 4095 lose area bits when rounded through float.
	const double area = double_area ? (double)ksize * (double)ksize_y : (double)(float)(ksize * ksize);
	if (smart_owner && box_sum_is_exact(mat, (size_t)w * h, std::max(ksize,ksize_y))) {
		box_blur_exact_sum(mat, w, h, ksize, area, ksize_y);
		return;
	}
	std::vector<float> src(mat, mat + (size_t)w * h);
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			double sum = 0.0;
			for (int j = -ksize_y/2; j <= ksize_y/2; ++j) {
				long yi = y + j;
				if (yi < 0) yi = 0;
				if (yi >= h) yi = h - 1;
				for (int i = -half; i <= half; ++i) {
					long xi = x + i;
					if (xi < 0) xi = 0;
					if (xi >= w) xi = w - 1;
					sum += src[(size_t)yi * w + xi];
				}
			}
			mat[(size_t)y * w + x] = (float)(sum / (double)area);
		}
	}
}

// Legacy cvSmooth mode 3 (CV_MEDIAN).  The retained AEX uses replicated
// borders and an odd square aperture.  Keep the temporary source separate:
// OpenCV's median pass never consumes values written earlier in the scan.
// Large replicated-border windows contain many copies of the same source
// samples. Count their multiplicities instead of materializing every tap.
// Finite values with no negative zero have a unique bit pattern per numeric
// value, so selecting the weighted order statistic preserves nth_element's
// result bits even when several source samples compare equal.
static bool median_blur_weighted(float *mat, long w, long h, int ksize)
{
	const size_t count = (size_t)w*h;
	if ((uint64_t)ksize*ksize <= (uint64_t)count*4 ||
	    !std::all_of(mat, mat+count, [](float v) {
	        return std::isfinite(v) && !(v == 0.0f && std::signbit(v));
	    })) return false;
	const std::vector<float> source(mat, mat+count);
	std::vector<size_t> order(count);
	for (size_t i=0; i<count; ++i) order[i]=i;
	std::sort(order.begin(), order.end(), [&](size_t a, size_t b) {
		return source[a] < source[b];
	});
	const long radius = ksize/2;
	auto multiplicity = [=](long sample, long center, long length) -> uint64_t {
		if (length == 1) return ksize;
		if (sample == 0) return std::max(0L, radius-center+1);
		if (sample == length-1) return std::max(0L, radius-(length-1-center)+1);
		return std::abs(sample-center) <= radius ? 1 : 0;
	};
	const uint64_t rank = (uint64_t)ksize*ksize/2;
	for (long y=0; y<h; ++y) for (long x=0; x<w; ++x) {
		uint64_t cumulative=0;
		for (size_t i:order) {
			cumulative += multiplicity(i%w,x,w)*multiplicity(i/w,y,h);
			if (cumulative > rank) { mat[(size_t)y*w+x]=source[i]; break; }
		}
	}
	return true;
}

static void median_blur(float *mat, long w, long h, int ksize)
{
	if (!mat || w <= 0 || h <= 0 || ksize <= 1) return;
	if (median_blur_weighted(mat, w, h, ksize)) return;
	const int radius = ksize / 2;
	std::vector<float> source(mat, mat + (size_t)w * h);
	std::vector<float> window((size_t)ksize * ksize);
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			size_t n = 0;
			for (int ky = -radius; ky <= radius; ++ky) {
				const long sy = std::max(0L, std::min(h - 1, y + ky));
				for (int kx = -radius; kx <= radius; ++kx) {
					const long sx = std::max(0L, std::min(w - 1, x + kx));
					window[n++] = source[(size_t)sy * w + sx];
				}
			}
			std::nth_element(window.begin(), window.begin() + n / 2, window.begin() + n);
			mat[(size_t)y * w + x] = window[n / 2];
		}
	}
}
