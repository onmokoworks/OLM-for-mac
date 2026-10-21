# OLMColorKey current Universal install / AE smoke

Status: **installed host smoke pass; pixel promotionなし**。

現行Universal `x86_64 + arm64`／ad-hoc署名済みbinary
`350ed6eb00c078952ad512b621e3489e6e6ed47d9129e3c11748f547fc441230`
をMediaCoreへ単一installした状態で、停止中のAfter Effectsからfreshな26.3x87
processを起動した。起動直後はOLMColorKey mappingがなく、64×36／32bpc／Software／
working space NoneのAE solidへ `OLM Color Key` を追加した後、PID `98933` はexactな
installed pathを1本だけmappingした。既定217 leaf parameterは前後不変で、effect offと
default no-op effect onの2本のEXRレンダーが完了し、installed binary hashも不変だった。
AEはスモーク後に終了済み。

両EXRのSHA-256は
`7bf128f1809160aca2d8d5f6c3f6f67ca3e6c6558c78c83f844f010923ffe855`
で一致する。これは `Use Color 1=0` の既定no-op host smokeであり、Windowsとのpixel
比較でも、Lab76 2-key tupleのlive-AE再現でもない。Lab76のbounded raw-exact主張は
`olmcolorkey_lab76_multikey_order_closure_20260812.{json,md}`だけが所有する。

runnerが生成したreportは加工せず
`olmcolorkey_current_install_smoke_raw_20260812.json`へ保存し、そのSHA-256は
`92addd3f2aa9a3af246749b3cd86f2a2854e8738c66608db4f72333b8729a8aa`。
このsummaryとtamper testはproduction source、installed binary、runner、raw report、
Lab76 closureの各SHAと、fresh process／lazy-load後exact path／render／quit gateを束ねる。
