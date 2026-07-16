import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"


def render_typed(source, depth, search_radius=1.0, comp_width=None):
    """Small portable model for the typed Mac core contract."""
    height = len(source)
    width = len(source[0])
    output = [[pixel for pixel in row] for row in source]
    maximum = {8: 255, 16: 32768, 32: 1.0}[depth]
    opaque = lambda pixel: pixel[3] == maximum if depth in (8, 16) else pixel[3] >= 1.0
    radius = int(__import__("math").ceil(search_radius * width / (comp_width or width)))
    distances = [[2**32 - 1] * width for _ in range(height)]

    for y in range(height):
        for x in range(width):
            if opaque(source[y][x]):
                distances[y][x] = 0

    def relax(x, y, coordinates):
        if distances[y][x] == 0:
            return
        best = 2**32 - 1
        best_xy = None
        for nx, ny in coordinates:
            if 0 <= nx < width and 0 <= ny < height:
                distance = distances[ny][nx]
                if distance < best:
                    best = distance
                    best_xy = (nx, ny)
        if best_xy is None or best + 1 >= distances[y][x]:
            return
        candidate = best + 1
        distances[y][x] = candidate
        if candidate <= radius:
            nx, ny = best_xy
            output[y][x] = output[ny][nx]

    for y in range(height):
        for x in range(width):
            relax(x, y, ((x - 1, y), (x - 1, y - 1), (x, y - 1), (x + 1, y - 1)))
    for y in range(height - 1, -1, -1):
        for x in range(width - 1, -1, -1):
            relax(x, y, ((x + 1, y), (x + 1, y + 1), (x, y + 1), (x - 1, y + 1)))

    return output


class ToonDilateTypedCoreTests(unittest.TestCase):
    def test_source_keeps_explicit_smart_depth_dispatch(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("PF_OutFlag2_FLOAT_COLOR_AWARE", source)
        self.assertIn("RenderTyped<PF_Pixel16>", source)
        self.assertIn("RenderTyped<PF_PixelFloat>", source)
        self.assertIn("RenderWorld(input_world, output_world, info, extra->input->bitdepth)", source)
        self.assertIn("PF_PixelFormat_ARGB32", source)
        self.assertIn("PF_PixelFormat_ARGB64", source)
        self.assertIn("PF_PixelFormat_ARGB128", source)
        self.assertNotIn("premultiply_semi_alpha", source)

    def test_16bpc_opaque_seed_and_boundary_are_integer_exact(self):
        transparent = (0, 0, 0, 0)
        seed = (32768, 12345, 5432, 32768)
        source = [[transparent] * 3 for _ in range(3)]
        source[1][1] = seed
        result = render_typed(source, 16)
        self.assertEqual(result, [[seed] * 3 for _ in range(3)])

        corner_source = [[transparent] * 3 for _ in range(3)]
        corner_source[0][0] = seed
        corner = render_typed(corner_source, 16)
        self.assertEqual(corner[0][0], seed)
        self.assertEqual(corner[1][1], seed)
        self.assertEqual(corner[2][2], transparent)

    def test_8bpc_semi_alpha_rgb_survives_without_postpass(self):
        semi = (201, 101, 51, 128)
        source = [[semi, semi]]
        self.assertEqual(render_typed(source, 8), source)

    def test_16bpc_semi_alpha_is_not_seed_and_rgb_survives(self):
        semi = (32767, 32769, 65535, 16384)
        source = [[semi, (0, 0, 0, 0), (100, 200, 300, 32768)]]
        result = render_typed(source, 16)
        self.assertEqual(result[0][0], semi)
        self.assertEqual(result[0][1], source[0][2])

    def test_float_seeded_live_pattern_preserves_out_of_radius_semi_rgb(self):
        semi = (0.8, 0.4, 0.2, 0.25)
        opaque = (0.1, 0.2, 0.3, 1.0)
        source = [[opaque, (0.6, 0.3, 0.15, 0.5), semi]]
        result = render_typed(source, 32)
        self.assertEqual(result[0][1], opaque)
        self.assertEqual(result[0][2], semi)


if __name__ == "__main__":
    unittest.main()
