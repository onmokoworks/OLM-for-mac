# OLMDirectionalBlur Type 2 natural64 historical install / AE smoke（2026-08-12）

Status: **historical installed host smoke pass; superseded identity; pixel gate fail-closed**

この記録のinstalled SHA `9142c199...516f6`は当時のbinaryに限定されます。現行accepted
identityとpost-ColorKeep all-ten smokeは別のDirectional SHA
`1dd6c11889a261fadec2f6cd64440c8a3e7afcadcaa59631714e0ffc232ac3e4`をbindするため、
この個別smokeはcurrent install証拠ではありません。以下はhistorical observationとして
保持し、現行mappingや数値exactへ昇格しません。

Production source SHA-256
`b37b100cf99ef900bb7b661a013e5d1bf4b8e106214887d199adfa8f505c8bc6`
から構成したUniversal（x86_64 + arm64）binary SHA-256
`9142c19937c54dec8ed07a06c14181db1cf274335b599605251982bf671516f6`を
MediaCoreへ単一installし、ad-hoc署名のdeep/strict検証を通した。直前の
binary `f9c914b6fd30b4715d3c469859f2271b0bcdbadd72a15724438cffbf61b09940`
は`/tmp/olmdirectionalblur-natural64-backup.nvITrj/OLMDirectionalBlur.plugin`へ
回復可能な形で退避している。

AE 26.3x87 PID 92353ではvmmap上のinstalled path/countをoperator observation
として確認したが、そのraw vmmap outputは永続化されていないためexact module
identity proofには使わない。byte-preservedに残るのは、scriptがrender直前に
installed pathのon-disk SHAを照合したことと、default effect renderの結果である。
64x36 compへ入力PNG
`0673ea66da1913c89180fed2b9500cd26ce5b88511cf2c59dfd9d515e67a5e4e`
を置き、`OLM Directional Blur`をdefault parameterのまま追加・有効化し、
SOFTWARE / 32bpcでPNGをrenderした。output SHA-256は
`bf59701e9e4e562c9cb3e174bf9302283ea779f0e799303506772ff20208c99e`。
AEが書いたraw resultはbyte-preservedで
`olmdirectionalblur_type2_natural64_current_install_smoke_raw_20260812.json`
へ保存し、そのSHA-256は
`3482673aa164cf03e7f99945a29eb35a74fa4a9e29942370625f6ac2d36112e2`。

このrunはscript-checked current on-disk binary / effect add / render smokeだけを
閉じ、mapped module identityはunpersisted operator observationとしてfail-closeする。
Type 2、Noise Variation 25、64x36の当時のpixel exact性は、同一production
source SHAをbindした当時のbounded hostless closure snapshot
`olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.json`
（SHA-256
`3b75a06e07446df07f4445cc0ce40798febb42087f5c6e353b0c9b9dc6d58647`）
に限定される。現在そのpathにあるclosureとproduction sourceはexact-source
SHA guardを追加した後継版であり、この旧SHAへ戻して照合しない。この
default-parameter AE smokeからWindows/Mac AE pixel exact、
Type-2 natural64 tupleのlive-AE pixel exact、任意parameter/geometryへの昇格は
行わない。
