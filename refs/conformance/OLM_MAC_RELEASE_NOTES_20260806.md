# OLM for Mac Public Beta リリースノート — 2026-08-13更新

- 2026-08-14: このbounded port cycleはclosedです。現行accepted identity manifestは
  `94c6a1ef…650`で、全10本のUniversal／署名／単一bundle／identity exactと限定public
  hostless routeを確認済みです。最終fresh AEは1回だけ起動しましたが、`DoScriptFile`の
  returnが現れず0 plugin rowのままfail-closeし、再試行していません。releaseは
  `release_gate_pending_or_invalid`／`releasable=false`です。正本は
  `olm_bounded_port_cycle_final_status_20260814`です。Radial PF32 32x18 Strength 290は、同一sourceで
  AEX internal ownerとMac typed ownerがraw exact（`940c1e7e…`）ですが、AEXCompatの
  host代替`atan2f`／`log2f`を通したexported Smartは`f8be3360…`となり84ワード差です。
  native Windows UCRT結果を未取得のため、productionは従来どおりiteration前
  fail-closeを維持します。証拠は
  `olmradialblur_strength290_exported_math_boundary_20260814`です。

- 2026-08-14: OLMSmoother2 current source `c710902f…` now admits the retained
  full-HD PF8 twelve-case grid only under its exact active-source SHA and twelve
  exact parameter tuples. The twelve direct outputs reach the retained
  current-AEX PNGs through an independently checked nearest-code
  premultiplication with zero differences over 99,532,800 bytes. Together with
  the prior 25 cells and case-07 PF16/PF32, the source-built candidate has 39
  bounded Smart cells. Universal minOS11 candidate `c8ea1f0e…` passes the PF8
  12-positive/34-negative public closure on both slices. The exact candidate
  is now installed as `c8ea1f0e…`; accepted identity `7212ca5c…` changes only
  the OLMSmoother2 row and top-level timestamps, with three exact predecessor
  copies retained. Two all-ten preflights are byte-identical and AE-free. No
  native output-world capture or arbitrary-input claim is added. The final
  hostless installed replay passes all ten plug-ins on both slices (96.88s),
  including all 39 Smoother2 cells and its 94-row expansion per slice. The later
  single aggregate AE attempt returned no payload and adds no host or numerical evidence.

> 本プロジェクトはOLM DigitalのオリジナルOLMプラグインを基にした非公式の
> 互換移植であり、OLM Digitalによる提携・承認を示すものではありません。
> オリジナルのプラグイン、製品名、商標および原著作物に関する権利は、
> それぞれの権利者に帰属します。リポジトリのLICENSEは収録コードの利用条件であり、
> 本家資産に別途の権利を付与するものではありません。

## 現行release integrationの正本

全10プラグインのaccepted identity manifestの`accepted_at`／`installed_after`
（2026-08-12 09:59 UTC）は、全10本を一括受理したall-ten baselineの時刻であり、後続の
Radial単体install受理時刻ではありません。Radial Type 1のfreshなinstall authorityは、
incremental reportの検証時刻（`generated_at` 2026-08-12 11:05:06 UTC）と
installed executable SHA-256 `03e837e8...d548`であり、post-Radial smoke relationが
そのreport digestと同じexecutableをbindします。Radial-row-only identity transitionは
top-levelの2時刻と非Radial 9行だけを維持し、Radial行の2 hash fieldを更新しました。
formal gate inputsもpost-Radial smokeへretarget済みです。現行全10 installed executableは
build productとbyte exact、arm64+x86_64、
strict codesign、各1 bundleです。release gateはこのidentity manifestのファイルdigest／
`accepted_at`と、受理後に起動した単一fresh AE
processによる全10本のload／apply／module mappingとhost-frame summaryを直接照合します。
その後のKira-only transitionではminimum macOS 11.0を固定し、Kira行の2 hash fieldと
manifest受理時刻だけを更新しました。その時点のformal gateはpost-Kira smokeへretargetされ、
post-Radial／post-Distance smokeは各時点のimmutable historical evidenceとして保持します。
さらにColorKeep-only transitionでsource `3ff3a4d4...ebdfd3`からbuildした
`fcd501da...dd77`を受理し、Info.plistと両sliceのminimum macOS 11.0を固定しました。
post-ColorKeep count9 fresh smokeはその時点のidentityに対するimmutable historical evidenceです。
その後、ToonDilateに加えてbatch4（OLMBlur／OLMColorKey／OLMSmoother／OLMSmoother2）を更新し、
accepted identityは`426dce71…eccc`になりました。batch4のfresh AEは1回だけ起動しましたが、
receipt／payload前のDoScript readinessでfail-closeし、plugin rowを一件も実行していません。
失敗は`handoffs/olm_all10_post_batch4_fresh_ae_smoke_failure_20260813/`へ保存し、retryは
code-levelで禁止しています。
その後のhostless batch5で、OLMBlur `ecdf3d93...284d`、OLMDirectionalBlur
`371c3b62...d0f0`、OLMRadialBlur `1bd0d6ee...baa6`を一括installし、accepted
identityは`40cd982c...4363`になりました。3本とも候補とinstalled full bundle inventoryが
exactで、旧bundleは各3コピーを保持します。全10 preflightは2回byte-identicalで、
AE processは0です。batched-checkpoint方針により、このtransition後の
AE／aerender／formal gateはまだ実行していません。
さらにRadialだけを現行source `0aac085a...cb26`から再buildし、Universal minOS11
candidate `da72af55...b859`へatomic swapしました。batch5で一時的に入った
pre-promotion `1bd0d6ee...baa6`は3つのfull-inventory exact rollback copyとして保持し、
accepted identityは`cc9cb7ed...66be`です。他9行はexactで、全10 preflightは2回
byte-identical、AE processは0です。このRadial修復後もAE／formal gateは延期しています。
さらにType1 exact-source batch 4をsource `44f1e7f9...c5acb`／Universal
`2934d136...3083`としてRadialだけatomic更新しました。98-cell fixed-32x18 projection
全行と9x7 controls、57 route-specific mutation rejects／sliceをhostlessで閉じ、旧
`da72af55...b859`は3つのfull-inventory exact rollback copyとして保持しています。
accepted identityの変更はRadial 1行とtop-level timestampsだけで、全10 preflightは
2回byte-identical、AE processは0です。AE／formal gateは引き続き延期しています。
その後、Type3 source／Layer guardをcurrent source
`efb54d65...480b`へ拡張しました。固定9×7／NV25で各depth 15の計45 exact pairだけを
admitし、actual typed owner、source-built direct、Classic、Smartの
internal planesとpadded outputがraw exactです。PF8 constant／impulseは補正なしRGB writerで
exact化し、PF8／PF16 full-alpha natural Layerも各5 sourceでexactです。Universal minOS11版
`1b29b5ea...643c`はfull-inventory exactでinstall済みです。旧35行版`ce5b57e1...0e7a`は
3つのexact rollback copyに保持し、45行版のAE／formal gateは実行していません。
最終host-frame契約はBlur／Directionalの2本だけをenabled、他8本をdisabledとしました。
ただし唯一のcurrent-identity実行はpayload return前にfail-closeし、plugin rowとPNGは0件です。
したがってplugin computationやpublic numerical exact tupleの証拠は追加されていません。
2026-08-10の旧green gate内容と、それ以前の個別host smokeは、名前が`current`であっても
旧binary固有の履歴です。現在checked-inの`olm_release_gate_status_20260806.json`は
`release_gate_pending_or_invalid`です。install identity 10／10、parameter／UI 10／10、
Windows最小7観測はproven／acceptedですが、current-identity Mac AEは0 proven／10 invalidで、
audit modeのため固定fixtureもpendingです。current host evidenceを得てfull gateが完走するまで
release可能とは扱いません。

