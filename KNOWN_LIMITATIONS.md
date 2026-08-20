# OLM for Mac Public Beta — 既知の制限

このベータは、Windows版OLM Toolsの全入力・全geometry・全パラメーター直積に対する
完全互換を保証しません。`Exact`は、証拠に記録されたAEバージョン、レンダー経路、
色深度、入力、geometry、設定値におけるbyte／raw word一致を意味します。

## 共通

- 主な検証環境はAfter Effects 26.3x87、CPU Software、working space None、linear
  blending offです。
- macOS 15.7.2 arm64の最新最小host smokeでは全10プラグインのロード、適用、
  64×64 PNGレンダーが成功しています。この結果はhost smokeであり、Windowsとの
  pixel exactや主要パラメーター設定の一致を証明するものではありません。
- AEの素材import、premultiply／unpremultiply、色管理、codec、EXR出力はWindowsと
  macOSで異なる場合があります。同じプラグイン演算でも最終ファイルが一致しないことが
  あります。
- GPUレンダー、異なるAEバージョン、第三者ホストは互換性主張の対象外です。
- 現在のbundleはUniversal／ad-hoc署名を確認していますが、Developer ID署名とApple
  notarizationは未実施です。ダウンロード先のMacでGatekeeperに拒否される可能性があります。
- 未証明の設定では、安全のためエラーを返す、処理を拒否する、または限定経路へ入る場合が
  あります。
- 公開パラメーターの順序・型・名前・初期値・範囲はactual AEXの30定義と比較しています。
  一方、Windows版と同じcustom preview描画、クリック操作、動的ラベルのEVENT／UPDATE
  経路は未移植・未証明です。現行Mac版は、それらのcustom UI capabilityをAEへ広告しません。

## プラグイン別

- ColorKeep：actual Windows exported Smart owner、現行installed Mac public
  `EffectMain`、isolated Universal candidateは、固定11×7／row padding 12、固定
  100色palette、Enabled Color Num 5／100のPF8／PF16／PF32計6セルでactive raw
  exactです。Mac public経路は入力全体・world header・入出力padding不変と101
  parameter checkout/checkinを確認しています。本番admissionはこの境界だけで、
  Classic PF32、他geometry／rowbytes／palette／countはfail-closeです。この従来laneは
  count9追加後も変更していません。別のcount9 laneは固定4×3／padding 8、深度別rowbytes
  24／40／72、exact active sourceと9色paletteだけをadmitします。production sourceは
  `d1c44304...bac3`で、従来laneも深度/count別exact active-source SHAへ固定しました。Windows exported Smart PF8／PF16／PF32とMac public Classic
  PF8／PF16・Smart PF8／PF16／PF32がraw exactです。136件のcanonical rejectは
  131件のpre-iterate拒否と5件の制御されたiterate failureで、すべてpublic destinationを
  保持します。Classic PF32、任意source／palette／geometry／strideへの一般化は
  ありません。現行installed executableは`dae59a6f...f46d`、Info.plistと両sliceのminimum
  macOSは11.0です。fresh AEはColorKeepをeffect-disabledでload／add／single-path mapping
  しただけで、count9 numerical renderは実行も主張もしていません。
  証拠は[`colorkeep_nine_color_public_closure_20260813.md`](refs/conformance/colorkeep_nine_color_public_closure_20260813.md)、
  [`colorkeep_source_bound_complete_union_install_20260813.md`](refs/conformance/colorkeep_source_bound_complete_union_install_20260813.md)、
  [`olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813.json`](refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813.json)です。
