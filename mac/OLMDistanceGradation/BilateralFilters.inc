static float bilateral_ipp_exp(float x)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	static const double powers[256] = {
		0x1.0000000000000p+0, 0x1.00b1afa5abcbfp+0, 0x1.0163da9fb3335p+0, 0x1.02168143b0281p+0,
		0x1.02c9a3e778061p+0, 0x1.037d42e11bbccp+0, 0x1.04315e86e7f85p+0, 0x1.04e5f72f654b1p+0,
		0x1.059b0d3158574p+0, 0x1.0650a0e3c1f89p+0, 0x1.0706b29ddf6dep+0, 0x1.07bd42b72a836p+0,
		0x1.0874518759bc8p+0, 0x1.092bdf66607e0p+0, 0x1.09e3ecac6f383p+0, 0x1.0a9c79b1f3919p+0,
		0x1.0b5586cf9890fp+0, 0x1.0c0f145e46c85p+0, 0x1.0cc922b7247f7p+0, 0x1.0d83b23395decp+0,
		0x1.0e3ec32d3d1a2p+0, 0x1.0efa55fdfa9c5p+0, 0x1.0fb66affed31bp+0, 0x1.1073028d7233ep+0,
		0x1.11301d0125b51p+0, 0x1.11edbab5e2ab6p+0, 0x1.12abdc06c31ccp+0, 0x1.136a814f204abp+0,
		0x1.1429aaea92de0p+0, 0x1.14e95934f312ep+0, 0x1.15a98c8a58e51p+0, 0x1.166a45471c3c2p+0,
		0x1.172b83c7d517bp+0, 0x1.17ed48695bbc0p+0, 0x1.18af9388c8deap+0, 0x1.1972658375d2fp+0,
		0x1.1a35beb6fcb75p+0, 0x1.1af99f8138a1cp+0, 0x1.1bbe084045cd4p+0, 0x1.1c82f95281c6bp+0,
		0x1.1d4873168b9aap+0, 0x1.1e0e75eb44027p+0, 0x1.1ed5022fcd91dp+0, 0x1.1f9c18438ce4dp+0,
		0x1.2063b88628cd6p+0, 0x1.212be3578a819p+0, 0x1.21f49917ddc96p+0, 0x1.22bdda27912d1p+0,
		0x1.2387a6e756238p+0, 0x1.2451ffb82140ap+0, 0x1.251ce4fb2a63fp+0, 0x1.25e85711ece75p+0,
		0x1.26b4565e27cddp+0, 0x1.2780e341ddf29p+0, 0x1.284dfe1f56381p+0, 0x1.291ba7591bb70p+0,
		0x1.29e9df51fdee1p+0, 0x1.2ab8a66d10f13p+0, 0x1.2b87fd0dad990p+0, 0x1.2c57e39771b2fp+0,
		0x1.2d285a6e4030bp+0, 0x1.2df961f641589p+0, 0x1.2ecafa93e2f56p+0, 0x1.2f9d24abd886bp+0,
		0x1.306fe0a31b715p+0, 0x1.31432edeeb2fdp+0, 0x1.32170fc4cd831p+0, 0x1.32eb83ba8ea32p+0,
		0x1.33c08b26416ffp+0, 0x1.3496266e3fa2dp+0, 0x1.356c55f929ff1p+0, 0x1.36431a2de883bp+0,
		0x1.371a7373aa9cbp+0, 0x1.37f26231e754ap+0, 0x1.38cae6d05d866p+0, 0x1.39a401b7140efp+0,
		0x1.3a7db34e59ff7p+0, 0x1.3b57fbfec6cf4p+0, 0x1.3c32dc313a8e5p+0, 0x1.3d0e544ede173p+0,
		0x1.3dea64c123422p+0, 0x1.3ec70df1c5175p+0, 0x1.3fa4504ac801cp+0, 0x1.40822c367a024p+0,
		0x1.4160a21f72e2ap+0, 0x1.423fb2709468ap+0, 0x1.431f5d950a897p+0, 0x1.43ffa3f84b9d4p+0,
		0x1.44e086061892dp+0, 0x1.45c2042a7d232p+0, 0x1.46a41ed1d0057p+0, 0x1.4786d668b3237p+0,
		0x1.486a2b5c13cd0p+0, 0x1.494e1e192aed2p+0, 0x1.4a32af0d7d3dep+0, 0x1.4b17dea6db7d7p+0,
		0x1.4bfdad5362a27p+0, 0x1.4ce41b817c114p+0, 0x1.4dcb299fddd0dp+0, 0x1.4eb2d81d8abffp+0,
		0x1.4f9b2769d2ca7p+0, 0x1.508417f4531eep+0, 0x1.516daa2cf6642p+0, 0x1.5257de83f4eefp+0,
		0x1.5342b569d4f82p+0, 0x1.542e2f4f6ad27p+0, 0x1.551a4ca5d920fp+0, 0x1.56070dde910d2p+0,
		0x1.56f4736b527dap+0, 0x1.57e27dbe2c4cfp+0, 0x1.58d12d497c7fdp+0, 0x1.59c0827ff07ccp+0,
		0x1.5ab07dd485429p+0, 0x1.5ba11fba87a03p+0, 0x1.5c9268a5946b7p+0, 0x1.5d84590998b93p+0,
		0x1.5e76f15ad2148p+0, 0x1.5f6a320dceb71p+0, 0x1.605e1b976dc09p+0, 0x1.6152ae6cdf6f4p+0,
		0x1.6247eb03a5585p+0, 0x1.633dd1d1929fdp+0, 0x1.6434634ccc320p+0, 0x1.652b9febc8fb7p+0,
		0x1.6623882552225p+0, 0x1.671c1c70833f6p+0, 0x1.68155d44ca973p+0, 0x1.690f4b19e9538p+0,
		0x1.6a09e667f3bcdp+0, 0x1.6b052fa75173ep+0, 0x1.6c012750bdabfp+0, 0x1.6cfdcddd47645p+0,
		0x1.6dfb23c651a2fp+0, 0x1.6ef9298593ae5p+0, 0x1.6ff7df9519484p+0, 0x1.70f7466f42e87p+0,
		0x1.71f75e8ec5f74p+0, 0x1.72f8286ead08ap+0, 0x1.73f9a48a58174p+0, 0x1.74fbd35d7cbfdp+0,
		0x1.75feb564267c9p+0, 0x1.77024b1ab6e09p+0, 0x1.780694fde5d3fp+0, 0x1.790b938ac1cf6p+0,
		0x1.7a11473eb0187p+0, 0x1.7b17b0976cfdbp+0, 0x1.7c1ed0130c132p+0, 0x1.7d26a62ff86f0p+0,
		0x1.7e2f336cf4e62p+0, 0x1.7f3878491c491p+0, 0x1.80427543e1a12p+0, 0x1.814d2add106d9p+0,
		0x1.82589994cce13p+0, 0x1.8364c1eb941f7p+0, 0x1.8471a4623c7adp+0, 0x1.857f4179f5b21p+0,
		0x1.868d99b4492edp+0, 0x1.879cad931a436p+0, 0x1.88ac7d98a6699p+0, 0x1.89bd0a478580fp+0,
		0x1.8ace5422aa0dbp+0, 0x1.8be05bad61778p+0, 0x1.8cf3216b5448cp+0, 0x1.8e06a5e0866d9p+0,
		0x1.8f1ae99157736p+0, 0x1.902fed0282c8ap+0, 0x1.9145b0b91ffc6p+0, 0x1.925c353aa2fe2p+0,
		0x1.93737b0cdc5e5p+0, 0x1.948b82b5f98e5p+0, 0x1.95a44cbc8520fp+0, 0x1.96bdd9a7670b3p+0,
		0x1.97d829fde4e50p+0, 0x1.98f33e47a22a2p+0, 0x1.9a0f170ca07bap+0, 0x1.9b2bb4d53fe0dp+0,
		0x1.9c49182a3f090p+0, 0x1.9d674194bb8d5p+0, 0x1.9e86319e32323p+0, 0x1.9fa5e8d07f29ep+0,
		0x1.a0c667b5de565p+0, 0x1.a1e7aed8eb8bbp+0, 0x1.a309bec4a2d33p+0, 0x1.a42c980460ad8p+0,
		0x1.a5503b23e255dp+0, 0x1.a674a8af46052p+0, 0x1.a799e1330b358p+0, 0x1.a8bfe53c12e59p+0,
		0x1.a9e6b5579fdbfp+0, 0x1.ab0e521356ebap+0, 0x1.ac36bbfd3f37ap+0, 0x1.ad5ff3a3c2774p+0,
		0x1.ae89f995ad3adp+0, 0x1.afb4ce622f2ffp+0, 0x1.b0e07298db666p+0, 0x1.b20ce6c9a8952p+0,
		0x1.b33a2b84f15fbp+0, 0x1.b468415b749b1p+0, 0x1.b59728de5593ap+0, 0x1.b6c6e29f1c52ap+0,
		0x1.b7f76f2fb5e47p+0, 0x1.b928cf22749e4p+0, 0x1.ba5b030a1064ap+0, 0x1.bb8e0b79a6f1fp+0,
		0x1.bcc1e904bc1d2p+0, 0x1.bdf69c3f3a207p+0, 0x1.bf2c25bd71e09p+0, 0x1.c06286141b33dp+0,
		0x1.c199bdd85529cp+0, 0x1.c2d1cd9fa652cp+0, 0x1.c40ab5fffd07ap+0, 0x1.c544778fafb22p+0,
		0x1.c67f12e57d14bp+0, 0x1.c7ba88988c933p+0, 0x1.c8f6d9406e7b5p+0, 0x1.ca3405751c4dbp+0,
		0x1.cb720dcef9069p+0, 0x1.ccb0f2e6d1675p+0, 0x1.cdf0b555dc3fap+0, 0x1.cf3155b5bab74p+0,
		0x1.d072d4a07897cp+0, 0x1.d1b532b08c968p+0, 0x1.d2f87080d89f2p+0, 0x1.d43c8eacaa1d6p+0,
		0x1.d5818dcfba487p+0, 0x1.d6c76e862e6d3p+0, 0x1.d80e316c98398p+0, 0x1.d955d71ff6075p+0,
		0x1.da9e603db3285p+0, 0x1.dbe7cd63a8315p+0, 0x1.dd321f301b460p+0, 0x1.de7d5641c0658p+0,
		0x1.dfc97337b9b5fp+0, 0x1.e11676b197d17p+0, 0x1.e264614f5a129p+0, 0x1.e3b333b16ee12p+0,
		0x1.e502ee78b3ff6p+0, 0x1.e653924676d76p+0, 0x1.e7a51fbc74c83p+0, 0x1.e8f7977cdb740p+0,
		0x1.ea4afa2a490dap+0, 0x1.eb9f4867cca6ep+0, 0x1.ecf482d8e67f1p+0, 0x1.ee4aaa2188510p+0,
		0x1.efa1bee615a27p+0, 0x1.f0f9c1cb6412ap+0, 0x1.f252b376bba97p+0, 0x1.f3ac948dd7274p+0,
		0x1.f50765b6e4540p+0, 0x1.f6632798844f8p+0, 0x1.f7bfdad9cbe14p+0, 0x1.f91d802243c89p+0,
		0x1.fa7c1819e90d8p+0, 0x1.fbdba3692d514p+0, 0x1.fd3c22b8f71f1p+0, 0x1.fe9d96b2a23d9p+0,
	};
	if (std::fabs(x) < 0x1p-28f) return 1.0f + x;
	const double scaled = (double)x * 0x1.71547652b82fep+8;
	const double biased = 0x1.8p52 + scaled;
	std::uint64_t bits;
	std::memcpy(&bits, &biased, sizeof(bits));
	const std::int32_t n = (std::int32_t)(std::uint32_t)bits;
	const double residual = scaled + (0x1.8p52 - biased);
	double value = powers[(std::uint32_t)n & 255];
	std::memcpy(&bits, &value, sizeof(bits));
	bits += (std::uint64_t)(std::int64_t)(n >> 8) << 52;
	std::memcpy(&value, &bits, sizeof(bits));
	const double quadratic = (0x1.ebfbdff82c58ep-19 * residual) * residual;
	const double linear = 0x1.62e42fefa72c5p-9 * residual + 1.0;
	return (float)(value * (linear + quadratic));
}