最新のhostless OLMBlur source `22eb712a...fdd7`は、同一sourceのPF8 12/12、PF16 8/8、
PF32 20/20セルをpublic Smartへ接続しました。closureはPF8が24正例／744 fail-close、PF16が
16正例／494 fail-close、PF32が40正例／60 fail-closeです。各深度のfractional Legacy
SmoothnessはWindows ownerのsigned integer-part materializationをexact admission内だけ再現します。
Universal候補`ecdf3d93...284d`はbatch5でfull-inventory exactにinstall済みです。
最終batched checkpointは1回だけ実行してreturnなしでfail-closeしました。再試行せず、
formal gateは実行していません。

Windows AEの最小7観測契約は7／7 accepted、0 invalid、0 pendingです。これは
process／module／parameter／EXR観測契約の受理であり、7行すべてのcross-host raw exactを
意味しません。current identity、fresh all-ten AE smoke、固定fixture、parameter/UI gateの
それぞれを別の証明境界として維持します。

## 2026-08-11 追加検証

2026-08-10の統合ゲート通過後も、完了判定に寄与する複合分岐の
actual-AEX比較を追加しました。これは全パラメーター直積への一般化ではありません。

- OLMRadialBlur Type 3 Layer：固定9×7／NV25のexact source／Layerペアだけをproductionへ
  接続しました。現行closureはPF8／PF16／PF32それぞれ5 source×3 exact Layer＝15行、
  合計45行です。45行すべてでdirect internal actual owner、
  source-built direct、Classic EffectMain、SmartPreRender→SmartRenderのsource span、
  pre／post polar、padded outputがraw exactです。PF8 constant／impulseはType3 ownerの
  補正なしRGB writerでexact化しました。この追加はhostless numerical evidenceで、native AEの
  数値証拠ではありません。current sourceは`efb54d65...480b`、Universal minOS11
  `1b29b5ea...643c`はinstall済みです。Windows exported renderはType 3時に未初期化の
  worldコピー先を参照するため、exported-entry数値oracleではなくbounded typed ownerを正本にします。

- OLMRadialBlur Smart cleanup：public SmartRenderはhost outputへ直接描かず、private
  worldへ描画して、成功した30 parameter checkoutとInput／Noise Layer checkoutの
  cleanupが全て成功した後だけactive rowをcommitします。SmartRenderの15 returned-
  error／throw controlとSmartPreRenderの2 cleanup controlは失敗時のinput／output全体
  不変を確認しました。source `8fde53eb...8c10`の旧Universal候補`1bd0d6ee...baa6`は
  batch5で一時installされた後、current source `0aac085a...cb26`の`da72af55...b859`に
  supersedeされました。AEとformal gateは実行していません。
  固定Type 3 tupleの10 source／Layer行はpublic Smartでもactual owner／Classicと
  active bytes・paddingがraw exactです。新tupleには一般化しません。

- OLMRadialBlur：32×18の記録済みcomponent fixtureで、PF8／PF16／PF32の
  Size Variation×Noise Variation（48行）、Brightness×Size×Noise（96行）、
  Edge Fade×Noise（72行）をexact確認しました。さらにRotationの
  Offset×Noise（48行）、ZoomのEdge×Offset×Noise（48行）、Rotationの
  Edge×Offset×Noise（96行）を閉じました。Noise Variation 0では
  Zoomのself seedを保持するactual-AEXの振る舞いも回帰に反映しています。
- OLMSmoother2：v1／v2、PF8／PF16／PF32、複数geometryと入力patternを含む
  core 96行とfeature 18行の計114行をactual AEXとexact確認しました。
  この過程で、特定の幅での水平／対角scan境界を修正しています。
  Gamma 1.0／2.4、Gamma All／Colors、key極性、3 smoothing tupleを交差した
  9×7 fixtureは54／54 raw exactです。旧PF8 Gamma All 2.4 mixed tupleの5-byte seamは、
  current-AEXの10,000-entry LUTをPF8 decode／outputにも使い、Windowsのscalar
  MULSS→ADDSSをarm64 FMADDへ縮約しないことで閉じました。期待byte補正ではありません。
  Gamma Colors paletteのcount／reorder／duplicateをkey極性と3深度で交差した
  18／18ケースもraw exactです。未列挙palette／key／smoothing直積へは一般化しません。
  さらに固定5×5 endpoint fixture（既存24px＋exact key 1px）で、Gamma Value 1.8、
  key RGB (202,187,230)、Gamma Colors `[red,key]`、smoothing上限を
  v1／v2×invert有無×3深度に交差し、exported Smart ownerとpublic EffectMainが
  12／12 raw exactです。入力不変、row padding、Smart lifecycleも確認しましたが、
  他の中間Gamma値、input、key／palette、geometryには一般化しません。
