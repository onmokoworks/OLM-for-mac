# OLMKiraKira Mode 4 Diagonal 2 install / AE smoke（2026-08-12）

Status: **installed host smoke pass; AE pixel gate fail-closed**

Diagonal 2 owner-angle修正を含むUniversal（x86_64 + arm64）binary SHA-256
`39700e41d7b1c22f16fa161856c7e453ecaaf80160168c275f1785c90a622b84`を
MediaCoreへ単一installし、ad-hoc署名のdeep/strict検証を通した。旧bundleは
`/tmp/olmkirakira-d2-install-backup.DTmImn/OLMKiraKira.plugin`へ回復可能な形で退避した。

AE 26.3x87のPF32 Render Queue smokeは、このinstalled moduleを実ロードしてeffect off/onの
EXRを生成した。ただしWindows比較はno-effect側から全word不一致で、AE入力解釈は
`preserve_rgb=null`だった。従ってこれはinstalled load/apply/renderのみの証拠であり、
Diagonal 2のpixel exact claimは別のhash-bound hostless closureに限定する。
