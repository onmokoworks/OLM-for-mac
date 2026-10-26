// Typed world adapters and retained PF16 store observation.
// Included in the main translation unit to preserve worker code generation.
// Retained case0006 store observation coordinate; diagnostic-only, no pixel correction.
static constexpr A_long kObservedX = 601;
// Same retained case0006 observation, vertical coordinate.
static constexpr A_long kObservedY = 598;

struct BlurObservationConfig {
	const char *dump_path;
	const char *case_id;
	const char *request_id;
	const char *render_id;
	const char *plugin_sha256;
	const char *project_bpc;
	const char *renderer;
	bool enabled;
};

static BlurObservationConfig
load_blur_observation_config()
{
	BlurObservationConfig config;
	config.dump_path = NULL;
	config.case_id = NULL;
	config.request_id = NULL;
	config.render_id = NULL;
	config.plugin_sha256 = NULL;
	config.project_bpc = NULL;
	config.renderer = NULL;
	config.enabled = false;
	const char *gate = getenv("OLMBLUR_OBSERVE_CASE0006_PIXEL");
	if (!gate || strcmp(gate, "1") != 0) return config;
	config.dump_path = getenv("OLMBLUR_OBSERVE_DUMP_PATH");
	config.case_id = getenv("OLMBLUR_OBSERVE_CASE_ID");
	config.request_id = getenv("OLMBLUR_OBSERVE_REQUEST_ID");
	config.render_id = getenv("OLMBLUR_OBSERVE_RENDER_ID");
	config.plugin_sha256 = getenv("OLMBLUR_OBSERVE_PLUGIN_SHA256");
	config.project_bpc = getenv("OLMBLUR_OBSERVE_PROJECT_BPC");
	config.renderer = getenv("OLMBLUR_OBSERVE_RENDERER");
	if (config.dump_path && *config.dump_path &&
		config.case_id && strcmp(config.case_id, "olmblur__case_0006") == 0 &&
		config.request_id && *config.request_id &&
		config.render_id && *config.render_id &&
		config.plugin_sha256 && *config.plugin_sha256 &&
		config.project_bpc && strcmp(config.project_bpc, "16") == 0 &&
		config.renderer && strcmp(config.renderer, "Software") == 0) {
		config.enabled = true;
	}
	return config;
}

static void
observe_blur_store16_pixel(
	const BlurObservationConfig *observation,
	const BlurParams *bp,
	A_long w, A_long h, A_long x, A_long y,
	float pre_r, float pre_g, float pre_b,
	u_short stored_r, u_short stored_g, u_short stored_b, u_short stored_a)
{
	if (!observation || !observation->enabled || x != kObservedX || y != kObservedY) return;
	FILE *fp = fopen(observation->dump_path, "a");
	if (!fp) return;
	fprintf(fp,
		"OLMBLUR_OBSERVE_STORE16 plugin=OLMBlur effect=OLM_Blur case_id=%s request_id=%s render_id=%s plugin_sha256=%s project_bpc=%s renderer=%s x=%d y=%d w=%d h=%d blur_amount=%.9g blur_smoothness=%.9g repeat=%d bias_dir=%d legacy=%d pre_store=(%.9g,%.9g,%.9g) pre_store_hex=(%a,%a,%a) stored=(%u,%u,%u,%u)\n",
		observation->case_id, observation->request_id, observation->render_id,
		observation->plugin_sha256, observation->project_bpc, observation->renderer,
		(int)x, (int)y, (int)w, (int)h,
		bp ? bp->blur_amount : 0.0f, bp ? bp->blur_smoothness : 0.0f,
		bp ? (int)bp->repeat : 0, bp ? (int)bp->bias_dir : 0,
		bp ? (int)bp->legacy : 0,
		pre_r, pre_g, pre_b, (double)pre_r, (double)pre_g, (double)pre_b,
		(unsigned int)stored_r, (unsigned int)stored_g,
		(unsigned int)stored_b, (unsigned int)stored_a);
	fclose(fp);
}