- OLMSmoother v1／v2 public guard：inputではなくoutput worldも含む実formatを
  PF World Suiteから取得し、format／dimension／rowbytes／active span／aliasを検査します。
  admissionをentry別に分け、v1はclassic証拠セルだけを許可してSmart numerical entryを拒否、
  v2はSmart証拠セルだけを許可してclassicを全深度で拒否します。さらに各tupleを
  rowwise active-source SHA-256へ個別対応させ、任意source unionを許可しません。
  v1はprivate output staging、v2はodd-stride PF16/PF32も安全なaligned tight input/output
  stagingを使い、全cleanup成功後にのみactive rowをhost outputへcommitします。
  Smart checkout途中失敗では成功済みresourceだけをcheckinし、World／Color suiteの
  acquire／callback／release errorも伝播し、real-SDK source-included probeで
  WorldSuite 12条件＋v2 ColorSuite 6条件を検証しました。focused guard 69／69、source contract、
  既存v1/v2 public exact回帰、および公式fixed-fixture 2 laneがpassしました。
  direct-coreだけの5×5 smoothing／semtransparentおよび9×7 matrixはpublic admissionへ
  昇格せず、回帰証拠としてのみ保持します。
  現workspace候補は`handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/`
  （v1 `f416579e…`／v2 `55d138e2…`、manifest `5bc74321…`）に固定し、macOS 11
  Universal x86_64/arm64、strict-valid ad-hoc署名です。このmanifestはbuild時点の
  未install境界を保持したまま、両bundleはその後batch4でfull inventory exactにinstall済みです。
  post-batch4 AE試行はreceipt／payload前に停止したため、現行identityのruntime証拠には扱いません。
  2026-08-14のsource-only更新では、OLMSmoother2 case-07のexact 1920×1080 PF16/PF32
  source／tupleを26・27番目のSmart cellとして追加しました。PF16はno-effect EXR全wordから
  一意復元したinput `c8d5ded0…`を使い、direct output `d306573a…`の`code/32768`表現が
  effect-on EXR全8,294,400 wordとexactです。PF32 direct straight output `31bbdb17…`と、
  Windows final EXR `69b56309…`へのfixture限定float32 premultiply関係を分離して証明し、
  public EffectMainは各depthで1 positive＋23 fail-close controlsを通過しています。新Universal候補
  `23b09445…`はminOS11／strict-valid ad-hocですが未installで、AEは起動していません。
- OLMKiraKira：Mode 4の方向レイを、回転後geometry 9×7以上、Length 1〜1000へ
  一般化しました。17ケース、51中間stageの比較はすべてmax ULP 0です。
  さらに5代表ケース×PF8／PF16／PF32で、非default色、半透明／HDR、Merge 1／2、
  ramp off／1／2を含むcompose交差を確認し、aggregate 320 bytesとtyped output
  560 bytesがraw exact／max ULP 0でした。Length 1の非identity経路と、
  actualの合成順Vertical→Horizontal→Diagonal→Diagonal2→Highlightも反映しています。
  natural Mode 4の残り4 source caseもsame-runで閉じ、新規12 typed outputは
  raw exact／max ULP 0です。Highlight gradientも記録済み5×3／Radius 3
  （kernel 7）のMode 4 public 3深度とMode 2 controlはraw exactです。Mode 1の
  同じalpha byte=`15*i`（typed正規化値は`15*i/255 = i/17`）tupleも、
  PF8 source decodeをAEX同様のfloat32 reciprocal乗算へ
  合わせて3深度raw exactです。さらにClassicと同一の固定5×3・14 tupleをSmart
  public routeへ接続し、PF8／PF16／PF32の42／42セルがhostless raw exactです。
  source family、padding、Windows同様の条件付きparameter checkout（base 25に有効な
  ramp payloadだけを加えた25／26／27回）、world lifecycle、input不変性を固定し、
  callback／suite失敗と未列挙tuple／source／geometry／layoutは出力変更前に拒否します。
  Universal版は現行installへ反映し、fresh AEでload／add／single-path mappingと
  effect-disabled host-frame renderを確認しました。5×3数値tupleのnative AE oracle比較は
  実施しておらず、numerical exactへは昇格しません。全radius／任意gradientへの一般化はfail-closeのままです。
- OLMDirectionalBlur：Front／Back Fade 50／100とSharp Tail 50／100の組合せを、
  PF8／PF16／PF32の計24行でraw exact確認しました。
  さらにfront／back各4 covering tupleでFade、Sharp、Noise Variation、
  Noise Type 1／2、Size Variationを交差させた高次24行もraw exactで、
  既存回帰を通過しています。さらにFront＋Back同時の4 tuple×3深度、計12行も
  raw exactです。Type 3、他geometry、未列挙tupleはfail-closeします。
  同じdual-side familyを32×18 geometryでも3深度12／12、rowdriver 32 callsで
  raw exact確認しました。他geometryや未列挙tupleは引き続きfail-closeです。
  64×36 geometryでもworker 12／12、public EffectMain 12／12がexactです。
  rotated width 76、32 calls×2 rows、tail preseedを含みます。対応範囲は
  記録済みdual-side 4 tupleに加え、64×36のType 2／NV25／Size0／Front8単独tupleを
  PF8／PF16／PF32でraw exact確認しています。新規PF16/PF32 admissionはこのtuple限定で、
  固定cropとzero／constant／impulse／checkerのsource基底も全深度exactです。PF8 controlも
  同じactive-source SHA unionへ狭め、source不一致を旧generic rendererへ流しません。
  PF16/PF32の60件とPF8 source mutation／unlisted 4件、計64件を拒否し、他の既存routeは不変です。
  後続のexported Smart再実行でdual-side 15セルのうち5セルがraw exact、10セルがmismatchと
  確定しました。current sourceはexact 5のみを限定昇格し、残る10とType 3 Layer 3セルを
  fail-closeします。Natural64のAEXCompat exported-entry laneも維持します。
