// Appended to the real-SDK callback fixture; uses production EffectMain.
#include <fstream>
#include <sstream>
#include <string>

static bool SetScalar(PF_ParamDef *defs, int slot, double value)
{
	if (slot >= 24 && slot < OLMCOLORKEY_NUM_PARAMS) {
		const int offset = (slot - 24) % 8;
		if (offset <= 1) defs[slot].u.bd.value = (PF_Boolean)value;
		else if (offset >= 4) defs[slot].u.fs_d.value = value;
		else return false;
		return true;
	}
	switch (slot) {
	case 1: case 4: case 7: case 8: case 23:
		defs[slot].u.bd.value = (PF_Boolean)value; break;
	case 5: case 6: case 15: case 19: case 20:
		defs[slot].u.pd.value = (A_long)value; break;
	case 14: case 22:
		defs[slot].u.sd.value = (A_long)value; break;
	case 2: case 9: case 10: case 11: case 18:
		defs[slot].u.fs_d.value = value; break;
	default: return false;
	}
	return true;
}

int main(int argc, char **argv)
{
	if (argc != 6) return 90;
	const int w = atoi(argv[1]), h = atoi(argv[2]), depth = atoi(argv[3]);
	const int route = atoi(argv[4]);
	const int ps = depth == 8 ? 4 : depth == 16 ? 8 : 16, rb = w * ps + 8;
	std::vector<std::uint8_t> input((size_t)rb * h), output((size_t)rb * h, 0xee);
	if (fread(input.data(), 1, input.size(), stdin) != input.size()) return 91;
	const auto before = input;
	OLMColorKeyInfo info{};
	info.number_of_colors = 2;
	PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS]{};
	PF_ParamDef *params[OLMCOLORKEY_NUM_PARAMS]{};
	FillParams(info, defs, params);
	std::ifstream file(argv[5]);
	std::string line;
	bool seen[OLMCOLORKEY_NUM_PARAMS]{};
	while (std::getline(file, line)) {
		std::istringstream record(line);
		int slot; char kind;
		if (!(record >> slot >> kind) || slot < 1 || slot >= OLMCOLORKEY_NUM_PARAMS || seen[slot]) return 92;
		seen[slot] = true;
		if (kind == 's') {
			double value;
			if (!(record >> value) || !SetScalar(defs, slot, value)) return 93;
		} else if (kind == 'c') {
			int a, r, g, b;
			if (slot < 24 || ((slot - 24) % 8 != 2 && (slot - 24) % 8 != 3) ||
			    !(record >> a >> r >> g >> b) || a < 0 || a > 255 || r < 0 || r > 255 ||
			    g < 0 || g > 255 || b < 0 || b > 255) return 94;
			defs[slot].u.cd.value = {(A_u_char)a, (A_u_char)r, (A_u_char)g, (A_u_char)b};
		} else return 95;
		std::string extra;
		if (record >> extra) return 96;
	}
	const int count = defs[22].u.sd.value;
	if (count < 1 || count > OLMCOLORKEY_MAX_COLORS) return 97;
	for (int slot : {1,2,4,5,6,7,8,9,10,11,14,15,18,19,20,22,23})
		if (!seen[slot]) return 98;
	for (int slot = 24; slot < 24 + 8 * count; ++slot) if (!seen[slot]) return 99;
	auto in = MakeWorld(input, rb, w, h), out = MakeWorld(output, rb, w, h);
	defs[0].u.ld = in;
	HostState state; state.input = &in; state.output = &out; state.params = defs;
	state.format = depth == 8 ? PF_PixelFormat_ARGB32 : depth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
	g_host = &state;
	SPBasicSuite basic{}; basic.AcquireSuite = Acquire; basic.ReleaseSuite = Release;
	auto in_data = MakeInData(&state, &basic);
	PF_OutData out_data{}; PF_Err err;
	if (!route) err = EffectMain(PF_Cmd_RENDER, &in_data, &out_data, params, &out, NULL);
	else {
		PF_PreRenderInput pi{}; PF_PreRenderOutput po{}; PF_PreRenderCallbacks pc{}; pc.checkout_layer = CheckoutLayer;
		PF_PreRenderExtra pe{&pi, &po, &pc};
		err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in_data, &out_data, NULL, NULL, &pe);
		if (err) return 100;
		PF_SmartRenderInput si{}; si.bitdepth = depth;
		PF_SmartRenderCallbacks sc{}; sc.checkout_layer_pixels = CheckoutPixels;
		sc.checkin_layer_pixels = CheckinPixels; sc.checkout_output = CheckoutOutput;
		PF_SmartRenderExtra se{&si, &sc};
		err = EffectMain(PF_Cmd_SMART_RENDER, &in_data, &out_data, NULL, NULL, &se);
		if (state.pre != 1 || state.layer != 1 || state.output_checkout != 1 || state.layer_checkin != 1 ||
		    state.param_checkout != 17 + 8 * count || state.param_checkin != 17 + 8 * count || state.preserve) return 101;
	}
	if (input != before || state.acquire != 2 || state.release != 2 || state.world_calls != 2 || state.color_calls != 2 * count) return 102;
	fprintf(stderr, "ERROR %d\n", int(err));
	if (err) { for (auto v : output) if (v != 0xee) return 103; return 0; }
	for (int y = 0; y < h; ++y) {
		for (int b = w * ps; b < rb; ++b) if (output[(size_t)y * rb + b] != 0xee) return 104;
		if (fwrite(output.data() + (size_t)y * rb, 1, (size_t)w * ps, stdout) != (size_t)w * ps) return 105;
	}
	return 0;
}
