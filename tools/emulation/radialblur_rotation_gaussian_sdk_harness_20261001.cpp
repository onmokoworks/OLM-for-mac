// Exercise actual production Gaussian helpers from exact argument bits.
#include "production_under_test.cpp"

int main()
{
    char operation;
    unsigned argument;
    while (std::scanf(" %c %x", &operation, &argument) == 2) {
        if (operation == 'E') {
            float exponent; std::memcpy(&exponent, &argument, 4);
            const float result = RotationGaussianSIMDExp(exponent);
            unsigned output; std::memcpy(&output, &result, 4);
            std::printf("%08x\n", output);
        } else if (operation == 'W') {
            const auto weights = RotationGaussianWeights((A_long)argument);
            for (const float weight : weights) {
                unsigned output; std::memcpy(&output, &weight, 4);
                std::printf("%08x", output);
            }
            std::printf("\n");
        } else return 2;
    }
    return std::ferror(stdin) ? 1 : 0;
}