static inline float bilateral_noncontracting_product(float left, float right)
{
	volatile float product = left * right;
	return product;
}

// The original generic scalar IPP body (1806be1e0) scans a circular
// kernel in row-major order, including the center. Its spatial and color
// exponent cutoffs are strictly greater than -25 (1815bd7c4/1815dce38).
static void bilateral_blur_ipp_scalar(float *mat, long w, long h, int radius)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	// For finite samples, spatial-zero taps add only signed zero. Both
	// accumulators start at +0, so removing these taps preserves their bits
	// and the order of every nonzero addition. Retain the full traversal for
	// nonfinite fields, where sample * 0 can produce a NaN.
	const bool finite = std::all_of(mat, mat + (size_t)w*h,
	    [](float value) { return std::isfinite(value); });
	const int extent = finite ? std::min(radius, 7) : radius;
	struct Offset { int x, y; float spatial; };
	std::vector<Offset> offsets;
	for (int y = -extent; y <= extent; ++y) {
		for (int x = -extent; x <= extent; ++x) {
			const int squared = x*x + y*y;
			if (squared > radius*radius || (finite && squared >= 50)) continue;
			const float exponent = -0.5f * (float)squared;
			offsets.push_back({x, y, exponent > -25.0f ? bilateral_ipp_exp(exponent) : 0.0f});
		}
	}
	const std::vector<float> source(mat, mat + (size_t)w*h);
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			const float center = source[(size_t)y*w+x];
			float sum = 0.0f, weight_sum = 0.0f;
			for (const Offset &offset : offsets) {
				const long sx = std::max(0L, std::min(w-1, x+offset.x));
				const long sy = std::max(0L, std::min(h-1, y+offset.y));
				const float sample = source[(size_t)sy*w+sx];
				const float difference = sample-center;
				const float exponent = (-0.5f*difference)*difference;
				const float color = exponent > -25.0f ? bilateral_ipp_exp(exponent) : 0.0f;
				const float weight = bilateral_noncontracting_product(color, offset.spatial);
				weight_sum += weight;
				sum += bilateral_noncontracting_product(sample, weight);
			}
			mat[(size_t)y*w+x] = sum / weight_sum;
		}
	}
}