- OLMBlur：従来のexact 24×24 source、rowbytes 113／215／416、Amount 5、Smoothness 100、
  Repeat 1、Bias 1、Legacy 0／1のPF8／PF16／PF32 6セルに加え、PF16 NonLegacyの固定source
  7セルだけをSmart public admissionへ追加しました。NonLegacyは7×5／rowbytes69／Amount4／
  Repeat1、12×12／rowbytes109／Amount3／Repeat1とRepeat2、18×18／rowbytes157／Amount11／
  Repeat1とRepeat3／Bias2です。Legacyは12×12／Amount3／Repeat2／Bias1、18×18／Amount11／Repeat3／Bias2、
  18×12 mixed-alpha／rowbytes157／Amount3／Repeat2／Bias2です。全てSmoothness100です。
  これらはWindows actual AEXのexported
  SmartPreRender／SmartRenderとMac source-included EffectMainでactive output／paddingまで
  raw exactです。PF16は8/8セルで、Mac closureは合計16正例と494件のcell別source／tuple／world／callback
  one-awayを確認し、失敗時は入力不変・destination全保持です。
  PF16 writerはactual AEXのfloor後low-word storeへ合わせていますが、未列挙のsource、tuple、
  geometry、layoutへの一般化はしません。Legacy 20×16 Smooth62.5はWindows exported ownerの
  signed integer-part materializationをexact admission内だけ再現します。PF16追加段階のsource
  `f8db5a6d...30f1`とUniversal候補`e8a916a8...a3e2`は履歴です。さらにPF8の固定source
  12セルを追加し、24正例／744 fail-closeを確認しました。PF32 retainedも20/20で、
  40正例／60 fail-closeです。3つのfractional Smoothnessセルはいずれも同じbounded整数化です。
  現行sourceは`22eb712a...fdd7`、Universal候補`ecdf3d93...284d`はbatch5で
  full-inventory exactにinstall済みです。旧batch4版`5893faea...c48b`は3コピー保持され、
  新セルのAE／aerender／native-host numerical claimはまだありません。classic
  `PF_Cmd_RENDER`は従来どおり固定24×24/default PF8/PF16 copy-onlyだけを許可します。
- OLMColorKey：Edge Blurのexact証拠には、記録済みの小型geometry、multi-key、および
  半透明入力のAmount 2／Direction 1〜3／Distance Type 1〜3が含まれます。
  半透明endpointのDirection 0／4、Amount 1／4、Distance Type 2も12行exactです。
  Direction 0／4、Distance Type 1／3のcoveringを含むmatrixは51／51 exactですが、
  PF32 Amount 4は記録済みshell限定です。任意geometry、amount、方向、distance typeの
  全直積は未証明です。64×36の記録済み4 tupleは12／12 exactで、PF32 Type 3の
  float distance multiply→double sin→float plane構築順を含みますが、任意geometryへは
  一般化しません。Lab76の記録済み2-key順序反転fixtureは、Windows comparatorの
  destructive a/b mutationとfloat32 Euclidean判定を再現し、PF8／PF16／PF32の6／6
  public owner出力がraw exactです。これは任意key数／threshold／Lab設定へ一般化しません。
  現行source public admissionはsource bytesまで固定したEdge Blur 33セル（48×27 D0/T3/A4の3深度を含む）、Lab76 6セル、固定11×7の
  Keep／Premultiplied／Replace 24セルです。real-SDK hostless `EffectMain`でClassic／Smart各63セルが
  同じWindows exported Smart oracleへraw exact、567 one-awayとSmart callback 13件、World／Color suite 12件、param checkout／checkin
  各33 failure ordinalがcommit前にfail-closeすることを確認しています。Universal minOS 11 buildは
  installed版は60セルのtoggle24 Universal版で、今回の3セルは未installです。native AE数値実行の証拠ではありません。
