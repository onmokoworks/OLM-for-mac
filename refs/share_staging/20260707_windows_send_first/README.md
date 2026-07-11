# Windows Send First

The authoritative selector is:

```bash
python3 scripts/print_next_olm_action.py ~/Downloads /tmp
```

This project-local staging folder is generated from
`refs/reports/pending_runtime_trace_packages.json`.

## Package

- Request: `olmdirectionalblur_front_alpha_host_boundary_2025_20260711`
- File: `olmdirectionalblur_front_alpha_host_boundary_2025_20260711.zip`
- Source: `refs/runtime_trace_packages/olmdirectionalblur_front_alpha_host_boundary_2025_20260711.zip`
- SHA-256: `08465290715f7cdd766a1e374d39174c5f984028d71b48c17f3f62f8184ee66a`

## Why This One

- 

## Hard Lane Context

{'note': 'refs/conformance/dblur_alpha_host_boundary_20260711.md', 'summary': 'The front-alpha kernel is binary-grounded, but the retained June19 reference omitted loaded-AEX identity and the exact PF input world. This one hash-gated invocation-bound capture decides host input, AEX generation, and output/export ownership without PNG tuning.'}

## Acceptance

- `refs/conformance/dblur_alpha_host_boundary_20260711.md`

## Stop Condition

Accept only status=answered with the exact 2025 SHA256, one input and one output hit bound by PID/RBP/RBX/output-world token, valid 1920x1080 PF worlds, and two 8294400-byte tight ARGB8 dumps.

## Share Check

```bash
test -f /Volumes/onmk/olm_pr/new/olmdirectionalblur_front_alpha_host_boundary_2025_20260711.zip \
  && shasum -a 256 /Volumes/onmk/olm_pr/new/olmdirectionalblur_front_alpha_host_boundary_2025_20260711.zip
```