// IPP scalar radius-two body FUN_1806bd9a0 groups taps by squared
// distance 4, 2, 1. Its spatial multiplication follows each four-tap
// reduction, and the center enters numerator/denominator at different
// points. The vector body (1806b7240) instead reduces distance 1, 4, 2,
// visits distance-four taps L/R/T/B, and adds the center last (1806b7919).
// A generic row-major circular reduction has different rounding.
static float bilateral_ipp_vector_exp(float x);

static void bilateral_blur_ipp_radius_two(float *mat, long w, long h)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	const int taps[3][4][2] = {
		{{0,-2},{-2,0},{2,0},{0,2}},
		{{-1,-1},{1,-1},{-1,1},{1,1}},
		{{0,-1},{-1,0},{1,0},{0,1}}
	};
	const float spatial[3] = {bilateral_ipp_exp(-2.0f),
	    bilateral_ipp_exp(-1.0f), bilateral_ipp_exp(-0.5f)};
	const std::vector<float> source(mat, mat+(size_t)w*h);
	for (long y=0; y<h; ++y) for (long x=0; x<w; ++x) {
		const float center=source[(size_t)y*w+x];
		const bool vector_dispatch = w >= 16 && h > 4 &&
		    (y < 2 || y >= h-2 || (x >= 2 && x < w-2));
		float numerators[3], denominators[3];
		for (int group=0; group<3; ++group) {
			float weights[4], products[4];
			for (int tap=0; tap<4; ++tap) {
				const long sx=std::max(0L,std::min(w-1,x+taps[group][tap][0]));
				const long sy=std::max(0L,std::min(h-1,y+taps[group][tap][1]));
				const float sample=source[(size_t)sy*w+sx];
				const float difference=sample-center;
				const float exponent=vector_dispatch ? (difference*difference)*-0.5f : (-0.5f*difference)*difference;
				weights[tap]=exponent > -25.0f ? (vector_dispatch ? bilateral_ipp_vector_exp(exponent) : bilateral_ipp_exp(exponent)) : 0.0f;
				products[tap]=bilateral_noncontracting_product(sample,weights[tap]);
			}
			if (vector_dispatch && group == 0) {
				std::swap(products[0],products[1]); std::swap(products[1],products[2]);
				std::swap(weights[0],weights[1]); std::swap(weights[1],weights[2]);
			}
			numerators[group]=bilateral_noncontracting_product(
			    ((products[0]+products[1])+products[2])+products[3],spatial[group]);
			denominators[group]=bilateral_noncontracting_product(
			    ((weights[0]+weights[1])+weights[2])+weights[3],spatial[group]);
		}
		const float numerator=vector_dispatch ? center+((numerators[2]+numerators[0])+numerators[1]) :
		    (center+(numerators[0]+numerators[1]))+numerators[2];
		const float denominator=vector_dispatch ? ((denominators[2]+denominators[0])+denominators[1])+1.0f :
		    ((denominators[0]+denominators[1])+1.0f)+denominators[2];
		mat[(size_t)y*w+x]=numerator/denominator;
	}
}

