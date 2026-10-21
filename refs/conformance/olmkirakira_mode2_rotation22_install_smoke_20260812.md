# OLMKiraKira Rotation 22° install / AE smoke（2026-08-12）

Status: **installed host smoke pass; AE pixel gate fail-closed**

Universal（x86_64 + arm64）かつstrict codesign済みのbinary SHA-256
`3ff1d6ed30922d869f0368e73d9a529f3c52f7ce27bb2d5acefd7c8fd16afb0a`を
MediaCoreへ単一installした。AE 26.3x87は全10プラグインをload/applyし、Kira専用Render Queue経路は
このinstalled moduleをロードしてeffect off/onのPF32 EXRを生成した。

ただし共通`saveFrameToPng` smokeは全10本でPNGを作らず、Render QueueのWindows比較もno-effect側から
全word不一致（`preserve_rgb=null`）だった。したがってMac AE pixel exactへは昇格せず、ここで証明するのは
installed load/apply/renderだけである。Rotation 22°のpixel exact claimは別のhash-bound hostless closureに限定する。
