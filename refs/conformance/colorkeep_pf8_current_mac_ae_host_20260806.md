# ColorKeep PF8 current Mac AE host result

The current Universal ColorKeep binary (`ccc897…17cce`) loaded in After Effects 26.3x87 and rendered the five-key PF8 fixture through the Software path.

AE enforces a minimum 4×4 composition, so the 4×3 reference source is placed at the top-left without resampling. The extra bottom row is required to remain transparent black.

The host export proves:

- exact alpha for all 12 source pixels;
- exact RGBA for every non-transparent source pixel;
- exact loaded-module path and SHA-256 via external `vmmap`;
- exact parameter surface/readback for the five enabled keys.

`saveFrameToPng` zeroes RGB whenever alpha is zero. Therefore hidden RGB is not observable in the AE PNG. A separate test directly loads the same installed Mach-O and invokes its PF8 worker on the identical 4×3 fixture; all 48 raw ARGB8 bytes, including hidden RGB, match the actual Windows AEX fixture.

`ae_exact_claim` remains false: this is a composed host-export plus installed-worker proof, not a raw hidden-RGB observation from AE itself. The result is limited to this PF8 case, AE version, renderer, input, and parameter set.