- OLMDistanceGradation：主要な各モード・補間・背景・反転・blurは個別に検証していますが、
  全コントロールの直積は未証明です。固定17×11のpublic admissionは、PF16 32セルと
  PF32のConstant／Linear／Sphere 24セル、計56セルがraw exactです。PF32 Power 8セルは、
  AEXがWindows UCRT `powf`をimportする一方、AEXCompatがhost `f32::powf`へ置換するため、
  native Windows capture取得まで両architectureでfail-closeします。productionの8セルから
  `powf` input 1,496件／unique 63件をbit exactで固定し、native UCRTだけをAEなしで評価する
  return packageはreadyですが、actual-AEX pre-call XMM inputとnative-derived final 8 outputは
  まだ同一evidence chainで証明されていません。PF32 Blur 5のfieldは
  OpenCV 4.5.5 IPP bilateralのdirect `expf`、L／T／R／B加算順、late spatial multiply、
  非縮約float積を再現し、非Power 6行がpublic raw exactです。旧portable bodyの37 word／最大2 ULP差は
  counterfactualとして保持し、期待word／座標補正は行いません。
  元AEXにはpublic command `0x18` → `FUN_181173d20` → PF32
  `FUN_181172a10` → iterateFloat／`FUN_181170c90` のSmart ownerが存在します。
  productionのPF32 Smart admissionは固定17×11の24 non-Power exactセルに限定し、
  未列挙tuple／geometry／layoutはfail-closeします。project/global fast-math設定や
  任意fast-math codegenへの一般化は行いません。
- OLMDirectionalBlur：Noise Type 3 LayerのPF16/PF32は、記録済みtupleを中心とする
  bounded対応です。Front／Back Fade 50／100×Sharp Tail 50／100は3深度でexactですが、
  Noise Type 1／2、Size Variationを含む高次covering 24行もraw exactです。
  Front＋Back同時の記録済み12行もraw exactです。Type 3、他geometry、未列挙tuple、
  Layer欠落／寸法不一致はfail-closeする場合があります。32×18の対応familyも
  3深度12／12 exactです。64×36もworker／public各12／12 exactで、rotated width 76、
  32 calls×2 rows、tail preseedを確認しています。対応geometryは16×16／32×18／64×36、
  記録済み4 tupleに限定し、Type 3／他geometryへ一般化しません。加えて64×36の
  Type 2／Noise Variation 25／Size Variation 0／Front 8単独tupleは、自然AEXCompat
  ownerとpublic EffectMainがPF8／PF16／PF32でraw exactです。PF16/PF32の新規admissionは
  この64×36／NV25 laneだけです。3深度すべてrowwise active-source SHA-256で
  固定cropとexactなzero／constant／impulse／checkerだけをadmitし、PF8もsource不一致時に
  旧generic rendererへfall throughしません。PF16/PF32の全predicate／scale／dimension／
  rowbytes／null 60件に、PF8のsource先頭／中央／末尾bit mutationと未列挙source4件を加えた
  64件を拒否します。任意sourceへの一般化はしません。現行hostless sourceではSmartの
  parameter/layer cleanupをsuccess-only ownership＋first-errorへ修正し、全cleanup成功後だけ
  private stagingからcommitします。returned error／throw 16件は入力とhost出力全体を不変に
  保ちます。このcandidateはbatch5でinstall済みですが、native AE実行は未確認です。
  dual-side固定32×18／64×36の15セルをWindows AEX exported Smartで再実行し、
  arm64は15／15 raw exactへ拡張しました。旧6セル差（PF8 5語／PF16 5語／PF32 20語、
  最大2 ULP）は、実AEX Iterate callbackをguest codeとして実行した上で、double-round `exp`
  counterfactualが全差分を再現し、imported float `expf` leafが6／6を閉じることを確認しています。
  Rosetta x86_64のlibSystem `expf`は旧差分を再現するため、同sliceでは従来9セルだけを許可し
  残り6を516で拒否します。Universal minOS 11 executable `3528d12c…122a7`は
  transactional install済みで、後続の現installed `9b5fc6b3…d2eff`でもarm64 15 exact／
  x86_64 9 exact＋6 fail-closeというarchitecture別境界をAE-free再実行しています。
  さらにNatural64のexact-source 15セル／sliceを現installed public entryで再生し、
  下記Type3 3セルと合わせてarm64 33 exact、x86_64 27 exact＋6 fail-closeです。
  旧`4e238ac0…4d77`は
  3つのfull-bundle rollback copyとして保持します。固定16×16 Type 3 Layerはその後、同一source／Layer・
  固定tuple／rowbytes／extentだけPF8／PF16／PF32の3セルをhostless exported SmartとMac publicでraw exact化しました。
  PF16の旧`byte*128` internal fixtureはSDK transportではないためsupersededです。未列挙条件はfail-closeし、
  Universal minOS 11 executable `9b5fc6b3…d2eff`としてtransactional install済みです。
  installed arm64／Rosettaの各sliceも3正例＋54 one-away reject（57／57）をAE-free public replayで
  source-built経路と一致確認しました。native Windows／AE numerical claimはありません。
  AEX oracleはpinned AEXCompat／Unicornでnative Windows／AE claimではなく、今回AEは起動せず
  次の変更とのbatched checkpointへ延期しています。
