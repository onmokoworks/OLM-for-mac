# Nightly fuzz summary

E = exact; M = mismatch; R = Mac refusal with successful AEX; U = uncompared/unavailable.
Zero rows mean no completed observations, not a pass. Counts exclude shrinking.

| Plugin | Sampler | E | M | R | U |
|---|---|---:|---:|---:|---:|
| olmcolorkey | default | 18368 | 3 | 0 | 6 |
| olmcolorkey | realistic | 0 | 0 | 0 | 0 |
| olmcolorkey | realistic-v2 | 0 | 0 | 0 | 0 |
| olmcolorkey | odd-even-v1 | 0 | 0 | 0 | 0 |
| olmdirectionalblur | default | 3059 | 0 | 0 | 12 |
| olmdirectionalblur | realistic | 0 | 0 | 0 | 0 |
| olmdirectionalblur | realistic-v2 | 0 | 0 | 0 | 0 |
| olmdirectionalblur | odd-even-v1 | 0 | 0 | 0 | 0 |
| colorkeep | default | 0 | 0 | 0 | 0 |
| colorkeep | realistic | 0 | 0 | 0 | 0 |
| colorkeep | realistic-v2 | 0 | 0 | 0 | 0 |
| colorkeep | odd-even-v1 | 0 | 0 | 0 | 0 |
| olmblur | default | 0 | 0 | 0 | 0 |
| olmblur | realistic | 0 | 0 | 0 | 0 |
| olmblur | realistic-v2 | 0 | 0 | 0 | 0 |
| olmblur | odd-even-v1 | 0 | 0 | 0 | 0 |
| olmtoondilate | default | 0 | 0 | 0 | 0 |
| olmtoondilate | realistic | 0 | 0 | 0 | 0 |
| olmtoondilate | realistic-v2 | 0 | 0 | 0 | 0 |
| olmtoondilate | odd-even-v1 | 0 | 0 | 0 | 0 |
| olmsmoother2 | default | 0 | 0 | 0 | 0 |
| olmsmoother2 | realistic | 0 | 0 | 0 | 0 |
| olmsmoother2 | realistic-v2 | 0 | 0 | 0 | 0 |
| olmsmoother2 | odd-even-v1 | 0 | 0 | 0 | 0 |
| olmsmoother | default | 0 | 0 | 0 | 0 |
| olmsmoother | realistic | 0 | 0 | 0 | 0 |
| olmsmoother | realistic-v2 | 0 | 0 | 0 | 0 |
| olmsmoother | odd-even-v1 | 0 | 0 | 0 | 0 |
| olmdistancegradation | default | 0 | 0 | 0 | 0 |
| olmdistancegradation | realistic | 0 | 0 | 0 | 0 |
| olmdistancegradation | realistic-v2 | 0 | 0 | 0 | 0 |
| olmdistancegradation | odd-even-v1 | 0 | 0 | 0 | 0 |
| olmkirakira | default | 0 | 0 | 0 | 0 |
| olmkirakira | realistic | 0 | 0 | 0 | 0 |
| olmkirakira | realistic-v2 | 0 | 0 | 0 | 0 |
| olmkirakira | odd-even-v1 | 0 | 0 | 0 | 0 |
| radialblur | default | 0 | 0 | 0 | 0 |
| radialblur | realistic | 0 | 0 | 0 | 0 |
| radialblur | realistic-v2 | 0 | 0 | 0 | 0 |
| radialblur | odd-even-v1 | 0 | 0 | 0 | 0 |

## New witnesses

New means first retained failure signature in this date directory; not necessarily new to the repository.

- `witnesses/c2d799e6b17314d055e78508.json`: pixels:PF32:nonfinite; first difference/status: `{"diff": {"actual_bytes": 128, "actual_word_hex": "4523c17f", "different_bytes": 12, "different_words": 3, "expected_bytes": 128, "expected_word_hex": "b7b6b63e", "first_byte": 100, "first_word": 25}, "error": 0, "metadata": {"ERROR": "0"}, "raw_sha256": "75374f10be7fc524cdbbb64e4e85d43701877c69190ee97ede0c1d2ca4ef32e5", "status": "mismatch"}`

Session: `{"actual_jobs": 1, "elapsed_seconds": 900.016, "hours": 0.25, "jobs_limit": 1, "retained_bytes": 48310, "start": "20261025T183048051312", "status": "deadline"}`