- OLMBlur：従来の固定24×24 exact-source 6セルに、Windows actual AEX exported Smart
  ownerで同一sourceを実行したPF16 7セルを追加しました。NonLegacyは7×5/Amount4/Repeat1、
  12×12/Amount3/Repeat1とRepeat2、18×18/Amount11/Repeat1です。Legacyは12×12/
  Amount3/Repeat2/Bias1、18×18/Amount11/Repeat3/Bias2、18×12 mixed-alpha/Amount3/
  Repeat2/Bias2です（rowbytes69/109/157、全てSmoothness100）。
  Windows public outputとMac public EffectMainはactive bytesと13-byte row paddingまでraw
  exactです。最新Mac real-SDK closureはPF16 16正例／494 fail-close、PF8 24正例／744
  fail-close、PF32 40正例／60 fail-closeです。PF8 12/12、PF16 8/8、PF32 20/20が
  Windows exported ownerとraw exactです。3つのfractional Smoothnessセルはownerの
  signed integer-part materializationをexact admission内だけ再現します。
  source`22eb712a...fdd7`のUniversal候補`ecdf3d93...284d`は両slice／Info.plist minOS 11、entry point 2本、strict/deep ad-hoc
  署名を確認し、batch5でfull-inventory exactにinstallしました。旧batch4
  `5893faea...c48b`は3コピー保持され、AEは起動していません。未列挙tuple／source／layoutへの
  一般化はなく、既存Classic境界も不変です。
- OLMColorKey：半透明入力のEdge Blur Amount 2、Direction 1／2／3、
  Distance Type 1／2／3を、PF8／PF16／PF32の計27行でbyte exact確認しました。
  さらにDirection 0／4、Amount 1／4、Distance Type 2のendpoint 12行も
  temporary planeからrow paddingを含む出力までexactです。
  Direction 0／4、Distance Type 1／3のcovering 12行も追加でexactとなり、
  retained controlを含むmatrixは51／51です。PF32 Amount 4は記録済みshellに限定し、
  未列挙tuple／geometryへは一般化しません。Lab76 2-key順序反転fixtureは、nativeの
  destructive comparator mutationとfloat32 Euclidean threshold順を再現して
  PF8／PF16／PF32の6／6 public owner出力がraw exactです。
- OLMRadialBlur：Size Variation 25／100とEdge Fade 50／100の記録済み複合経路を、
  PF8／PF16／PF32の計36行でexact確認しました。
- OLMRadialBlur Rotation Type 1 inverse-cell closure：Dual Strength×Noiseの48ケースでは、ZoomとRotation Noise Type 2は
  全内部stage exactです。Rotation Type 1の旧sampled-source-scalar ULP seamは、
  fixed 32×18 inverse-cell closureの該当18セルでraw exactへ更新されました。
  未列挙tupleを拒否するfail-close controlは維持します。
- OLMRadialBlur：Rotationの固定32×18 component fixtureで、PF8／PF16／PF32、
  Outer／Inner、Size Variation 25／100、Offset Mode 2／3（UI 4）の計24ケースを
  actual AEXとexact確認しました。polar、source scalar、accum、max、final、coords、
  outputの各stageが一致します。未列挙値、geometry、Type 3はfail-closeします。
- OLMRadialBlur：Zoom／Rotation、PF8／PF16／PF32、4 covering tupleの
  Size×Edge×Noise計24ケースで、consumed planesとtyped outputがexactです。
  Edge prepassのcomponent factorと、scatterが使うSize×Noise spanは別経路として
  一致を確認しました。Rotation Size Variation 25の旧diagnostic source-scalar差も
  inverse-cell closureの該当12セルでraw exactへ更新済みです。
  Inner、未列挙tuple／geometry、Type 3はfail-closeします。
- OLMRadialBlur：Inner Strength 4のSize×Edge×NoiseもZoom／Rotation、
  PF8／PF16／PF32、4 tupleの24ケースでconsumed planes／output exactです。
  PF32 Rotationの4 tupleだけはforward-angle、PF8／PF16はreverse-angleを使います。
  Size Variation 25の旧diagnostic source-scalar差もinverse-cell closureでraw exactです。
  未列挙tuple／geometry／Type 3はfail-closeします。
- OLMRadialBlur：非neutral transform×workerの3 tupleをZoom／Rotation、
  PF8／PF16／PF32で交差した18／18ケースがexactです。Aはratio 2／angle 30°＋
  Edge 50、BはQuality 3／Repeat off＋Noise 100 Type 2、Cはoff-center (8,6)＋
  Size 50です。Repeat offでは有効tapだけで正規化し、Rotation noise gateを通し、
  Quality 3のouter spanは3／5を使うactual-AEX機序を反映しています。
  未列挙tuple／geometry／Type 3へは一般化せずfail-closeします。
- OLMDistanceGradation：Constant／Linear／Sphere／Power、Background on／offの
  typed blur matrixで、PF16 32行とPF32 non-Power 24行、計56 admittedをraw byte exact確認しました。
  PF32 Blur 5は固定17×11の厳格predicate内で、OpenCV 4.5.5 IPPのdirect `expf`、
  L／T／R／B逐次加算、late spatial multiply、明示的な非縮約float積を再現し、
  Constant／Linear／Sphere×Background off／onの6／6がpublic raw exactです。
  PF32 Power 8セルはnative Windows UCRT `powf` captureがなくfail-closeです。production由来の
  1,496 call／63 unique input pairとAE不要のnative UCRT requestは固定済みですが、actual-AEX
  pre-call XMM inputとnative-derived final 8 outputが未証明なので、この時点ではpromotionしません。
  DirectionalBlurの158 `expf`引数と合わせた221-row one-shot Windows batchも固定済みで、
  同一`System32\\ucrtbase.dll` identityを必須化しています。これはAEを起動しない収集準備であり、
  native returnやpublic output closureを代替しません。
  旧portable bodyの37 word／最大2 ULP差とbarrierなしbuildはcounterfactualとして保持し、
  期待word／座標補正は採用していません。Linear Mode 5の自然観測では、距離pre-plane
  187／187 wordsがexactで、public post-IPP field `7aaab791...`もproductionと一致します。public
  command `0x18` のPF32 Smart ownerは`FUN_181173d20` → `FUN_181172a10`
  → iterateFloat／`FUN_181170c90` と実在し、残差の初出はfinal composeではなく
  x86 OpenCV 4.5.5 IPP bilateral producer fieldでした。productionは固定17×11の
  PF32 24 non-Power exactセルのみadmitし、Power／未列挙tuple／geometry／layoutをfail-closeします。
  project/global fast-math設定や任意fast-math codegenへは一般化しません。

AEXCompat側の旧`37bdeae9`はhistorical infrastructure checkpointです。現行closure群が
固定するworkerはcommit `28d535469f84f67236ef3425afe4291ea2fb0991`、SHA-256
`46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61`です。
基盤更新自体はOLMのExact証拠に数えず、各closureのraw outputで判定します。

