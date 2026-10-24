// Inspect the production helper before normalization, in the same translation unit.
#include "../../../core/olmdistancegradation_fieldgen.cpp"
#include <cstdio>
int main(int argc, char** argv) {
    if (argc != 4) return 64;
    const size_t w = std::strtoul(argv[1], nullptr, 10);
    const size_t h = std::strtoul(argv[2], nullptr, 10);
    std::vector<unsigned char> mask(w*h);
    if (std::fread(mask.data(), 1, mask.size(), stdin) != mask.size()) return 65;
    std::vector<float> field(w*h);
    olm::distancegradation::precise_l2_edt(mask.data(), w, h, field.data());
    FILE* out = std::fopen(argv[3], "wb");
    if (!out) return 66;
    const bool ok = std::fwrite(field.data(), sizeof(float), field.size(), out) == field.size();
    std::fclose(out);
    return ok ? 0 : 67;
}
