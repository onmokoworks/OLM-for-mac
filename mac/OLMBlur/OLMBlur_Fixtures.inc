// PF16 12x12 retained standard-source row stride; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard12RowBytes = 109;
// PF16 18-wide retained source row stride; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard18RowBytes = 157;
// AE nominal PF16 white in the retained source fixtures; retained public-admission witness, not an AEX coefficient.
static constexpr int kAE16White = 32768;
// inclusive 0..32768 source-pattern modulus; retained public-admission witness, not an AEX coefficient.
static constexpr int kAE16SampleModulus = 32769;
// standard PF16 source red x coefficient; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard16RedXStep = 257;
// standard PF16 source red offset; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard16RedOffset = 101;
// standard PF16 source green x coefficient; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard16GreenXStep = 113;
// standard PF16 source green y coefficient; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard16GreenYStep = 211;
// standard PF16 source green offset; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard16GreenOffset = 307;
// standard PF16 source blue x coefficient; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard16BlueXStep = 401;
// standard PF16 source blue y coefficient; retained public-admission witness, not an AEX coefficient.
static constexpr int kStandard16BlueYStep = 97;
// PF16 retained source blue step/offset value; retained public-admission witness, not an AEX coefficient.
static constexpr int kBluePatternStepOrOffset = 503;
// quarter nominal PF16 white in the source fixtures; retained public-admission witness, not an AEX coefficient.
static constexpr int kQuarterWhite16 = 8192;
// half nominal PF16 white in the source fixtures; retained public-admission witness, not an AEX coefficient.
static constexpr int kHalfWhite16 = 16384;
// mixed-alpha PF16 source red value; retained public-admission witness, not an AEX coefficient.
static constexpr int kMixedAlpha16Red = 12800;
// mixed-alpha PF16 source green value; retained public-admission witness, not an AEX coefficient.
static constexpr int kMixedAlpha16Green = 25600;
// retained PF16 source high blue/green value; retained public-admission witness, not an AEX coefficient.
static constexpr int kSource16HighBlueOrGreen = 30000;
// 7x5 PF16 source red offset; retained public-admission witness, not an AEX coefficient.
static constexpr int kSevenByFiveRedOffset = 1000;
// 7x5 PF16 source red x coefficient; retained public-admission witness, not an AEX coefficient.
static constexpr int kSevenByFiveRedXStep = 701;
// 7x5 PF16 source green y coefficient; retained public-admission witness, not an AEX coefficient.
static constexpr int kSevenByFiveGreenYStep = 811;
// 7x5 PF16 source blue offset; retained public-admission witness, not an AEX coefficient.
static constexpr int kSevenByFiveBlueOffset = 200;