static bool is_scalar_bilateral_shape(const DGParams &p, long w, long h)
{
	if (!p.smart_owner || p.blur_mode != BLUR_MODE_BILATERAL ||
	    p.pixel_size == sizeof(PF_Pixel16) || p.ds_x != 1.0f || p.ds_y != 1.0f) return false;
	const long radius = (long)((float)p.blur_size * std::min(p.ds_x, p.ds_y) + 0.5f);
	// Retain PF8 dispatch. Radius two has its own scalar/vector body;
	// larger scalar kernels discard only proven zero-weight finite-field taps.
	return radius >= (p.pixel_size == sizeof(PF_PixelFloat) ? 2 : 3) && radius <= (p.pixel_size == sizeof(PF_PixelFloat) ? 4096 : 32) &&
	    (radius == 2 || w <= 2*radius || h <= 2*radius);
}

// Bounded lane of the original IPP vector exponential (180ba5780).
// Coefficients at 1815f0600..1815f0880; preserve MULPS/ADDPS rounding.
static float bilateral_ipp_vector_exp(float x)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	const float scaled = bilateral_noncontracting_product(x, 0x1.715476p+0f);
	const float biased = scaled + 0x1.8p23f;
	const float n = biased - 0x1.8p23f;
	const float hi = bilateral_noncontracting_product(n, 0x1.62e4p-1f);
	const float lo = bilateral_noncontracting_product(n, 0x1.7f7d1cp-20f);
	const float residual = (x - hi) - lo;
	float poly = bilateral_noncontracting_product(0x1.0fb3fcp-7f, residual) + 0x1.570724p-5f;
	poly = bilateral_noncontracting_product(poly, residual) + 0x1.555958p-3f;
	poly = bilateral_noncontracting_product(poly, residual) + 0x1.fffe68p-2f;
	poly = bilateral_noncontracting_product(poly, residual) + 0x1.fffffcp-1f;
	poly = bilateral_noncontracting_product(poly, residual) + 1.0f;
	std::uint32_t scale_bits, result_bits;
	std::memcpy(&scale_bits, &biased, 4);
	std::memcpy(&result_bits, &poly, 4);
	result_bits += scale_bits << 23;
	std::memcpy(&poly, &result_bits, 4);
	return poly;
}