- OLMToonDilate：legacy PF_Cmd_RENDERは実AEX同様no-opで、描画はSmartRender経路です。
  実AEXの記録済み成功経路がoptional checkin_layer_pixelsを呼ばないため、
  Mac版もpixel/output checkout各1回、optional checkin 0回へ合わせました。別契約の
  parameter checkout/checkinは維持しています。source-included public経路とisolated
  Universal candidateはPF8／PF16／PF32で既存のpixel、padding、guard、入力不変性を
  保持し、null optional callbackも安全です。productionのcheckout失敗はcheckin 0、
  success＋null worldはBAD_CALLBACK_PARAMで閉じますが、実AEXの失敗control flowは
  未captureで同等性主張外です。source `ded9eaab…4464b`のUniversal minOS11 candidateは
  installed executable `5bbe6931…036e`とfull-inventory exactで、AE-free installed public
  closureでも固定12セルを両sliceで再現します。現行identityでのnative AE numerical exactは
  未証明です。任意radius／geometry／入力へも一般化しません。
- OLMRadialBlur：centered neutral InnerはPF8/PF16/PF32で複数geometryを実AEXと
  bit完全一致確認済みです。直接観測済みの最大geometryはPF8/PF16が640×360、PF32が
  64×36です。off-center、非unit ratio、angle、quality、repeat、offset、
  edge fade、noise、variationを含む全組合せは未証明です。Size Variation×Edge Fadeは
  記録済み32×18 fixtureの3深度36行でexactですが、任意geometryや未列挙値へは一般化
  しません。Rotation Size Variation×Offset Mode 2／3は同fixtureの3深度24ケースで
  全stage exactですが、未列挙値、geometry、Type 3はfail-closeします。
  Rotation Noise Type 1の旧1〜4 ULP sampled-source-scalar seamは、固定32×18の
  exact five admission flags／98セルでinverse-cell samplerへ接続して閉じました。
  familyごとに利用可能なsource span／scalar、polar、accum、max、final、coords、
  padded outputがraw exactで、Edge系はprepass alphaもexactです。旧reportの
  inactive-only表現はhistoricalであり、実際には消費可能な差分cellも含まれていました。
  未列挙tuple／geometry、Rotation Type 3、Strength 290 public admissionはfail-closeします。
  ratio 2／angle 30°＋Edge、Quality 3／Repeat off＋Noise Type 2、off-center＋Sizeの
  3 tupleはZoom／Rotation・3深度の18／18でexactです。これはRepeat-off有効tap正規化、
  Rotation noise gate、Quality 3 outer span 3／5を閉じるbounded証拠であり、
  任意transform／worker直積へは一般化しません。
  Inner Strength 4のSize×Edge×Noiseも記録済み24ケースでconsumed planes／output
  exactです。PF32 Rotationの4 tupleだけforward-angle、PF8／PF16はreverse-angleです。
  このうち固定32×18 Rotation Type 1のSV25 source scalarも上記inverse-cell closureで
  raw exactへ更新済みです。未列挙tuple／geometry／Type 3へは一般化しません。
  Rotation Dual Strength×Size×Noise×Offsetは固定32×18の3深度24ケースで、
  Size×Noise span、Outer／Inner寄与、選択側Mode 2／3 Offsetの内部面と出力がexactです。
  未列挙tuple／geometryはfail-closeし、この証拠でType 3をadmitしません。
  現installed Universal `9be59d18...76b5`のarm64／Rosetta両sliceでは、上記の
  exact-source Type 1 public union 106セルをClassic／Smartの両EffectMain entryで
  source closureと再照合済みです。5 family合計57件のsource mutationも各sliceで
  output非commitのままfail-closeし、Classic／Smartのpadded output全体が一致します。
  これはAE-free installed-Mach-O証拠であり、任意source／tuple／geometryやnative AEへは
  一般化しません。現source `b74b3d2c...b0d1`ではClassic／Type3 SmartのWorldSuite
  acquire、success-null、function-null、format取得、release error／例外も明示的に
  fail-closeし、primary errorを保持します。
  Type 3 LayerはPF32 Zoomの固定9×7／rowbytes 160、center (4,3)、Outer 4、
  Inner／Size 0、NV25、Repeat on、Ratio 1、Angle 0、Quality 5、Brightness 1、
  Seed 1、Offset 0、Thickness 3、同一origin／sizeのLayerだけをadmitします。
  direct internal actual ownerとpublic Mac classic productionはsource span、pre／post polar、
  padded output、および5 source基底×normal／inverse Layerの10行でraw exactです。
  SmartRenderはprivate worldへ描画し、成功した30 paramとInput／Noise Layerのcleanupが
  全て成功した後だけactive rowをhostへcommitします。15件のSmartRender failureと
  2件のSmartPreRender cleanup controlではinput／output全体が不変です。同じ固定tupleの
  5 source基底×normal／inverse Layer 10行はpublic SmartでもClassic／actual ownerと
  active bytes・paddingまでraw exactです。これは同じbounded tupleのentry接続であり、
  新tupleの昇格ではありません。
  同じ9×7 tupleのPF8（rowbytes 44、center (4.5,3.5)）、PF16（rowbytes 80、
  center (4,3)）、PF32（rowbytes 160）では、5 source基底×3 Layer familyの各15組を
  source span、pre／post polar、padded outputまでdirect typed ownerとraw exactに接続しました。
  同じ現installed Universalのarm64／Rosetta両sliceでも、全45組の
  Classic EffectMainとSmartPreRender→SmartRenderをsource-built ownerと再照合し、各組の
  bounded reject controlもoutput非commitで通過しています。これはAE-free public-entry証拠であり、
  native AEの証拠ではありません。未列挙PF8／PF16／PF32 source／Layer、
  null／format／origin／size不一致、
  他のType 3 geometry／rowbytes／tupleはfail-closeし、native AE pixel exactは主張しません。
  Windows独自のcustom preview描画と操作も未証明です。
