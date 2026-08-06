# ColorKeep PF16 upstream fixture-source scaffold

No existing diagnostic effect in the repository writes arbitrary extended
`PF_Pixel16` words into an AE-managed world.  A test-only bounded source effect
has therefore been scaffolded under `tools/ae_pf16_fixture_source`; ColorKeep
production is unchanged.

The effect exposes match name `OLM Test PF16 Fixture Source`, declares only
deep-color awareness, and implements the legacy `PF_Cmd_RENDER` path.  In a
16bpc host world it writes the same twelve active ARGB16 words used by the
honest ColorKeep host fixture and transparent black outside the top-left 4x3
footprint.  It rejects non-deep worlds rather than silently quantizing them.

The Universal build succeeded without installation:

- verified rebuild binary SHA-256: `d274e6b05f9bcbe413807b4ead19bfda1ea45b02a27b2510cd915d9068e0ee63`
- architectures: `x86_64 arm64`
- source SHA-256: `7dbd851cab1be7855d2d5145657ec22ce4f816f95e3e157441cf3f0ecc9cfd48`
- strict ad-hoc codesign verification: pass

The exported `EffectMain` was dynamically loaded outside AE and invoked with a
4x3 deep world using rowbytes 40.  All 120 bytes were exact, including the
three untouched eight-byte padding regions.  Payload SHA-256:
`a6fb865bc873cc7c38f32251a3767a01b5d089cef3a2bd9422255b4c6e7417f7`.

It has not been copied into any Adobe plug-in directory and has not been loaded
by AE.  The safe next host step is:

1. Stop AE after all other lanes release it.
2. Install this bundle as the sole `OLMPF16FixtureSource.plugin`, recording its
   exact hash and keeping it separate from all OLM production bundles.
3. Start fresh AE and prove exact mappings for both the fixture source and
   current ColorKeep.
4. Apply fixture source first and ColorKeep second to a 4x4 16bpc Software comp.
5. Render a fixture-source-only control and the two-effect output through the
   FLOAT EXR output module.  The control must demonstrate that AE passes the
   extended PF16 words between effects before ColorKeep is evaluated.
6. Compare the ColorKeep output to the actual-AEX active-pixel fixture.  Keep
   the existing installed-public 120-byte/padding proof as a separate leg.

No AE or ColorKeep exact claim is made by this scaffold.
