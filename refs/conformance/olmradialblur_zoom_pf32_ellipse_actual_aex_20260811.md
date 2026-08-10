# OLM RadialBlur PF32 Zoom ellipse — 2026-08-11

Status: **exact**

Ratio 2/5 × Angle 0/30/90 の6セルで、actual AEX と production の pre-blur、post-blur、padded PF32 output が全段 byte-exact です。Angle は radians の16.16整数を AEX と同じく直接 double sin/cos へ渡し、Ratio は `sin(theta) * ratio` を先にfloat演算してからradiusを掛けます。