- OLMSmoother2：key、invert、Gamma、range、paletteの主要分岐はbounded exactです。
  Gamma／key／smoothing交差は54／54 exactです。旧PF8 Gamma All 2.4 seamは
  current-AEX LUT契約と非縮約scalar積和で閉じましたが、全パラメーター直積と
  AE host実行は未証明です。palette count／reorder／duplicate交差18／18もexactですが、
  未列挙palette直積へは一般化しません。追加の固定5×5 endpoint fixtureでは、
  Gamma Value 1.8、key RGB (202,187,230)、Gamma Colors `[red,key]`、smoothing上限を
  v1／v2×invert有無×3深度で交差し、exported Smart ownerとpublic EffectMainが
  12／12 raw exactです。これは24px保持＋1 exact-key endpoint置換の限定証拠で、
  他の中間Gamma値、key／palette、input、geometryへは一般化しません。
  public numerical entryはSmartに限定し、3×2のPF32 installed-owner cell、5×5の
  exported-owner Gamma 1.8／2.4 cell、17×11の6-cell public matrixという
  明示的unionだけをadmitします。classicは全深度でfail-closeします。direct-coreだけの5×5 smoothing／semtransparentと
  9×7 matrixは回帰証拠として保持しますがpublic admissionへは使いません。
  input／output format、寸法、rowbytes、active span、extent、非aliasを検査し、
  3×2 PF16 synthetic classic adapter、未列挙tuple／geometry／layoutはBAD_CALLBACK_PARAMでfail-closeします。
  Smart checkoutが途中失敗した場合も、成功済みparameter／Layerだけをcheckinします。
  ColorSuiteが成功を返してもbyte colorと異なるfloat値を返す場合は拒否し、World／Color suiteの
  acquire-success/null、function-null、callback／release errorはreal-SDK source-included probeで
  fail-closeを確認しています。v1／v2 guard版はisolated Universal build／ad-hoc署名確認後、
  batch4でinstall済みです。post-batch4 AEはreadiness段階で停止したため、現行binaryの
  AE smoke／numerical実行は未証明です。