上記の数値は記録済みfixtureの行数です。任意のgeometryや未列挙の
Size／Noise／Edge／Offset／Brightness組合せへの完全互換は主張しません。
OLMRadialBlur Noise Type 3のLayer入力と、未記録の複合tupleは引き続き
証拠境界です。OLMKiraKiraの極小geometry、OLMDirectionalBlurとOLMColorKeyの
未列挙値・未列挙複合tupleも同様であり、上記結果を全設定へ一般化しません。
OLMKiraKira Mode 4の自然生成5×3 full-frameは、同一actual-AEX full-caller実行の
vtable seed 15 words、Horizontal slot 1／Length 5／Rotation 0°、aggregate入口ray
15 wordsからPF8／PF16／PF32 typed outputまでraw exactです。production変更は不要でした。
これはhostlessの1 source caseで、Windows AE pixelや任意sourceへは一般化しません。

## リリース候補の状態

Mac統合候補は、インストール済みUniversal bundleのarchitecture／署名／identity検査を
通過しています。固定fixtureとfresh all-ten Mac AE load／apply／renderは、現行identityへ
digest-boundした統合gateで再判定します。

旧identityで保存された最小host smokeの契約はAfter Effects 26.3x87、macOS 15.7.2 arm64、
Software renderer（raw 1816）で実行し、全10プラグインがloaded／applied／
render_succeededでした。これは履歴であり、現行identityのgateには数えません。各プラグインについて64×64 PNGを1枚保存し、以前の
9/10 smokeで未達だったOLMDirectionalBlurも今回は成功しています。これはhostの
ロード・適用・レンダー成立を示すsmokeであり、Windows pixel exact、主要パラメーター
一致、または保存PNGのconformanceを一般化する証拠ではありません。

同一契約によるWindows AE 7行は取得・受領検証済みです。ColorKeep 3深度、
OLMKiraKira Mode 4 PF32内部経路、OLMSmoother v1 PF16内部経路のbounded比較も
完了しています。host入出力変換を含むraw EXRの包括一致へは昇格しません。

## 2026-08-12 public entry／installed boundary

- ColorKeep：固定11×7／padding 12／固定palette、count 5／100 × PF8／PF16／PF32の
  6セルは、pinned AEXCompat上のactual exported Smart owner、installed public
  EffectMain、isolated Universal candidateでactive raw exactです。Mac public harnessは
  入力全体・world header・両padding不変、101 checkout/checkinを確認しています。
  productionはこの境界だけをadmitし、Classic PF32と未列挙geometry／rowbytes／palette／
  countをfail-closeします。Smart 38＋classic 24のone-away reject（world flags／
  originとWorld／Color／Iterate suite acquire failureを含む）を確認済みで、
  同じproduction sourceをDebugで再buildしたnamed productは現行all-ten identityへ
  install済みです。isolated candidateとのreproducible binary identityは主張せず、
  fresh AE smokeも別gateです。
- ColorKeep count9：従来laneとは別に、exact source／9色palette、固定4×3／padding 8、
  rowbytes 24／40／72だけをadmitします。source SHA-256は
  `d1c443042998e466b021d6fd2351537a2be63fe95d3e79a2089d82f78217bac3`です。
  同sourceでは従来11×7 count5/100 laneも深度/count別exact active-source SHAへ固定し、
  任意sourceを通しません。
  Windows exported Smart PF8／PF16／PF32とMac public Classic PF8／PF16・Smart
  PF8／PF16／PF32はraw exactです。Smartは未使用91色のdefault opaque-black tailも固定し、
  Classicはtailを読みません。136件のcanonical rejectは131件のpre-iterate拒否と5件の
  制御されたiterate failureで、いずれもpublic destinationを保持します。Classic PF32と
  未列挙source／palette／count／geometry／stride／layoutはfail-closeします。installed
  executableは`dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d`、
  minimum macOS 11.0です。fresh AEはeffect-disabledのload／add／single-path mappingだけで、
  count9 numerical renderを実行・証明していません。証拠は
  `colorkeep_nine_color_public_closure_20260813.{json,md}`、
  `colorkeep_source_bound_complete_union_candidate_20260813.{json,md}`、
  `colorkeep_source_bound_complete_union_install_20260813.{json,md}`、
  `refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813.json`です。
- OLMSmoother2：public EffectMain SmartPreRender→SmartRenderの6セルが3深度で
  actual-AEX coreとexactです。同条件classic Renderは3深度とも拒否してoutputを保持します。
  別の固定5×5 Gamma 1.8／exact-key
  endpoint交差もv1／v2×invert有無×3深度の12／12でexported ownerとraw exactです。
- OLMToonDilate：従来installed EffectMain Smart chainの4 semantic family×3深度は
  12／12 raw exactでした。actual AEXの記録済み成功経路はoptional
  checkin_layer_pixelsを呼ばないため、production成功経路も0回へ揃えました。
  productionのcheckout失敗もcheckin 0、success＋null worldはfail-closeしますが、
  実AEX失敗control flowとの同等性は未主張です。別のparameter checkinは維持し、
  null optional callback、PF8／PF16／PF32 public回帰、isolated Universal candidate
  12／12を確認済みです。同じproduction sourceをDebugで再buildしたnamed productは
  現行all-ten identityへinstall済みです。isolated candidateとのreproducible binary
  identityは主張せず、fresh AE smokeも別gateです。
- OLMDirectionalBlur：Windows AEX exported Smartのdual-side 15セルはarm64 publicで15／15 raw exact、
  Rosetta x86_64では従来9セルのみexactです。旧6セル差は実AEX Iterate callback guest executionと
  `expf` leaf counterfactualで二重丸めが原因と確定し、arm64では期待補正なしに閉じました。
  x86_64 libSystem `expf`は旧差分を再現するため、その6セルを516でfail-closeします。
  Universal minOS 11 executable `3528d12c…122a7`はtransactional install済みです。
  arm64は15 exact、x86_64は9 exact＋6 fail-closeを維持し、更新前`4e238ac0…4d77`は
  3つのfull-bundle rollback copyとして保持します。
  Type 3 Layerは後続hostless closureで、固定16×16同一source／Layer・固定tuple／rowbytes／extentの
  PF8／PF16／PF32 3セルだけをexported SmartとMac publicのraw exactへ昇格しました。PF16はSDK準拠
  `round(byte*32768/255)`で、旧`byte*128` internal fixtureをsupersedeします。未列挙条件はfail-closeです。
  Smart routeのWorldSuite acquire／input-output format get／releaseを20-row real-SDK lifecycle closureでfail-closeし、
  現source `49411688…2e845`は製品buildで無効なtest-seam ABI互換だけを追加し、Universal minOS 11 executable
  `856ab700…bc0de`をtransactional installしました。
  installed arm64／Rosettaの各sliceで3正例＋54 source／layout one-away reject（57／57）をsource-built public経路と一致確認し、
  直前`6af1f1d6…67434`は二重backup＋moved-old、その前の`9b5fc6b3…d2eff`も先行handoffに保持しています。
  AEX側はAEXCompat／Unicorn、Mac側もhostlessで、native AEは今回起動せず次の変更との
  batched checkpointへ延期しています。