static PF_Err
render_8bpc_legacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                       float blur_amount, float blur_smoothness,
	                       float render_scale, A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<std::uint8_t> source_argb(pixels * 4);
		std::vector<std::uint8_t> destination_argb(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const PF_Pixel8 *source_row = (const PF_Pixel8*)((const char*)input->data + y * (size_t)input->rowbytes);
			for (size_t x = 0; x < width; ++x) {
				const PF_Pixel8 &pixel = source_row[x];
				std::uint8_t *packed = source_argb.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker8_legacy::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0),
			render_scale
		};
		olm::blur::worker8_legacy::render(
			source_argb.data(), destination_argb.data(), width, height, params);

		for (size_t y = 0; y < height; ++y) {
			const PF_Pixel8 *source_row = (const PF_Pixel8*)((const char*)input->data + y * (size_t)input->rowbytes);
			PF_Pixel8 *output_row = (PF_Pixel8*)((char*)output->data + y * (size_t)output->rowbytes);
			for (size_t x = 0; x < width; ++x) {
				const std::uint8_t *packed = destination_argb.data() + (y * width + x) * 4;
				PF_Pixel8 &pixel = output_row[x];
				pixel.alpha = source_row[x].alpha;
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
render_16bpc_nonlegacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                           float blur_amount, float blur_smoothness,
	                           A_long repeat, A_long bias_dir,
	                           const BlurParams *bp,
	                           const BlurObservationConfig *observation)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<std::uint16_t> source_argb16(pixels * 4);
		std::vector<std::uint16_t> destination_argb16(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				PF_Pixel16 pixel; memcpy(&pixel,source_row+x*sizeof(pixel),sizeof(pixel));
				std::uint16_t *packed = source_argb16.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker16::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0)
		};
		olm::blur::worker16::StoreObservation store_observation = {
			kObservedX, kObservedY, false, {0.0f, 0.0f, 0.0f}, {0, 0, 0, 0}
		};
		olm::blur::worker16::render_nonlegacy(
			(const std::uint8_t*)source_argb16.data(), (std::uint8_t*)destination_argb16.data(),
			width, height, params, observation && observation->enabled ? &store_observation : NULL);
		if (observation && observation->enabled && !store_observation.captured) {
			return PF_Err_INTERNAL_STRUCT_DAMAGED;
		}

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			unsigned char *output_row = (unsigned char*)output->data + y * (size_t)output->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				const std::uint16_t *packed = destination_argb16.data() + (y * width + x) * 4;
				PF_Pixel16 source_pixel,pixel; memcpy(&source_pixel,source_row+x*sizeof(source_pixel),sizeof(source_pixel));
				pixel.alpha = source_pixel.alpha;
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
				memcpy(output_row+x*sizeof(pixel),&pixel,sizeof(pixel));
				if (x == kObservedX && y == kObservedY) {
					observe_blur_store16_pixel(observation, bp, (A_long)width, (A_long)height,
						(A_long)x, (A_long)y,
						store_observation.pre_store[0], store_observation.pre_store[1],
						store_observation.pre_store[2], store_observation.stored_argb[1],
						store_observation.stored_argb[2], store_observation.stored_argb[3],
						store_observation.stored_argb[0]);
				}
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
render_16bpc_legacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                       float blur_amount, float blur_smoothness,
	                       float render_scale, A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<std::uint16_t> source_argb16(pixels * 4);
		std::vector<std::uint16_t> destination_argb16(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				PF_Pixel16 pixel; memcpy(&pixel,source_row+x*sizeof(pixel),sizeof(pixel));
				std::uint16_t *packed = source_argb16.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker16_legacy::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0),
			render_scale
		};
		olm::blur::worker16_legacy::render(
			(const std::uint8_t*)source_argb16.data(), (std::uint8_t*)destination_argb16.data(),
			width, height, params);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			unsigned char *output_row = (unsigned char*)output->data + y * (size_t)output->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				const std::uint16_t *packed = destination_argb16.data() + (y * width + x) * 4;
				PF_Pixel16 source_pixel,pixel; memcpy(&source_pixel,source_row+x*sizeof(source_pixel),sizeof(source_pixel));
				pixel.alpha = source_pixel.alpha;
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
				memcpy(output_row+x*sizeof(pixel),&pixel,sizeof(pixel));
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
render_8bpc_nonlegacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                          float blur_amount, float blur_smoothness,
	                          A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	const size_t bytes = pixels * 4;
	u_char *source_argb = (u_char*)malloc(bytes);
	u_char *destination_argb = (u_char*)malloc(bytes);
	if (!source_argb || !destination_argb) {
		free(source_argb);
		free(destination_argb);
		return PF_Err_OUT_OF_MEMORY;
	}

	for (size_t y = 0; y < height; ++y) {
		const PF_Pixel8 *source_row = (const PF_Pixel8*)((const char*)input->data + y * (size_t)input->rowbytes);
		for (size_t x = 0; x < width; ++x) {
			const PF_Pixel8 &pixel = source_row[x];
			u_char *packed = source_argb + (y * width + x) * 4;
			packed[0] = pixel.alpha;
			packed[1] = pixel.red;
			packed[2] = pixel.green;
			packed[3] = pixel.blue;
		}
	}

	olm::blur::worker::Params params = {
		blur_amount,
		blur_smoothness,
		(size_t)(repeat > 0 ? repeat : 0),
		(size_t)(bias_dir > 0 ? bias_dir : 0)
	};
	try {
		olm::blur::worker::render_8bpc_nonlegacy(
			source_argb, destination_argb, width, height, params);
	} catch (const std::bad_alloc &) {
		free(source_argb);
		free(destination_argb);
		return PF_Err_OUT_OF_MEMORY;
	}

	for (size_t y = 0; y < height; ++y) {
		PF_Pixel8 *output_row = (PF_Pixel8*)((char*)output->data + y * (size_t)output->rowbytes);
		for (size_t x = 0; x < width; ++x) {
			const u_char *packed = destination_argb + (y * width + x) * 4;
			PF_Pixel8 &pixel = output_row[x];
			pixel.alpha = packed[0];
			pixel.red = packed[1];
			pixel.green = packed[2];
			pixel.blue = packed[3];
		}
	}

	free(source_argb);
	free(destination_argb);
	return PF_Err_NONE;
}

