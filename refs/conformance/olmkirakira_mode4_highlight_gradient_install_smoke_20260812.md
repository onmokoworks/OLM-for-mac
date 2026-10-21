# OLMKiraKira Mode 4 Highlight gradient install / AE smoke（2026-08-12）

Status: **installed host smoke pass; AE pixel gate fail-closed**

Highlight box-filter修正を含むUniversal（x86_64 + arm64）binary SHA-256
`136ca31b2a2f75bd2dc624bbba4f907e29214202af80926c091abcef536f5c92`を
MediaCoreへ単一installし、ad-hoc署名のdeep/strict検証を通した。旧bundleは
`/tmp/olmkirakira-highlight-install-backup.ed3Bpp/OLMKiraKira.plugin`へ回復可能な形で退避した。

AE 26.3x87はinstalled moduleを実ロードし、Highlight Radius 5のparameterを適用して
PF32のeffect off/on EXRを両方生成した。ただしWindows比較はno-effect側から
6,220,800 words全てが不一致で、AE入力解釈は`preserve_rgb=null`だった。
従ってこれはinstalled load/apply/renderの証拠に限り、pixel exact主張は別の
hash-bound 5×3 / Radius 3 / kernel 7 hostless closureに限定する。
このhostless closureは後続のPF8入力decode限定修正後にも再検証した。その後さらに
Smart bounded promotionが入り、mutable workspace sourceはこのinstall時点から進んでいる。
installed binaryそのもののidentityは、このsmokeが記録した当時のproduction source SHAと
binary SHAだけに束縛する。本書は現在のsource SHA、現在のon-disk MediaCore identity、
またはSmart候補のinstall／native-AE numerical exactを主張しない。

Raw AE report: `olmkirakira_mode4_highlight_gradient_install_smoke_raw_20260812.json`
（SHA-256 `a335c37dc1825699ae444ad824db6676dc7c180196df22ac6abc147e4dabda10`）。
`loaded_module_identity_exact`は、raw reportが記録したmapped pathが単一でinstalled pathと
一致し、そのpathのon-disk binaryをsmoke前後に別途SHA固定したという境界である。