- OLMColorKey：固定sourceのEdge Blur 32×18／64×36と独立固定48×27 D0/T3/A4を合わせた33セル、固定1×1
  Lab76 2-key順序6セル、固定11×7 Keep／Premultiplied／Replace 24セルは、現行production
  EffectMainのClassic／Smart両public routeでWindows exported Smart ownerへraw exactです。567 one-away、13 callback error／throw、
  World／Color suite 12件、param checkout／checkin各33 failure ordinalはcommit前に
  fail-closeします。minOS 11 Universal toggle24 candidateはtransactional install済みです。両installed sliceを
  source-built replayはClassic 63／Smart 63、installed版のAE-free replayは従来のClassic 60／Smart 60／callback negative 13を
  exact再現します。今回の3セルは未installで、native AE数値claimもありません。
- OLMRadialBlur：Outer 4＋Inner 2／4とSize 25／100をZoom／Rotation・3深度で
  交差した24／24が内部planeからtyped outputまでexactです。
- OLMKiraKira：Mode 1、Mode 2 ramp／Merge 2、Mode 3 Gaussian Length 50の
  public 3-depth経路は、記録済み5×3半透明source、Rotation 0でactive bytes、
  input不変、row paddingまでraw exactです。AEXCompatのarbitrary handle対応
  `94210e51`を用いてMode 2 ramp ownerを接続しました。nondefault Rotationは
  AEXCompat `28d53546`で編集可能になり、Windows raw fixed 1（実処理1°）の
  Mode 1／2／3×3深度、計9／9がexactです。Mode 2 Rotation 22°も自然ownerの
  inner aggregate selectorを回収し、PF8／PF16／PF32すべてraw exactに閉じました。
- OLMKiraKira Mode 4 public owner：Horizontal／Diagonal2／Highlight soloと
  記録済みDiagonal2 multirayは、PF8／PF16／PF32の全12行がraw exactです。
  Windows ownerの角度表は`{90, 0, 45, 135, 0}+Rotation`で、D2 fixtureは
  +136°を使います。旧Macの-44°は幾何学的には同軸でもMode 4の有向recurrenceで
  bit同値ではなく、修正後はseed、warp、ray、aggregate、writerまで一致します。
  未列挙ray構成／geometryへは一般化しません。
- OLMKiraKira Highlight gradient：記録済み5×3／Radius 3（kernel 7）は、
  natural rayからpublic Mode 4 PF8／PF16／PF32までraw exactです。Mode 2の
  同tupleも3深度exactの回帰controlです。Mode 1の同tupleも、PF8入力decodeを
  Windows ownerのfloat32 reciprocal乗算へ合わせて3深度raw exactです。
  任意のMode 1入力や全radius／全gradient直積へは
  一般化せず、期待word補正も採用しません。
- OLMSmoother v1：PF16の64×36 practical geometryでColor Key off／on、
  Do Smooth Range 6／127の4／4 raw worldがexactです。PF32 native arithmeticと
  AE 32bpc host conversionはこの主張に含めません。
- OLMColorKey：64×36 geometry transferは12／12 exactです。旧PF32 Direction 0／
  Distance Type 3／Amount 4残差は、Type 3 direction planeをfloat distance multiply→
  double sin→+1後にfloat cast→float half-scaleの順で構築して閉じました。
  これは記録済み4 tupleの限定証拠で、未列挙geometry／tupleへは一般化しません。
- OLMRadialBlur：Dual Strength×Size×Noiseは固定32×18、Zoom／Rotation・3深度の
  24／24でconsumed paths／typed output exactです。Rotation Type 1の該当6セルは
  inverse-cell closureによりsource scalarを含めraw exactへ更新済みです。
- OLMRadialBlur：RotationのDual Strength×Size×Noise×Offsetは固定32×18、
  PF8／PF16／PF32の24／24でSize×Noise span、Outer／Inner同時寄与、
  選択側Mode 2／3 Offsetを含むconsumed internal planes／typed outputがexactです。
  未列挙tuple／geometryはfail-closeし、この32×18 Rotation複合laneからType 3へは
  一般化しません。
- OLMRadialBlur Type 3：旧AEXCompat pilotのoutput未到達状態はsupersededです。
  以下のPF32 10行＋PF8／PF16各1行は当時の閉鎖で、現在は上記27-pair closureに
  supersedeされたsubsetです。
  PF32 Zoom、固定9×7／rowbytes 160／NV25、same-origin／same-size Layer tupleだけ、
  direct actual internal ownerとMac Classic public EffectMainが5 source×2 Layerの
  10／10 raw exactです。SmartはLayer checkout／plumbingのみを確認し、live AE numerical
  renderはtimeoutしてoutput／readbackを得ていないためpixel exactを主張しません。
  PF8／PF16にも同じ固定tupleのexact source／Layer各1行をhostless typed ownerとして追加し、
  3深度すべてsource span／pre／post／padded output raw exactです。未列挙PF8／PF16 source／Layer、
  null／mismatch Layer、他のgeometry／rowbytes／tupleはfail-closeします。

これらは記録済みfixtureのpublic-entry／installed境界であり、Windows AE pixel exactや
未列挙入力・geometry・パラメーター直積へは昇格しません。