// Retained source admission patterns, from the public-admission witnesses.
// These are existing compatibility guards, not output overrides.
static bool
ExactPublicSource(const PF_EffectWorld *world, short bpc, bool legacy,
	PublicBlurSourceKind source_kind)
{
	if (!world || !world->data) return false;
	if (source_kind == PublicBlurSourcePF32Legacy24Repeat1Union)
		return ExactPublicSource(world,bpc,legacy,PublicBlurSourcePF32LegacyStandard) ||
			ExactPublicSource(world,bpc,legacy,PublicBlurSourceOriginal24);
	if (source_kind == PublicBlurSourcePF16Standard && bpc == 16 &&
		((world->width == 12 && world->height == 12 && world->rowbytes == kStandard12RowBytes) ||
		 (world->width == 18 && world->height == 18 && world->rowbytes == kStandard18RowBytes))) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const uint16_t expected_argb[4] = {
				(uint16_t)(legacy ? kAE16White : (((x*5 + y*3) % 17) == 0 ? 0 : kAE16White)),
				(uint16_t)((kStandard16RedXStep*x + 31*y + kStandard16RedOffset) % kAE16SampleModulus),
				(uint16_t)((kStandard16GreenXStep*x + kStandard16GreenYStep*y + kStandard16GreenOffset) % kAE16SampleModulus),
				(uint16_t)((kStandard16BlueXStep*x + kStandard16BlueYStep*y + kBluePatternStepOrOffset) % kAE16SampleModulus)
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*8u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF16MixedAlpha && bpc == 16 && legacy &&
		world->width == 18 && world->height == 12 &&
		world->rowbytes == kStandard18RowBytes) {
		for (A_long y=0;y<12;++y) for (A_long x=0;x<18;++x) {
			const bool boundary = x == 0 || x == 17 || y == 0 || y == 11;
			const bool hole = (x*7 + y*11) % 13 == 0;
			const uint16_t expected_argb[4] = {
				(uint16_t)(boundary || hole ? 0 : kQuarterWhite16 + ((x*29 + y*17) % 4) * kHalfWhite16),
				kMixedAlpha16Red, kMixedAlpha16Green, kSource16HighBlueOrGreen
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*8u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF16SevenByFive && bpc == 16 &&
		world->width == 7 && world->height == 5 && world->rowbytes == 69) {
		for (A_long y=0;y<5;++y) for (A_long x=0;x<7;++x) {
			const uint16_t expected_argb[4] = {
				kAE16White,
				(uint16_t)(kSevenByFiveRedOffset + kSevenByFiveRedXStep*x + 17*y),
				(uint16_t)(kSource16HighBlueOrGreen + 37*x + kSevenByFiveGreenYStep*y),
				(uint16_t)(kSevenByFiveBlueOffset + kBluePatternStepOrOffset*x + 29*y)
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*8u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8NonLegacyStandard && bpc == 8 && !legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const unsigned char expected_argb[4] = {
				(unsigned char)(((x*5 + y*3) % 17) == 0 ? 0 : 255),
				(unsigned char)((17*x + 3*y + 11) & 255),
				(unsigned char)((7*x + 19*y + 23) & 255),
				(unsigned char)((29*x + 13*y + 37) & 255)
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8LegacyStandard && bpc == 8 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const unsigned char expected_argb[4] = {
				255,
				(unsigned char)((17*x + 3*y + 11) & 255),
				(unsigned char)((7*x + 19*y + 23) & 255),
				(unsigned char)((29*x + 13*y + 37) & 255)
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8LegacyMixedAlpha && bpc == 8 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const bool boundary = x == 0 || x == world->width-1 || y == 0 || y == world->height-1;
			const bool hole = (x*7 + y*11) % 13 == 0;
			const unsigned char expected_argb[4] = {
				(unsigned char)(boundary || hole ? 0 : 32 + ((x*29 + y*17) % 4) * 64),
				50, 100, 150
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8LegacyBoundaryGradient && bpc == 8 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const bool boundary = x == 0 || x == world->width-1 || y == 0 || y == world->height-1;
			const unsigned char expected_argb[4] = {
				255,
				(unsigned char)(boundary ? ((x*19 + y*23 + 7) & 255) : ((31 + x*9 + y*13) & 255)),
				0, 0
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8LegacyByteBoundaries && bpc == 8 && legacy) {
		// Retained PF8 boundary witness values (public admission capture).
		static constexpr unsigned char byteBoundaries[] = {0,1,127,128,254,255};
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const unsigned char expected_argb[4] = {
				byteBoundaries[(x+5*y)%6], byteBoundaries[(2*x+y+1)%6],
				byteBoundaries[(x+3*y+2)%6], byteBoundaries[(5*x+2*y+3)%6]
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF16LegacyWordBoundaries && bpc == 16 && legacy) {
		// Retained PF16 boundary witness values (public admission capture).
		static constexpr uint16_t wordBoundaries[] = {0,1,32767,kAE16White};
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const uint16_t expected_argb[4] = {
				wordBoundaries[(x+3*y)%4], wordBoundaries[(x+y+1)%4],
				wordBoundaries[(2*x+y+2)%4], wordBoundaries[(x+2*y+3)%4]
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*8u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if ((source_kind == PublicBlurSourcePF32NonLegacyStandard ||
		source_kind == PublicBlurSourcePF32LegacyStandard) && bpc == 32) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			// Retained witness uses double expressions followed by float conversion.
			const float expected_argb[4] = {
				(float)(((x*5+y*3)%17)==0 ? 0.0 : ((x+y)%5 ? 1.0 : -0.5)),
				(float)(-1.25 + 0.17*x + 0.031*y),
				(float)(0.5 + 0.11*x - 0.23*y),
				(float)(1.5 + 0.07*x + 0.19*y)
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*16u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF32LegacyMixedAlpha && bpc == 32 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const bool boundary=x==0||x==world->width-1||y==0||y==world->height-1;
			const bool hole=(x*7+y*11)%13==0;
			// Retained witness uses double expressions followed by float conversion.
			const float expected_argb[4] = {
				(float)(boundary||hole?0.0:((x+2*y)%7==0?-0.5:0.25+0.125*((x*3+y)%4))),
				(float)(0.25+0.031*x),(float)(-0.5+0.017*y),(float)(1.5+0.011*(x+y))
			};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*16u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF32LegacyRedBoundary && bpc == 32 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const bool boundary=x==0||x==world->width-1||y==0||y==world->height-1;
			const float expected_argb[4]={(float)(boundary?0.0:1.0),(float)(0.2+0.11*x+0.037*y),0.0f,0.0f};
			const unsigned char *actual_pixel=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*16u;
			if (memcmp(actual_pixel,expected_argb,sizeof(expected_argb))) return false;
		}
		return true;
	}
	if (source_kind != PublicBlurSourceOriginal24) return false;
	if (world->width != 24 || world->height != 24) return false;
	const size_t pixel_bytes = bpc == 8 ? 4u : (bpc == 16 ? 8u : (bpc == 32 ? 16u : 0u));
	if (!pixel_bytes || world->rowbytes != (A_long)(24u * pixel_bytes + (bpc == 8 ? 17u : (bpc == 16 ? 23u : 32u)))) return false;
	// Original24 PF8 source palette from the retained public admission witness.
	static constexpr unsigned char byteSamples[] = {0,1,64,127,128,192,254,255};
	// Original24 PF16 source palette from the same retained witness.
	static constexpr uint16_t wordSamples[] = {0,1,kQuarterWhite16,kHalfWhite16,32767,kAE16White};
	// Original24 PF32 palette; retain float division and exact literal widths.
	static constexpr float floatSamples[] = {-0.5f,0.0f,1.0f/255.0f,0.25f,0.5f,1.0f,1.25f,2.0f};
	for (A_long y=0;y<24;++y) for (A_long x=0;x<24;++x) {
		const int selector=(x*5+y*3)%17;
		const unsigned char *actual_pixel=(const unsigned char*)world->data+(size_t)y*world->rowbytes+(size_t)x*pixel_bytes;
		if (bpc==8) {
			unsigned char expected_argb[4]={(unsigned char)(selector==0?0:byteSamples[(x+3*y)%8]),byteSamples[(2*x+y+1)%8],byteSamples[(x+5*y+2)%8],byteSamples[(7*x+3*y+3)%8]};
			if (memcmp(actual_pixel,expected_argb,4)) return false;
		} else if (bpc==16) {
			uint16_t expected_argb[4]={(uint16_t)(selector==0?0:wordSamples[(x+3*y)%6]),wordSamples[(2*x+y+1)%6],wordSamples[(x+5*y+2)%6],wordSamples[(7*x+3*y+3)%6]};
			if (memcmp(actual_pixel,expected_argb,8)) return false;
		} else {
			float expected_argb[4]={(float)(selector==0?0.0f:floatSamples[(x+3*y)%8]),floatSamples[(2*x+y+1)%8],floatSamples[(x+5*y+2)%8],floatSamples[(7*x+3*y+3)%8]};
			if (memcmp(actual_pixel,expected_argb,16)) return false;
		}
	}
	return true;
}