// FUN_1802a1640 selects scalar side tiles and vector top/bottom/interior.
// FUN_1806b7d40 retains circular row-major taps and separate float operations.
static void bilateral_blur_ipp_general(float *mat, long w, long h, int radius)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	// For finite samples, spatial-zero taps add only signed zero. Both
	// accumulators start at +0, so removing these taps preserves their bits
	// and the order of every nonzero addition. Retain the full traversal for
	// nonfinite fields, where sample * 0 can produce a NaN.
	const bool finite = std::all_of(mat, mat + (size_t)w*h,
	    [](float value) { return std::isfinite(value); });
	const int extent = finite ? std::min(radius, 7) : radius;
	struct Offset { int x, y; float spatial; };
	std::vector<Offset> offsets;
	for (int y = -extent; y <= extent; ++y) {
		for (int x = -extent; x <= extent; ++x) {
			const int squared = x*x + y*y;
			if (squared > radius*radius || (finite && squared >= 50)) continue;
			const float exponent = -0.5f * (float)squared;
			offsets.push_back({x, y, exponent > -25.0f ? bilateral_ipp_exp(exponent) : 0.0f});
		}
	}
	const std::vector<float> source(mat, mat + (size_t)w*h);
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			const bool vector_dispatch = w >= 16 && w > 2*radius && h > 2*radius &&
			    (y < radius || y >= h-radius || (x >= radius && x < w-radius));
			const float center = source[(size_t)y*w+x];
			float sum = 0.0f, weight_sum = 0.0f;
			for (const Offset &offset : offsets) {
				const long sx = std::max(0L, std::min(w-1, x+offset.x));
				const long sy = std::max(0L, std::min(h-1, y+offset.y));
				const float sample = source[(size_t)sy*w+sx];
				const float difference = sample-center;
				const float exponent = vector_dispatch ? (difference*difference)*-0.5f : (-0.5f*difference)*difference;
				const float color = exponent > -25.0f ? (vector_dispatch ? bilateral_ipp_vector_exp(exponent) : bilateral_ipp_exp(exponent)) : 0.0f;
				const float weight = bilateral_noncontracting_product(color, offset.spatial);
				weight_sum += weight;
				sum += bilateral_noncontracting_product(sample, weight);
			}
			mat[(size_t)y*w+x] = sum / weight_sum;
		}
	}
}