OLMDistanceGradation PF32 Mode 5は、残差の初出をOpenCV 4.5.5 IPP bilateral producer
fieldへ局在した自然traceからscalar演算順を再現しました。direct `expf`、L／T／R／B
逐次加算、late spatial multiply、非縮約float積によりMode 5 non-Powerは6／6、typed matrixは
56 admitted raw exactです。両Universal sliceのfield codegenはhelper call 3・fused op 0です。
PF32 Powerは全8セルを両sliceでfail-closeし、native Windows UCRT captureなしにraw exactとは
主張しません。
AEXCompatの自然public traceとMac public EffectMain contractは
`refs/conformance/olmdistancegradation_public_smart_owner_contract_20260812.{json,md}`
に固定し、arith/codegen closureは
`refs/conformance/olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.{json,md}`と
`refs/conformance/olmdistancegradation_pf32_mode5_universal_codegen_20260812.{json,md}`です。
Power fail-closeを含むUniversal build `231421e4a0c1...`は、直前のinstalled
`b9971c648008...`を3つのfull-bundle rollback copyとして保持したうえで、Distanceだけ
MediaCoreへ導入しました。accepted identityの他9行はbyte不変です。post-change fresh AE smokeは
10本のload／apply／exact mapping／host-frame renderを確認し、Distanceは正規pathから
`231421e4a0c1...`が1本だけmapされ、実行前後のon-disk SHAも不変です。ただしDistanceは
effect-disabled host-frameなので、AE数値exactやMode 5 pixel exactへの昇格ではありません。
install identityは
`refs/conformance/olmdistancegradation_power_failclose_incremental_install_identity_20260812.{json,md}`、
fresh host evidenceは
`refs/conformance/olm_all10_post_distance_power_failclose_fresh_ae_smoke_20260812.json`と
同名`_raw` JSONに固定しています。

現在のhost証拠は、原則として次の条件を前提とします。

- After Effects `26.3x87`
- CPU `SOFTWARE`レンダー
- working space：None
- linear blending：off
- 各証拠に記録された入力解釈、source hash、geometry、bit-depth、パラメーター

この文書での`Exact`は、該当レコード内のbyte一致、またはraw FLOAT32 word一致です。
あらゆる画像や全コントロールの直積に対する主張ではありません。

配布候補はUniversal／ad-hoc署名を検証しています。Developer ID署名とAppleの
notarizationは未実施であり、ダウンロード先のGatekeeperに拒否される可能性があります。

## 対応範囲と重要な境界

| プラグイン | リリース候補の主要モード／native depth | 重要な証拠境界 |
| --- | --- | --- |
| OLMBlur | Legacy／NonLegacy、repeat、bias；PF8／PF16／PF32 | Smart publicはsame-source PF8 12／12、PF16 8／8、PF32 20／20 ownerセルを接続（24／744、16／494、40／60）。旧広域matrixはtyped-worker-only、Classicは固定24×24/default PF8/PF16だけ。source `22eb712a...fdd7`／candidate `ecdf3d93...284d`はbatch5でinstall済み、AEは明示的batched checkpointまで保留 |
| ColorKeep | 固定11×7／padding 12／count 5・100、およびexact source／paletteの固定4×3／padding 8／count 9；PF8／PF16／PF32限定 | 11×7の既存Smart 6＋Classic 4セルを維持。4×3 count9はWindows Smart 3＋Mac Classic 2／Smart 3 depthがraw exact、136 reject。Classic PF32と未列挙source／palette／count／geometry／stride／layoutはfail-close。fresh AEはdisabled host-frameで数値非claim |
| OLMColorKey | fixed-source Edge Blur 32×18／64×36／48×27（48×27はD0/T3/A4のみ）、固定1×1 Lab76 2-key順序、固定11×7 Keep／Premultiplied／Replace；PF8／PF16／PF32 | 現行source public admissionはClassic／Smart各63セルraw exact。567 one-away＋lifecycle/suite/param failureをatomic fail-close。未列挙source／tuple／geometry／layoutへ一般化しない。installed toggle24版は従来60セルのまま。native AE numericalは未実行 |
| OLMToonDilate | copy／dilate、fractional radius、frontier／tie／corner／eligibility；PF8／PF16／PF32 | padded／partial／empty worldとradius -1〜4を確認。実効radiusは`ceil(radius × downsample_x.num / den)`。legacy `PF_Cmd_RENDER`は実AEX同様3深度でno-op、描画はSmartRender経路。現行PF32 radius 13 AE代表はhost smoke |
| OLMDistanceGradation | Inside／Outside／Both、RGB／Layer、Constant／Linear／Sphere／Power、invert／background／blur；PF8／PF16／PF32限定 | actual public command `0x18`にPF32 Smart ownerが存在。固定17×11はPF16 32＋PF32 non-Power 24＝56 admitted raw exact。PF32 Power 8セルはnative Windows UCRT `powf` capture待ちでfail-close。Mode 5 fieldはIPPのdirect `expf`・L/T/R/B順・late spatial multiply・非縮約積を再現し、期待補正なし。未列挙geometry／tuple／layoutは拒否 |
| OLMDirectionalBlur | 基本方向ブラー、Noise Type 1／2／3；PF8／PF16／PF32限定 | Natural64 exact-source 15セル／sliceに加え、exported Smart dual-sideはarm64で15セル、x86_64で9セルをexact-source限定許可。x86_64の残る6は516 fail-close。固定16×16 Type3 Layer 3セルも同一source／Layer限定でraw exact。WorldSuite lifecycle 20行とtest-seam ABI互換を閉じたsource `49411688…2e845`／installed `856ab700…bc0de`の完全bounded replayはarm64 33 exact、x86_64 27 exact＋6 fail-close。Type3は両sliceで3正例＋54 reject。直前`6af1f1d6…67434`と前世代`9b5fc6b3…d2eff`はrollback用。AEはbatched checkpointまで保留 |
| OLMRadialBlur | Zoom／Rotation／Inner；PF8／PF16／PF32 guard付き | PF8 centered neutral Inner Strength 1〜64などbounded複合経路はexact。Rotation Type1のexact-source union 106セルは現installed Universal両sliceのClassic／Smartで全再生し、57 source mutation／sliceをfail-close。Rotation Strength×Size×Noise×Offsetは固定32×18・3深度24／24 internal／output exact。Type 3 Layerは固定9×7／NV25のpaired matrixだけを許可し、各深度15、計45行がtyped internal planesからpadded outputまでexact。現installed両sliceでも全45組と各組のbounded reject controlsをAE-free再生済み。合計151 public cells／slice。PF8 constant／impulseは補正なしRGB writerでexact。未列挙tuple／geometry／source／Layer mismatchはfail-closeし、Windows exported Type3は上流の未初期化worldコピー先のため数値oracleに使わない |
| OLMSmoother2 | v1／v2 classifier、key／invert、Gamma None／All／Colors、range／extra、palette；PF8／PF16／PF32限定 | Gamma／key／smoothing 54／54、palette交差18／18、固定5×5のGamma 1.8／exact-key endpoint交差12／12がraw exact。旧PF8 seamはLUT契約と非縮約scalar積和で解消したが、他の中間値、任意直積、AE hostへは一般化しない |
| OLMKiraKira | Mode 1／2／3／4、ramp、compose、warp／blur；PF8／PF16／PF32限定 | Classic／Smartは同一の固定5×3・14 tuple×3深度がhostless raw exact。現行source `f251b191…6c2`はFP縮約補正を維持し、WorldSuiteを明示acquire／get／releaseする20-row lifecycle closureを追加。現行installed `edd6953f…6a7` public EffectMainは両sliceで42 positive／765 negative／3 request controlsをexact再現。未列挙tuple／source／geometry／layoutとsuite failureはcommit前にfail-close。installed replayはAE-freeで、現identityのnative-AE numerical exactは未主張 |
| OLMSmoother v1 | no-key／Color Key、smoothing range；native PF8／PF16 | PF16 practical 64×36のkey off/on・Range 6/127は4／4 exact。AEXにnative PF32 callbackはなく、32bpc projectではAEがclassic integer pluginの前後をhost-convertするためnative PF32としては未証明 |

