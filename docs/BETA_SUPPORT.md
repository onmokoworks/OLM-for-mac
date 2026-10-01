# Public Beta 対応範囲

この表は、現在のソースコードに実装されている「固定テスト画像に依存しない」経路を示します。
「任意画像」は画素内容を識別するSHAや固定パターン照合を行わない、という意味です。
Windows版との全設定・全画素一致を意味しません。表にない設定は、既存の固定検証経路へ入るか、
安全のため処理を拒否することがあります。

## 共通条件

- CPU Softwareレンダーが対象です。GPUレンダーは対象外です。
- プラグイン別のpointwise ROI経路を除き、入出力は同じ幅・高さ・色深度です。
  ROI経路ではworld originと各storage寸法から論理包含を検証します。いずれも各rowbytesは
  そのworldの可視画素行以上必要です。
- ROI方針はプラグイン別です。`extent_hint`はcontent boundで、storageや座標のauthorityではありません。
- 独立した入出力バッファを前提とする経路があります。
- 8／16／32 bpcは、それぞれAEのARGB32／ARGB64／ARGB128を指します。
- 新しい汎用経路は実用性を優先するベータ実装です。既存の固定fixtureはWindows oracleとの
  raw exact回帰を維持しますが、汎用経路全体についてWindows版とのbit完全一致はまだ主張しません。

## Capability matrix