// PF8/PF32 Smart reproduction of the retained radius-one IPP bilateral body.
// cvSmooth(CV_BILATERAL, diameter 1 or 3, ..., 0, 0) selects radius one and
// unit sigmas (1812ca750). Larger radii and PF16 remain separate lanes.
// IPP evaluates four color weights directly, accumulates
// L/T/R/B without contraction, then applies the common spatial weight.
static void bilateral_blur_opencv455_f32x4(float *mat, long w, long h)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	if (!mat || w <= 0 || h <= 0) return;
	std::vector<float> source(mat, mat + (size_t)w * h);
	const float spatial_weight = bilateral_ipp_exp(-0.5f);
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			const long top = std::max(0L, y - 1), bottom = std::min(h - 1, y + 1);
			const long left = std::max(0L, x - 1), right = std::min(w - 1, x + 1);
			const float center = source[(size_t)y * w + x];
			const float values[4] = {source[(size_t)y * w + left], source[(size_t)top * w + x],
			                         source[(size_t)y * w + right], source[(size_t)bottom * w + x]};
			// 1802a1640 uses the scalar padded body below 3 pixels in either
			// dimension. At width16+, top/bottom and interior tiles use the
			// vector body; the one-column side tiles keep the scalar body.
			const bool vector_dispatch = w >= 16 && h >= 3 &&
				(y == 0 || y == h-1 || (x > 0 && x < w-1));
			float sum = 0.0f;
			float weight_sum = 0.0f;
			for (int k = 0; k < 4; ++k) {
				const float difference = values[k] - center;
				const float exponent = vector_dispatch ? (difference * difference) * -0.5f : (-0.5f * difference) * difference;
				// 1806bd7ba..1806bd84f skips exp at/below -25; the exp
				// helper is only reproduced on that bounded input interval.
				const float color_weight = exponent > -25.0f ? (vector_dispatch ? bilateral_ipp_vector_exp(exponent) : bilateral_ipp_exp(exponent)) : 0.0f;
				weight_sum += color_weight;
				sum += bilateral_noncontracting_product(values[k], color_weight);
			}
			weight_sum = bilateral_noncontracting_product(weight_sum, spatial_weight);
			sum = bilateral_noncontracting_product(sum, spatial_weight);
			mat[(size_t)y * w + x] = (sum + center) / (weight_sum + 1.0f);
		}
	}
}

// ============================================================================
// Helpers: pixel fetch / store (alpha, red, green, blue order in AE)
// ============================================================================
template<typename P> static inline void load_rgba_norm(const P *p, float &a, float &r, float &g, float &b);

template<> inline void load_rgba_norm<PF_Pixel8>(const PF_Pixel8 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / 255.0f; r = p->red / 255.0f; g = p->green / 255.0f; b = p->blue / 255.0f;
}
template<> inline void load_rgba_norm<PF_Pixel16>(const PF_Pixel16 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / 32768.0f; r = p->red / 32768.0f; g = p->green / 32768.0f; b = p->blue / 32768.0f;
}
template<> inline void load_rgba_norm<PF_PixelFloat>(const PF_PixelFloat *p, float &a, float &r, float &g, float &b) {
	a = p->alpha; r = p->red; g = p->green; b = p->blue;
}

// The actual-AEX PF8 and PF16 compose callbacks both use float-to-int