- OLMKiraKira：Mode 1〜4の主要経路を実装しています。Mode 4の方向レイは、9×7以上の
  回転後geometryとLength 1〜1000を、実AEXの17ケース・51中間stageで一般化しています。
  5代表compose交差では非default色、半透明／HDR、Merge 1／2、ramp off／1／2を含めて
  raw exactですが、小型shape、ray／色／ramp／Merge Modeの全直積とDrawbot custom UIは
  未証明です。自然生成5×3 full-frameは同一実行のseed／ray／aggregateからtyped
  outputまでexactですが、hostlessの1 source caseであり、Windows AE pixelや
  geometry-generalへは昇格しません。追加4 source／12 typed outputはmax ULP 0です。
  Highlight gradientも記録済み5×3／Radius 3（kernel 7）に限り、Mode 4 public
  PF8／PF16／PF32がraw exactです。Mode 2の同tupleは3深度exactの回帰controlです。
  Mode 1の同tupleも、PF8 source decodeをWindows ownerと同じ丸め済みfloat32
  `1/255`乗算へ合わせ、PF8／PF16／PF32がraw exactです。この主張は記録済み
  5×3入力に限定し、任意のMode 1入力や全パラメーター直積へ一般化しません。
  Mode 1／2／3 public ownerのRotation 1°は3深度9／9 raw exactです。AEXCompatの
  raw fixed解釈修正を含む限定証拠です。Mode 2 Rotation 22°も自然ownerのinner
  aggregate selectorを回収し、PF8／PF16／PF32すべてraw exactに閉じました。
  Mode 4 Horizontal／Diagonal2／Highlight soloと記録済みDiagonal2 multirayも
  3深度raw exactです。Diagonal2はWindows ownerの有向`135°+Rotation`へ修正し、
  seedからwriterまで一致しました。任意rotationやgeometryへは一般化しません。
  Highlightのexact主張も上記Radius 3／kernel 7限定で、全radius／全gradient直積へは
  一般化せず、期待word補正も行いません。
- OLMSmoother v1：元AEXのnative depthはPF8/PF16です。32bpcプロジェクトではAEが
  classic integer pluginの前後を変換するため、native PF32互換とは表現しません。
  public admissionは、960×540 PF8 canonical、7×5 PF8/PF16 family、64×36 PF16
  practical family、および5×3 PF16 Color Key sessionに限定します。output world所有の
  format判定を使い、PF32 classic、format／dimension／rowbytes／alias不一致、未列挙
  tuple／geometryをfail-closeします。これらはclassic entryだけのadmissionで、
  advertise／owner witnessのないSmart numerical entryは全拒否します。guard版Universal buildはbatch4でinstall済みですが、
  current native-AE smokeは未実施です。各admissionはtuple固有のactive-source SHA-256を要求し、
  paddingをsource identityへ混ぜません。v1はprivate stagingで成功時だけactive rowをcommitし、
  v2はodd-stride PF16/PF32をaligned tight stagingへ移して、parameter／Layer／suite cleanupが
  すべて成功した後だけcommitします。任意入力へは一般化しません。

より詳細な証拠境界は
[リリース完成表](refs/conformance/olm_release_completion_matrix_20260806.md)を参照してください。