残課題として、OLMSmoother v1 PF32はnative laneではなくAE host conversion、Layer Noise Type 3の
汎用検証は未完です。Type 3のmacOS側fixture実行基盤はAEXCompat #1162の対象です。

## AE host境界

AE import、premultiplication、color management、exportの差は、プラグイン演算とは
別のhost境界です。両hostが同じ入力worldを渡していない場合、最終ファイル差だけで
プラグイン演算差とは判定しません。

ColorKeepでは通常importによる16bpc clamp／色変換、Smoother v1ではalpha 254の
premultiply→unpremultiply境界を実際に分離しています。

## 受領済みWindows AE境界 — 7行

使用するパッケージ：

`refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip`

| プラグイン | ケース | depth |
| --- | --- | --- |
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF8 |
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF16 |
| ColorKeep | `colorkeep_opaque_cells_red_darkgray` | PF32 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF8 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF16 |
| OLMKiraKira | `kk_mapped_bm4_mm1_hi_r5_orange_opaque` | PF32 |
| OLMSmoother v1 | `case_0001` | PF16 |

各行でdisabled／effect-onのuncompressed scanline FLOAT32 OpenEXRと、
`BATCH_CONTRACT.json`指定のprocess／module attestationが必要です。PNG previewは
返却物として使用しません。今回の返却はこの条件で7行すべて受理されました。
ただし、受理はWindows観測の成立を意味し、Win/Mac pixel equalityの成立は
プラグイン別の同一条件比較が完了した行だけに限定します。

パッケージSHA-256：

```text
6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652
```

返却物：

`refs/returns/windows/RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip`

返却物SHA-256：

```text
e582b0f368deb6dfbb34de2675e382d2222372705da043151d90dc895f7d7a0a
```

受領記録は
[`olm_windows_ae_release_boundary_minimal_intake_20260806.json`](olm_windows_ae_release_boundary_minimal_intake_20260806.json)
を参照してください。

プラグイン別の同一契約解析：

- ColorKeep：[`colorkeep_windows_mac_ae_boundary_20260806.md`](colorkeep_windows_mac_ae_boundary_20260806.md)
- OLMKiraKira：[`olmkirakira_mode4_windows_boundary_closure_20260806.md`](olmkirakira_mode4_windows_boundary_closure_20260806.md)
- OLMKiraKira hostless exact境界：[`olmkirakira_mode4_highlight_hostless_actual_aex_20260807.md`](olmkirakira_mode4_highlight_hostless_actual_aex_20260807.md)
- OLMSmoother v1：[`olmsmoother_v1_windows_ae_release_boundary_mac_exact_20260806.md`](olmsmoother_v1_windows_ae_release_boundary_mac_exact_20260806.md)
- OLMSmoother v1 host Gamma境界：[`olmsmoother_v1_pf16_crosshost_gamma_boundary_20260806.md`](olmsmoother_v1_pf16_crosshost_gamma_boundary_20260806.md)

## 最終Mac検証結果の読み方

```text
The checked-in status is authoritative only when all valid_for digests match:
- release manifest
- accepted installed identity manifest
- fresh post-acceptance all-ten Mac AE smoke

release_gate_pass additionally requires:
- fixed fixture regression: proven
- Universal installed identities: 10 / 10
- parameter/UI registration: 10 / 10
- current fresh Mac AE rows: 10 proven / 0 pending / 0 invalid
```

再実行：

```sh
python3 scripts/run_olm_release_gate_20260806.py
python3 -m unittest \
  tests.test_olm_release_documentation_20260806 \
  tests.test_windows_ae_release_boundary_minimal_20260806
shasum -a 256 refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip
```

Windows返却物の再検証：

```sh
python3 scripts/verify_windows_ae_release_boundary_minimal_20260806.py \
  RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip
```

プラグイン別の詳細証拠とfail-close条件は
[`olm_release_completion_matrix_20260806.md`](olm_release_completion_matrix_20260806.md)、
インストール済みbinary hashは
[`olm_installed_identity_manifest_20260806.json`](olm_installed_identity_manifest_20260806.json)、
統合結果とその適用対象digestは
[`olm_release_gate_status_20260806.json`](olm_release_gate_status_20260806.json)を参照してください。

## English summary

The ten accepted installed identities pass Universal/signature/build-identity
checks. A release status is current only when its `valid_for` digests bind the
current release manifest, accepted identity manifest, and one fresh
post-acceptance all-ten Mac AE smoke; `release_gate_pass` also requires the
fixed-fixture and parameter/UI gates. Exactness claims remain limited to the declared host,
depths, fixtures, geometries and parameter boundaries. Seven same-contract
Windows AE calibration rows are accepted and bounded per-plugin comparisons
are complete. Host color/export transforms remain separate, so no blanket
cross-host exported-pixel equality is claimed.
