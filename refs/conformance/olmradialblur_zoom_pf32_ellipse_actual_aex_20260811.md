# OLM RadialBlur PF32 Zoom ellipse — 2026-08-11

Status: **bounded_exact**

Ratio 2/5 × Angle 0/30/90 の6セルを捕捉しました。Ratio 2・Angle 0 は actual AEX と production の pre-blur、post-blur、padded PF32 output が全段 byte-exact です。他の5セルは pre-blur から差があるため admission せず、証拠境界として残します。
