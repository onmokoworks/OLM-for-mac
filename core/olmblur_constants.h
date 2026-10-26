#pragma once

namespace olm::blur {
// Six original worker partitions (e.g. AEX 0x180003710); preserve carry boundaries.
constexpr int kPassParts = 6;
// Final partition receives the remainder in AEX 0x180003710.
constexpr int kLastPassPart = 5;
// Radius-to-sigma divisor and repeated-radius target, AEX 0x180003710/0x180007300.
constexpr float kSigmaDivisor = 3.0f;
// Smoothness percentage denominator, Legacy worker AEX 0x180007300.
constexpr float kSmoothnessPercent = 100.0f;
// Coefficient allocation padding, Non-Legacy worker AEX 0x180003710.
constexpr int kRadiusPadding = 2;
// Add-half before floor/CVTTSS2SI, AEX writers 0x180006cf3/0x180007fdf.
constexpr float kRoundingHalf = 0.5f;
// Inclusive signed conversion minimum, CVTTSS2SI at AEX 0x180006cf3/0x180007fdf.
constexpr float kInt32LowerBound = -2147483648.0f;
// Exclusive signed conversion maximum, CVTTSS2SI at AEX 0x180006cf3/0x180007fdf.
constexpr float kInt32UpperBound = 2147483648.0f;
// Previous-sample RGB seed, AEX DAT_18000d27c in helpers 0x1800014f0/0x180001ea0.
constexpr float kLegacyCarrySentinel = -1.0f;
// Native scheduling threshold introduced with the ec6cc82c parallel split; not AEX arithmetic.
constexpr int kParallelMinDimension = 256;
}  // namespace olm::blur
