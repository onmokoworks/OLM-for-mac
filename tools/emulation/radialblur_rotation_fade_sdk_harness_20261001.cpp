// Exercise the actual production fade helper with the real SDK definitions.
#include "production_under_test.cpp"

int main()
{
    int length;
    while (std::scanf("%d", &length) == 1) {
        if (length < 1 || length > 99) return 2;
        const auto weights = RotationFadeGaussianWeights((A_long)length);
        for (float weight : weights) {
            unsigned bits; std::memcpy(&bits, &weight, 4);
            std::printf("%08x", bits);
        }
        std::printf("\n");
    }
    return std::ferror(stdin) ? 1 : 0;
}
