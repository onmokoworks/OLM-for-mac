#define main olmdirectionalblur_old_dual_probe_main
#include "probe_olmdirectionalblur_current_installed_dual_side_20260813.cpp"
#undef main

int main(int argc, char **argv)
{
	if (argc != 2) return 2;
	std::vector<unsigned char> rgba(W * H * 4, 0);
	void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
	if (!handle) return 4;
	auto candidate = reinterpret_cast<Effect>(dlsym(handle, "EffectMain"));
	if (!candidate) return 5;
	int passed = 0;
	for (int depth : {8, 16, 32}) {
		const Result source = Dispatch(SourceBuiltOLMDirectionalBlurEffectMain, depth, rgba, false);
		const Result built = Dispatch(candidate, depth, rgba, false);
		const int pixel_size = depth == 8 ? 4 : depth == 16 ? 8 : 16;
		const int padding = depth == 8 ? 12 : depth == 16 ? 16 : 32;
		const std::vector<unsigned char> untouched(
			static_cast<std::size_t>(W * pixel_size + padding) * H, 0xee);
		const bool lifecycle =
			source.pre == 2 && source.layer == 2 && source.out == 1 &&
			source.input_checkin == 1 && source.noise_checkin == 0 &&
			source.param_out == 21 && source.param_in == 21 &&
			source.preserve && source.rects;
		const bool candidate_lifecycle =
			built.pre == source.pre && built.layer == source.layer && built.out == source.out &&
			built.input_checkin == source.input_checkin &&
			built.noise_checkin == source.noise_checkin &&
			built.param_out == source.param_out && built.param_in == source.param_in &&
			built.preserve && built.rects;
		const bool exact =
			source.pre_err == PF_Err_NONE && built.pre_err == PF_Err_NONE &&
			source.render_err == PF_Err_BAD_CALLBACK_PARAM &&
			built.render_err == PF_Err_BAD_CALLBACK_PARAM &&
			source.input == built.input && source.output == untouched &&
			built.output == untouched && lifecycle && candidate_lifecycle;
		passed += exact ? 1 : 0;
		std::printf("PF%d fail_closed=%d source_err=%d candidate_err=%d\n",
			depth, exact, source.render_err, built.render_err);
	}
	dlclose(handle);
	std::printf("SUMMARY pass=%d total=3\n", passed);
	return passed == 3 ? 0 : 6;
}
