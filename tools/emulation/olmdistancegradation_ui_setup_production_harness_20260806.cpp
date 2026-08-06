#include <cstdio>
#include <cstring>

#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

static bool first = true;

static PF_Err capture_param(PF_ProgPtr, PF_ParamIndex, PF_ParamDefPtr def)
{
	if (!first) std::putchar(',');
	first = false;
	std::printf("{\"disk_id\":%u,\"ui_flags\":%u,\"ui_width\":%u,\"ui_height\":%u,"
	            "\"param_type\":%u,\"name\":\"%s\",\"flags\":%u",
	            (unsigned)def->uu.id, (unsigned)def->ui_flags,
	            (unsigned)def->ui_width, (unsigned)def->ui_height,
	            (unsigned)def->param_type, def->name, (unsigned)def->flags);
	switch (def->param_type) {
	case PF_Param_CHECKBOX:
		std::printf(",\"checkbox\":[%d,%d]", (int)def->u.bd.value, (int)def->u.bd.dephault);
		break;
	case PF_Param_POPUP:
		std::printf(",\"popup\":[%d,%d,\"%s\"]", (int)def->u.pd.num_choices,
		            (int)def->u.pd.dephault, def->u.pd.u.namesptr);
		break;
	case PF_Param_SLIDER:
		std::printf(",\"slider\":[%d,%d,%d,%d,%d,%d]", (int)def->u.sd.value,
		            (int)def->u.sd.valid_min, (int)def->u.sd.valid_max,
		            (int)def->u.sd.slider_min, (int)def->u.sd.slider_max,
		            (int)def->u.sd.dephault);
		break;
	case PF_Param_COLOR: {
		unsigned current = 0, dephault = 0;
		std::memcpy(&current, &def->u.cd.value, 4);
		std::memcpy(&dephault, &def->u.cd.dephault, 4);
		std::printf(",\"color\":[%u,%u]", current, dephault);
		break;
	}
	case PF_Param_FLOAT_SLIDER:
		std::printf(",\"float_slider\":[%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%d,%d,%u,%.17g,%d,%.17g]",
		            def->u.fs_d.value, def->u.fs_d.valid_min, def->u.fs_d.valid_max,
		            def->u.fs_d.slider_min, def->u.fs_d.slider_max, def->u.fs_d.dephault,
		            (int)def->u.fs_d.precision, (int)def->u.fs_d.display_flags,
		            (unsigned)def->u.fs_d.fs_flags, def->u.fs_d.curve_tolerance,
		            (int)def->u.fs_d.useExponent, def->u.fs_d.exponent);
		break;
	default:
		return 92;
	}
	std::putchar('}');
	return PF_Err_NONE;
}

int main()
{
	PF_InData in_data{};
	PF_OutData global_out{};
	PF_OutData params_out{};
	in_data.effect_ref = reinterpret_cast<PF_ProgPtr>(0x1234);
	in_data.inter.add_param = capture_param;
	int global_error = EffectMain(PF_Cmd_GLOBAL_SETUP, &in_data, &global_out, nullptr, nullptr, nullptr);
	std::printf("{\"global\":{\"error\":%d,\"my_version\":%u,\"out_flags\":%u,\"out_flags2\":%u},"
	            "\"params\":{\"rows\":[", global_error, (unsigned)global_out.my_version,
	            (unsigned)global_out.out_flags, (unsigned)global_out.out_flags2);
	int params_error = EffectMain(PF_Cmd_PARAMS_SETUP, &in_data, &params_out, nullptr, nullptr, nullptr);
	std::printf("],\"error\":%d,\"num_params\":%d}}\n", params_error, (int)params_out.num_params);
	return global_error || params_error ? 1 : 0;
}
