# OLMKiraKira Mode4 Highlight gradient PF32 seam（2026-08-12）

Status: **fail_closed_pf32_seam**

5×3 gradientのsame-run seed 15 wordsからHighlight rayで初めてword 3/11が各1 ULPずれる。actual ray以後のaggregate 15 pixelsとPF8/PF16/PF32 writerはexact。constant Highlight controlも全段exact。一般boxFilter則を回収できていないためproductionは変更せずPF32 gradientをfail-closeする。