static PF_Err
render_32bpc_nonlegacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                           float blur_amount, float blur_smoothness,
	                           A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<float> source_argb(pixels * 4);
		std::vector<float> destination_argb(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				PF_PixelFloat pixel; memcpy(&pixel,source_row+x*sizeof(pixel),sizeof(pixel));
				float *packed = source_argb.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker32::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0)
		};
		olm::blur::worker32::render_nonlegacy(
			source_argb.data(), destination_argb.data(), width, height, params);

		for (size_t y = 0; y < height; ++y) {
			unsigned char *output_row = (unsigned char*)output->data + y * (size_t)output->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				const float *packed = destination_argb.data() + (y * width + x) * 4;
				PF_PixelFloat pixel;
				pixel.alpha = packed[0];
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
				memcpy(output_row+x*sizeof(pixel),&pixel,sizeof(pixel));
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
render_32bpc_legacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                       float blur_amount, float blur_smoothness,
	                       float render_scale, A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<float> source_argb(pixels * 4);
		std::vector<float> destination_argb(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				PF_PixelFloat pixel; memcpy(&pixel,source_row+x*sizeof(pixel),sizeof(pixel));
				float *packed = source_argb.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker32_legacy::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0),
			render_scale
		};
		olm::blur::worker32_legacy::render(
			source_argb.data(), destination_argb.data(), width, height, params);

		for (size_t y = 0; y < height; ++y) {
			unsigned char *output_row = (unsigned char*)output->data + y * (size_t)output->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				const float *packed = destination_argb.data() + (y * width + x) * 4;
				PF_PixelFloat pixel;
				pixel.alpha = packed[0];
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
				memcpy(output_row+x*sizeof(pixel),&pixel,sizeof(pixel));
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

