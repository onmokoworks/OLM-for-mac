#include <cstdlib>
#include <fstream>
#include <iterator>
#include <vector>

#define EffectMain SourceBuiltColorKeepEffectMain
#include "../../mac/ColorKeep/ColorKeep.cpp"
#undef EffectMain

int main(int argc,char **argv)
{
	if (argc != 5) return 2;
	const short depth = (short)std::atoi(argv[1]);
	const A_long count = (A_long)std::atoi(argv[2]);
	const A_long rowbytes = (A_long)std::atoi(argv[3]);
	std::ifstream stream(argv[4], std::ios::binary);
	std::vector<unsigned char> payload((std::istreambuf_iterator<char>(stream)), {});
	if (payload.size() != (size_t)rowbytes * 7) return 3;
	PF_EffectWorld world{};
	world.data = reinterpret_cast<PF_PixelPtr>(payload.data());
	world.width = 11; world.height = 7; world.rowbytes = rowbytes;
	return ColorKeepLegacySourceMatches(&world, depth, count) ? 0 : 4;
}
