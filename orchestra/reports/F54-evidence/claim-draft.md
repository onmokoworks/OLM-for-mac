Draft only — not posted. No upstream issue number assigned.

F54: 作業をclaimします。
Scope: optional guest session geometry (downsample, rowbytes padding, extent and request rectangles, pixel aspect, negotiated output, cropped checkouts), bounded on-demand frame allocation, and UHD support.
Acceptance: behavioral Rust tests, Release build, local independent review, direct F53 corpus and survey comparisons, and UHD PF8/16/32 time/RSS measurements.
Dependencies: F53 includes OLM UCRT and SSE NaN-order patches absent from the upstream base. Numerical equality outside the measured matching subset may require separately reviewed upstream work on those dependencies.
No claim, push, or PR is authorized by this ticket; this is text for the user to review.