| プラグイン | 任意画像のベータ経路 | 深度／経路 | geometry・stride | 対応パラメーター範囲 | 主な残存制限 | 検証状態 |
|---|---|---|---|---|---|---|
| ColorKeep | あり | Classic: 8/16、Smart: 8/16/32 | 正のgeometry、合法な独立stride。pointwise非ゼロorigin partial tile対応。depthはPixelFormatで選択し、DEEP bitは16 bpcだけ必須。AEの無関係なhost-reserved world flagsは許可 | Enabled Color Num 1–100、指定色との一致保持 | Classic 32 bpcなし。tile座標はworld originをauthorityとする | typed iterate実装済み。8/16/32 bpc・1×1〜4K sanitizer、partial tile property成功。Windows actual-AEX（SHA-256 `6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86`）はcount 5/100の末尾色境界を全3深度hostless exact。現行candidateはbaselineに加えcount 100＋100番目の色をnative AE Smart HD/4K×8/16/32で6/6通過。これは全1–100色、Classic native AE、同一frameのWindows-to-Mac数値一致を証明しない |
| OLMBlur | あり | Classic: 8/16 copy-only、Smart: 8/16/32 numerical | Classicは正のgeometry〜最大4096×2160かつUHD面積、Smartは24×24より大きく同じ辺上限。いずれも独立・非overlap stride可 | ClassicはWindows owner由来の既定tuple（Amount 5、Smoothness 100、Repeat 2。Bias/Legacyは未読）。SmartはAmount 1–1000、Smoothness 1–100、Repeat 1–10、Bias 1–2、Legacy on/off | Classic PF32はownerがPF16と識別できないため拒否。ROI counterexampleによりfull-frame以外はfail-close。Smart downsampleは1:1。4K超、高負荷条件は拒否 | Classic PF8/PF16とSmart全深度をtight stagingで成功時のみcommit。独立padded stride、overlap拒否、入力・padding保持、ASan/UBSan、hostless SD/HD/UHD成功。Windows実AEX→現行Mac SmartのAmount 5/129.4×Repeat 1/2/10×Legacy off/onは固定fixtureで3深度36/36 exact。Repeat 10＋Legacy onはnative AE Smart HD/4K×8/16/32で6/6通過。同一frameのWindows数値一致ではない |
| OLMColorKey | あり | Classic/Smart: 8/16/32 | pointwiseは非ゼロorigin partial tile対応。Thin/Blurはfull-frameのみ | pixel-local key／replace、Edge Thin −4000〜4000・Distance Type 1〜3、Inside／Around／Outside Edge Blur 0〜4000・Distance Type 1〜3とThin同時指定、既存oracle済みBlur profile | 未知internal directionは未対応。全color/threshold/HDRのexactとnative ROI/downsampleは未完。downsample 1:1 | hostless HD/4K・partial tile成功。固定13×11 actual-AEX 36-cell Thin captureはDistance Typeが内部値0のままで、公開popup 1〜3の合成根拠には使わない。current ROI v2 native quickはEdge 0。Windows実AEXのEdge Blur retained familyは3深度46-cell exact。入力一致key＋Edge Blur Amount 4／Distance Type 1／Aroundは現行Debugとbyte exactなinstalled binaryでnative AE Smart HD/4K×8/16/32を6/6通過。同一frameのWindows数値一致ではない。Inside/Outsideは元AEX公開ownerのローカル実行11232条件を現行Classic/Smartで再生しbit exact。実AE/UCRT・全color/threshold/HDRは未完 |
| OLMDirectionalBlur | 限定あり | Classic/Smart: 8/16/32 | 各辺4096以下かつ総画素数4096×2160以下、padded row可。ROIはfull-frame-normalized overscan。3 GiB per-render plugin-owned admission（64 MiB reserve込み） | Front／Backの片側または両側を各Strength 0–4000（少なくとも片側1以上）のうち、両sideのscatterを合算したgeometry別3億5000万work-unit上限内で扱う。Fade/Sharp Tail/Size Variation/Noise Variation=0。Angleは16.16 UI域、Brightness 0–10。PF8は選択した各sideの投影後effective strength 1以上、16/32はrender scale 1 | partial storageはfail-close。PF16はraw uint16 0–65535、PF32は全channel finiteを扱う。3 GiBはprocess/MFR全体の上限ではない。exact-tail等は固定union | direct／hostless EffectMainでFront／Back／Dual・全深度を確認。current canonical性能reportはHD/UHDそれぞれFront／Back／Dual×PF8/PF16/PF32の9 cases/geometryを各active Strength 2で実測し、source/toolchainの実行前後一致を確認。native AEではDual Angle 37.25・Gain 0.75・両Strength 2をHD/4K×8/16/32で6/6確認。actual-AEX raw-callback／production replay anchorはPF8 960×540・Back 240・Angle 0・Gain 1・scale 0.5で、native AE saved-frameではない。16×16 retained exact unionはPF8 Back 8・Angle 0/45・Gain 1、PF16 Back 1/2/8・Angle 45・Gain 1に加えてPF16 Dual Front 1/2/8＋Back 1・Angle 45・Gain 1、PF32 Back 1・Angle 0/45・Gain 0.5/1およびBack 8・Angle 45・Gain 1（すべてscale 1）に限定する。一般geometry・全Strength組合せ・generic DualのWindows exact・ROI v2 packageには遡及しない |
| OLMDistanceGradation | あり | Classic: 8/16/32、Smart: 8/16。Smart 32は限定 | 正のgeometry。Smart PF32は各辺4096以下かつ総画素4096×2160以下、aligned・disjoint padded rowbytes。ROIはfull-frame-normalized overscan | 8/16 typed core。Smart PF32はunblurred Constant/Linear/Sphereに加え、同3補間×Box/Gaussian/Median、Blur Size 1–500をgeometry別予算内で処理 | Smart PF32は全channel finite SDR 0–1。separable 12億／median 4億work-unit上限。partial storage、overlap、misalignment、HDR/nonfiniteはfail-close。Power/Bilateral一般laneは未対応で、最大1 ULP契約のoracle profileまたは固定unionのみ | 全Smart深度をtight staging化しcleanup成功後だけcommit。ASan/UBSan、odd、HD median、UHD Gaussian、全深度unblurred Sphere、overscan policy、PF32異常系を検証。Linear＋Gaussian Size 1はnative AE Smart HD/4K×8/16/32で6/6通過し、同tupleのWindows実AEX PF8 bounded Classic chainはexact。同一frameのWindows数値一致ではない |
| OLMKiraKira | 限定あり | Classic/Smart: 8/16/32 | full-frame、最小9×7、各辺4096以下かつ総画素4096×2160以下。合法な独立aligned padded stride。Mode 3は1 GiB per-render plugin-owned／120億work-unit上限 | oracle済みMode 1–4 tuple。追加genericはMode 3 Horizontal-only、Length 1–300、Rotation 0/1。Vertical／Diagonal／Diagonal2は0で、残りcontrolはLength 50 closureと同じneutral値 | partial ROI／tileとnon-1:1 downsampleはfail-close。PF16は0–32768、PF32はfinite 0–1。multi-ray、未列挙rotation、予算超過は拒否 | UI全300 Length×3深度=900、Classic/Smart、allocation全ordinal、HD/UHD各15 casesを検証。canonical reportはLength 300／Rotation 1を含み、source/toolchainの実行前後一致を確認。Windows actual-AEX（SHA-256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`）のhostless helper chainは代表14 Lengthの66 cases／497,250 words exact。別のexported-owner matrixでは、zero-alpha／nonzero-RGBを含む固定17×11 source、Length {1,2,50,300}×raw-fixed Rotation {0,1}×PF8/16/32の24/24がMac public EffectMain Classic/Smartとraw active-byte exact。これは全Length 1–300、任意source／geometry、Windows padded rowbytes／Classic、native Windows／macOS AE、installed plugin、native Windows UCRT／trigonometry、GPUの証拠ではない。32×18 Length 50 fixed positiveは保持し、旧fixture-only source／extent／stride negativesはgeneric safety契約に置換 |
| OLMRadialBlur | 限定あり | Classic/Smart: 8/16/32 | 正のgeometry、aligned独立stride。ROIはfull-frame-normalized overscan | baselineに加え、neutral outer-onlyのZoom/Rotationで Size Variation 25/100 × procedural Noise Variation 25/100 Type 1/2。全opaque、または画像端を含むfinite mixed-alphaの一般4連結topology | PF16はSDR 0–32768、PF32はfinite 0–1。1 GiB plugin-owned／350M work cap。partial storage、未列挙交差はfail-close | production EffectMain Classic/Smart全深度、allocation atomicity、HD/UHD各12 casesを検証。current canonical: HD 9.24 s / 261947392 B、UHD 18.75 s / 704659456 B。Windows exactは固定component anchorsのみで、portable右端処理を含む一般topology/native AE exactは未主張 |
| OLMSmoother | あり | Classic/Smart: 8/16 | 正の同寸full-frame、各辺4096以下かつ総画素4096×2160以下。独立・非overlap stride可 | Use Key on/off、Tolerance 0–255 | ROI counterexampleによりpartial tileはfail-close。32 bpcなし | tight stagingによるtransactional commit、overlap・上限超過の事前拒否、PF8/PF16 ASan/UBSan・SD/HD/4K、Smart cleanup失敗時の非commitを検証。Windows actual-AEX（SHA-256 `6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82`）のPF16 64×36 padded・Key off/on×Tolerance 6/127は、現行Classic/Smartともraw exact。PF8にはClassic owner anchorがあるが、現行SmartのWindows exact／現行RC native AEは未証明 |
| OLMSmoother2 | 限定あり | Smart: 8/16/32 | 16×16–8192×8192、独立stride。ROIはfull-frame-normalized overscan | v1/v2、Smoothness/Range/Extra各0–100、Key/Invert、Gamma None/All Colors、Gamma Colors palette count 1–5、Gamma 1.0–2.4 | partial storageはfail-close。custom/user LUTは拒否。Classic拒否。exact fixtureを汎用laneより優先。classifier近似残存 | 全深度hostless HD/4K。Gamma Colorsのpalette order／duplicate／inactive tail／alpha semanticsをhostless検証し、palette order／duplicate／toleranceにはPF16/PF32 padded 3×2 actual-AEX exact anchorがある。任意geometry・PF8・v1はhostless extrapolation。classifier 191/256はWindows exact、残る65/256はsafety-only |
| OLMToonDilate | あり | Smart: 8/16/32 | 正のgeometry、独立stride。安全上限内のfinite-halo tile対応 | finite Search Radius 0–100、正のdownsample ratio | halo不足・不正origin/stride・安全上限超過はcommit前に拒否。Classic no-op | typed tile core、halo request、transactional commit検証。Windows actual-AEXの5×5 corner seed／Radius 4代表は現行coreとPF8/PF16/PF32 active-byte exact。過去installed PF32 native AE 64×64／Radius 13は現行RC artifactへ遡及しない |

## 「検証済み」の読み方

- **Windows oracle exact**: Windows版から取得した同一入力・同一設定の出力とraw byte／wordが一致。
- **hostless**: AE SDK相当のworldとcallbackをテストハーネスで与えた検証。AEアプリ内実行とは異なります。
- **native AE**: 実際のmacOS版After Effectsでロード・適用・レンダーした検証。

現時点で新しい任意画像／一般geometryの各ベータ経路は「ソースに実装済み」の段階です。
既存fixtureのWindows oracleとhostless回帰に加え、2026-08-20のimmutable ROI v2 package
（artifact SHA-256 `7c8fb27e69ccb0a3fb2708ab026172e67050e8e15eff5acb49daf82d8f42b72b`）に
収録した10 binariesはnative AE quick smokeを10プラグインすべてで通過しました。ただし
full-frame 1920×1080・各プラグインの最初の宣言深度（今回の10件はすべて8 bpc）・
選択済みtuple各1件だけで、partial ROI／tile parityをnative AEで証明するものではありません。
この10/10証拠は上記artifactのバイナリにだけ結び付き、パッケージ後のソース／文書変更や、
全深度・Classic/Smart route・parameterの掛け合わせへ自動的に引き継がれません。
上表の汎用範囲をすべて掛け合わせたWindows oracle／native AE検証は完了していません。
したがって、重要な制作物では複製上で出力を確認してください。

さらに2026-08-22の現行Debug RC package（SHA-256
`74dd05284203287a61205a9f937e25c62731d4a07bbe6fbcecb3d951f523f80d`）について、package内と
MediaCore内がbyte exactなUniversal 10 binariesをAfter Effects 2026 `26.3x87`のSoftware rendererで
HD 1920×1080・8 bpc・選択済みtuple各1件レンダーし、10/10をconsumer-time再検証込みで通過しました。
証拠は [`olm_public_beta_rc_native_ae_quick_20260822.json`](../refs/conformance/olm_public_beta_rc_native_ae_quick_20260822.json)
です。この結果は現行RC artifactのnative AE残件を限定範囲で満たしますが、16/32 bpc、全Classic/Smart、
全parameter、SD/4K、native AE上のWindows exactを通過へ引き上げるものではありません。

その後のColorKeep現行candidate（installed binary SHA-256
`ae9643a5a02f111ac48d284d646418cb1f6c4e9b3eaf213a34c17c5698dd1a10`）では、AEが付ける
reserved world flagを固定値比較せず、PixelFormatと16 bpcのDEEP bitだけで深度整合を検証するよう修正しました。
After Effects 2026のSoftware rendererでSmart経路のHD/4K×8/16/32 bpcを6/6通過し、各publication
commitをconsumer-timeで再検証しています。証拠は
[`colorkeep_native_ae_hd_4k_all_depths_20260822.json`](../refs/conformance/colorkeep_native_ae_hd_4k_all_depths_20260822.json)
です。16 bpcは16 bpc projectでプラグインを実行後、TIFFからPNGへ変換してpublicationを検証するため、
16-bit数値出力一致の証拠ではありません。32 bpcは32 Float EXRを検証します。この6セルは既存3ゲートの
証拠であり、新しい判断基準ではありません。

2026-08-23には、上記ColorKeepを含む全10プラグインについて、各プラグインが宣言するnative AE
深度をHD 1920×1080と4K 3840×2160で実行し、合計54/54セルが成功しました。各publication
commitは生成後に独立したconsumer verifierで再検証しています。集約証拠は
[`olm_native_ae_declared_matrix_54_20260823.json`](../refs/conformance/olm_native_ae_declared_matrix_54_20260823.json)
です。Directional Blurは安全予算に従いHD Strength 48、4K Strength 8です。4K Strength 48は
350,000,000 operation-unit上限を超えるためfail-closeする既知境界であり、4K対応の失敗とは扱いません。
16 bpcは16 bpc projectで実行後にTIFFからPNGへ変換してpublication integrityを検証するため、
16-bit数値一致の証拠ではありません。32 bpcは32 Float EXRを検証します。この54セルも3ゲートを
支える証拠であり、全parameter cross-productや任意入力のWindows bit exactという追加条件ではありません。

2026-08-24にはColorKeepの別主要操作profileとして、`Enabled Color Num=100`を設定し、100番目の
palette entryへ任意gradientの画素(1,0)と同じRGBを指定しました。Smart経路のHD/4K×8/16/32 bpcを
6/6通過し、全publication commitをconsumer-timeで再検証しています。証拠は
[`colorkeep_native_ae_count100_major_ops_20260824.json`](../refs/conformance/colorkeep_native_ae_count100_major_ops_20260824.json)
です。Windows実AEX側には別途count 5/100と末尾paletteの3深度hostless exact anchorがありますが、
このnative AE 6セルと同一frameを数値比較した証拠ではありません。このprofileは既存の主要操作・実機ゲートを
支える証拠であり、新しいゲートでも固定54セルmatrixの追加セルでもありません。

同日、OLMBlurではWindows実AEX exact matrixと共通する`Amount 5 / Smoothness 100 / Repeat 10 /
Bias Vertical / Legacy on`を別主要操作profileにしました。現行Debug buildとbyte exactなinstalled binaryを
Smart経路のHD/4K×8/16/32 bpcで実行し6/6、全publication commitをconsumer-timeで再検証しています。
証拠は[`olmblur_native_ae_legacy_repeat10_major_ops_20260824.json`](../refs/conformance/olmblur_native_ae_legacy_repeat10_major_ops_20260824.json)
です。Windows anchorは同じparameter tupleを3深度でexactにしますが、fixtureとnative AE gradientの
同一frame比較ではありません。このprofileも新しいゲートや固定54セルmatrixの追加セルではありません。

OLMColorKeyでは、任意gradientの画素(1,0)をColor 1として有効化し、`Edge Blur Amount 4 /
Distance Type 1 / Direction Around`を単独主要操作profileにしました。現行Debug buildとbyte exactな
installed binaryをSmart HD/4K×8/16/32 bpcで実行し6/6、consumer-timeでも6/6再検証しています。
証拠は[`olmcolorkey_native_ae_edge_blur_major_ops_20260824.json`](../refs/conformance/olmcolorkey_native_ae_edge_blur_major_ops_20260824.json)
です。Windows実AEX側のretained Edge Blur familyは3深度46-cell exactですが、今回のgradientと
同一frameの数値比較ではありません。Edge Thinは0に保ち、既知差分であるThin＋Blur交差は含めません。
このprofileも新しいゲートや固定54セルmatrixの追加セルではありません。

OLMDistanceGradationでは、Windows実AEXのbounded Classic numerical chainと共通する
`Inside / RGB / Invert on / Inside Threshold 4 / Linear / Gaussian / Blur Size 1`を別主要操作profileに
しました。現行Debug buildとbyte exactなinstalled binaryをSmart HD/4K×8/16/32 bpcで実行し6/6、
consumer-timeでも6/6再検証しています。証拠は
[`olmdistancegradation_native_ae_linear_gaussian_major_ops_20260824.json`](../refs/conformance/olmdistancegradation_native_ae_linear_gaussian_major_ops_20260824.json)
です。Windows anchorはPF8 17×11 padded fixtureの同tupleをexactにしますが、今回のgradientとの
同一frame比較やPF16/PF32 Windows一致ではありません。Power、Bilateral、他のblur sizeとの交差も
含めず、このprofileも新しいゲートや固定54セルmatrixの追加セルではありません。

ROI v2 package reportの`beta_support_sha256`は、zip内にビルド時収録した
`OLM_Mac_Plugins_Release/BETA_SUPPORT.md`のimmutable manifest hashです。現在閲覧中の
`docs/BETA_SUPPORT.md`は、その後の検証結果を追記するlive文書であり、同じhashを持つ必要はありません。
live文書のhashでpackage manifest値を置き換えることもありません。

2026-08-21時点では、ColorKeepの8/16/32 bpcについて1×1から4Kまでの
AddressSanitizer／UndefinedBehaviorSanitizer検証が成功しています。current live-sourceの
worker callbackは、同一Windows AEX SHAから取得した5色のunrolled／scalar-tail代表について、
PF8／PF16／PF32それぞれの一致3ケースと不一致1ケースをtracked reportから再生し、出力単位／float bitがexactです。
この接続自体はhostlessなone-pixel worker oracleです。現行RC packageのAfter Effects内レンダー証拠は
上記quick smokeです。後続candidateのSmart全深度HD/4K証拠は上記6セルですが、同じ5色worker cellの
native AE数値一致を主張するものではありません。
current live-sourceの
canonical hostless性能reportは全10プラグイン×HD/UHDの20セルを実測し、20/20成功しました。
Directionalは各geometryでFront／Back／Dual×PF8/PF16/PF32の9 casesを各active Strength 2で実行し、
3 profileを同時に隠すidentity fallbackを避ける非対称入力とpairwise出力差も検査します。reportはproduction／driver／toolchainを
実行前後でhash照合し、exact matchでない測定を成功扱いにしません。対応セルはすべて成功を要求し、
非対応セルはreasonとsupport predicate付きで明示します。未計測セルを成功扱いにしていません。
KiraKiraは各geometryでMode 1／2／3／4の既存代表4件に、Mode 3 Horizontal Length 300・Rotation 1を
全深度で加えた15 casesを実行します。current reportではHD 40.20秒／peak 487,194,624 bytes、
UHD 151.27秒／peak 1,492,664,320 bytesで、各caseのSmart対Classic parity、Classic再実行の決定性、
独立stride、input／padding不変、active output変更を確認しました。これはHD/UHDの実測であり、
budget predicateが許可するDCI 4096×2160 endpointの実測やWindows／native AE数値一致ではありません。
このhostless性能証拠は、上記immutable ROI v2 packageへ後付けされるnative AE証拠ではなく、
Windows oracleやnative AE検証の代替ではありません。

追加の24-cell Windows-owner証拠では、actual Windows `OLMKiraKira.aex`のexported
`SmartPreRender`→`SmartRender` ownerをmacOS上のAEXCompat／Unicorn x86_64 backendでhostless実行し、
current Mac production sourceのpublic `EffectMain` Classic／Smartとactive bytesのSHA-256を比較しました。
固定17×11 sourceにはalpha 0かつRGB非ゼロの画素を含み、Length {1,2,50,300}、owner raw-fixed
Rotation {0,1}、PF8／PF16／PF32の24/24が3経路でexactです。workerはAEXCompat commit
`28d535469f84f67236ef3425afe4291ea2fb0991`のexact checkout内targetをCargo `--frozen`でbuildした
SHA-256 `fe376e9ba1d6ee1f20cd9b6954d63542555ed4ffd52a0dfb5e8c95d1f4ccdffe`
（3,886,128 bytes）で、reportはcargo／rustc 1.95、source/build identity、actual-AEX、公式配布ZIPを
cross-bindします。canonical report SHA-256 `50bbf05233f985608e4e320473970e734987d60ffd9e1d859c63bd10b1d8f687`
は独立sidecarに固定し、既定verifierは協調したcell hash書換えやJSON型混同もfail-closeします。
AEXCompat側はtight rowbytesで、Rotation 1のtrigonometry importはhost代替です。
したがって、これは全Length 1–300、任意source／geometry／tuple、Windows padded rowbytes／Classic、
native Windows／macOS AE、installed plugin、native Windows UCRT／trigonometry、GPUを証明しません。
Adobe SDK／symlinked Util／Mac system SDK・compiler・standard libraryもin-repo source closureの対象外です。

日常の変更ではhostless、sanitizer、generic gateを実行します。native AEの54-case smokeは
毎変更ではなく、milestoneまたはrelease candidateでまとめて実行する運用です。
今回の10-case quick smokeもmilestone確認であり、54-case smokeの代替ではありません。証拠は
[`olm_all10_roi_v2_quick_ae_smoke_20260820.json`](../refs/conformance/olm_all10_roi_v2_quick_ae_smoke_20260820.json)です。

## 主要操作ゲートを「通過」へ引き上げる証拠範囲

Public Betaの判断基準は [PUBLIC_BETA_3_GATES.md](PUBLIC_BETA_3_GATES.md) の3本だけです。
次は「主要操作」ゲートを現在の`限定`から`通過`へ引き上げるための証拠内訳であり、追加ゲートではありません。

- 8/16/32 bpcのうち表で対応する全深度
- 透明、単色、impulse、gradient、seed固定randomの5入力
- 小型奇数、SD、HD、縦長、4Kを含むgeometry
- tight、padding付き、入力/outputで異なる合法stride
- 対応parameter範囲の最小、既定、中間、最大、境界値
- クラッシュ、範囲外アクセス、padding破壊、失敗時の部分commitが0件
- 既存のWindows exact fixture回帰が100%成功
- macOS版AEで少なくともHDと4Kのnative renderを確認

固定fixtureごとの詳細な証拠と研究上の制限は、[既知の制限](../KNOWN_LIMITATIONS.md)を参照してください。

## 次フェーズ: ROI／tile／halo

現Public Betaの完了監査は[`public_beta_completion_audit_20260820.json`](../reports/public_beta_completion_audit_20260820.json)にあります。
現在、ColorKeep／ColorKeyのpointwise経路は非ゼロoriginのpartial tile、ToonDilateは安全上限内の
finite-halo tileを検証済みです。Distance Gradation／Directional Blur／Radial Blur／Smoother2は
full-frameへ正規化したoverscanを要求し、hostがpartial storageしか返さない場合は処理前に拒否します。
Blur／KiraKira／Smoother v1はcounterexampleに基づきfull-frame以外をfail-closeします。
`extent_hint`はcontent boundであり、storageや座標のauthorityとしては扱いません。

AEXCompatの非HD checkpointは14/14成功しています。HD checkpointは5/7成功しています。
ToonDilateのradius 2.01／5は未実行で、radius 0が281.765秒だったためcampaignの時間予算上
延期しました。2件の所要時間は未計測です。これはmacOS上のhostless AEXCompat証拠で、
native Windows／After Effects実行ではありません。
残作業の優先順は、(1) HD Toon 2件の性能実行、(2) overscan 4 laneのhost storage実証、
(3) counterexample 3 laneの全画面依存を解くことです。各laneのROI完了条件は次のとおりです。

- full-frame出力と、同じframeを複数のROI／tileへ分割して合成した出力が対応全深度で一致する
- 必要haloをparameterから決定し、画像端でclamp／repeat等の既存境界規則を維持する
- 非ゼロorigin、独立stride、padding、奇数寸法、縦長、HD、4Kを通す
- ROI外の出力とpaddingを変更せず、拒否時は部分commitしない
- 最小／既定／最大の対応parameterでASan／UBSan clean、決定性100%、既存fixture回帰100%
- native AEで少なくとも局所系1 laneと境界依存系1 laneのtile renderを確認する
