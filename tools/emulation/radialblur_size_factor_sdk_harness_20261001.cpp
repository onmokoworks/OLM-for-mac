// Invoke the actual size-factor helper using typed SDK worlds.
#include "production_under_test.cpp"
#include <fstream>

int main(int argc, char **argv)
{
    if (argc != 6) return 2;
    const int w = std::atoi(argv[1]), h = std::atoi(argv[2]), depth = std::atoi(argv[3]);
    if (w <= 0 || h <= 0 || w > 100 || h > 100) return 3;
    const float size = std::strtof(argv[4], nullptr);
    const size_t pixel_size = depth == 8 ? sizeof(PF_Pixel8) : depth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat);
    if (depth != 8 && depth != 16 && depth != 32) return 4;
    std::vector<unsigned char> raw((size_t)w*h*pixel_size);
    std::ifstream input(argv[5], std::ios::binary); input.read((char*)raw.data(), raw.size());
    if (input.gcount() != (std::streamsize)raw.size()) return 5;
    PF_EffectWorld world{}; world.data=(PF_PixelPtr)raw.data(); world.width=w; world.height=h; world.rowbytes=(A_long)(w*pixel_size);
    std::vector<float> factors; std::vector<A_long> areas;
    bool ok = depth == 8 ? BuildRadialSizeFactorPlaneAEX<PF_Pixel8>(&world,size,&factors,&areas)
        : depth == 16 ? BuildRadialSizeFactorPlaneAEX<PF_Pixel16>(&world,size,&factors,&areas)
        : BuildRadialSizeFactorPlaneAEX<PF_PixelFloat>(&world,size,&factors,&areas);
    if (!ok || factors.size() != (size_t)w*h+1 || factors.back() != 0.0f) return 6;
    std::fprintf(stderr, "AREAS"); for (A_long area : areas) std::fprintf(stderr, " %d", (int)area); std::fprintf(stderr, "\n");
    std::fwrite(factors.data(), sizeof(float), (size_t)w*h, stdout);
    return std::ferror(stdout) ? 7 : 0;
}
