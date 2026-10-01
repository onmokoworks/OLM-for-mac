// Execute the production enabled helper with the same rounded getter input.
#include "production_under_test.cpp"
#include <cinttypes>

int main()
{
    uint64_t word;
    while (std::scanf("%" SCNx64, &word) == 1) {
        double percentage; std::memcpy(&percentage, &word, sizeof(percentage));
        const float getter = (float)percentage;
        const float normalized = RadialF32Mul(getter, 0.01f);
        uint32_t getter_word, normalized_word;
        std::memcpy(&getter_word, &getter, sizeof(getter_word));
        std::memcpy(&normalized_word, &normalized, sizeof(normalized_word));
        std::printf("%08" PRIx32 " %08" PRIx32 " %d\n", getter_word,
                    normalized_word, (int)RadialSizeVariationEnabled(percentage));
    }
    return std::ferror(stdin) || std::ferror(stdout) ? 1 : 0;
}
