# DG_STRATEGY_A_REPORT

Local Unicorn emulation of `FUN_181170480` (DistanceGradation 16bpc
compose/word-store callback), Strategy A per `DG_M1_NOTES.md`. No
Windows round trip used. Binary is executed directly.

## 到達点
- leaf 検証 (degenerate/use_bg): use_bg=1 got=('0x8000', '0x4000', '0x8000', '0x2000') expected=('0x8000', '0x4000', '0x8000', '0x2000') match=True; use_bg=0 got=('0x0', '0x0', '0x0', '0x0') expected=('0x0', '0x0', '0x0', '0x0') match=True.
- leaf 検証結果: PASS。ABI (stack arg5 = [RSP+0xd0] 相当) はこの結果で 確認された。
- leaf 検証が通ったため、case_0023 triplet compose を実行した。

## ABI 確定事項
- 出力ピクセルポインタ (5th arg) は Windows x64 標準スタック配置 (`shadow(0x20) + retaddr(0x8)` 相対 `[RSP+0x28]` at call site == callee prologue `PUSH RDI(+8); SUB RSP,0xa0` 後の `[RSP+0xd0]`) で正しく渡ることを `aex_loader.call_function` の既存スタック引数配置ロジック（変更なし）で確認した。
- **word 順の訂正**: `DG_M1_NOTES.md` 1b は ARGB=A,R,G,B と記載していたが、degenerate 分岐 (`0x1811704ad-0x181170509`) と normal 分岐 (`0x1811707fc-0x181170828`) の両方の disasm を直接オペランド追跡すると、メモリ word 順は **A(+0), G(+2), R(+4), B(+6)** である（例: degenerate 分岐で `BGg*32768 -> EDX -> [RDI+2]`, `BGr*32768 -> ECX -> [RDI+4]`, `BGb*32768 -> R8D -> [RDI+6]`, alpha `0x8000 -> [RDI]`）。fieldの読み取り位置 `[RCX+2]` も 同じ word 順で 'G' スロットに一致するが、この値は色ではなく distance field 値として再利用される。

## triplet ビット照合結果
- (414,393) field_x=0.0: raw AGRB words=`('0x8000', '0x0', '0xe0e', '0x7777')`, raw RGBA=(3598, 0, 30583, 32768), promoted RGBA (÷32768×65535)=(7195, 0, 61165, 65535), Windows final RGBA16=(7195, 0, 61165, 65535) -> 一致
- (415,393) field_x=1.0: raw AGRB words=`('0x8000', '0x0', '0x8000', '0x0')`, raw RGBA=(32768, 0, 0, 32768), promoted RGBA (÷32768×65535)=(65535, 0, 0, 65535), Windows final RGBA16=(65535, 0, 0, 65535) -> 一致
- (416,393) field_x=1.0: raw AGRB words=`('0x8000', '0x0', '0x8000', '0x0')`, raw RGBA=(32768, 0, 0, 32768), promoted RGBA (÷32768×65535)=(65535, 0, 0, 65535), Windows final RGBA16=(65535, 0, 0, 65535) -> 一致

## Mac 港への含意
- 3ピクセル全てで compose 出力（÷32768×65535 promoted）が Windows final RGBA16 と一致した。これは case_0023 の endpoint 選択（Gradation色 vs BG色）が `field_x` の 0/1 判定と `Invert=0` の 1-X 変換、Linear pass-through、use_bg ブレンド式で完全に説明できることをローカルで binary-grounding したことを意味する。
- したがって、Windows debugger による xy-binding が3回失敗した case_0023 の compose 段は、この emulation で代替確定できた。残る乖離（IR記録の 73px 中 65px の `inside=1.0` 系列など）は compose 段ではなく、upstream の field 値そのもの（distanceTransform/threshold 正規化）に起因することが一層裏付けられる。

## 残課題
- **field_x の値は INFERRED**: このスクリプトは (414,393)=0.0, (415,393)=(416,393)=1.0 を「Inside Threshold=36 crossing の前後」という記録済み事実から仮定して注入した。実際の raw inside-distance 値 (35.014/36.014/37.014) をどう normalize/threshold して0/1 の binary field_x に落とすかという upstream 段（`FUN_181174760` の distanceTransform→threshold→normalize）はこの run では再現していない。compose 段の binary-grounding はできたが、field 生成段の binary-grounding は別作業として残る。
- promotion 式 `trunc(half_word/32768*65535)` はこの run で3ピクセル全てにおいて Windows final RGBA16 と一致することから EMPIRICALLY 再導出したものであり、`FUN_181170480` 自体の disasm には現れない（promotion は AE ホスト側で行われるため compose 関数のコードスコープ外）。単純な `×2`（half-range 0x8000 を 0x10000 として扱う仮定）は (414,393) で ±1 の誤差を生み、Windows と不一致だった。`÷32768×65535` への訂正で3ピクセル全てが一致した。この promotion 式は本 triplet（3点）でのみ検証されており、他の値域（特に中間値・丸め境界）での一般性は未確認。
- 8bpc sibling (`FUN_181170870`) や Sphere/Power (`interp_mode==3/4`) など他の interp_mode / render_mode 分岐はこの run では検証していない（case_0023 は Linear/Gradation のみ）。
