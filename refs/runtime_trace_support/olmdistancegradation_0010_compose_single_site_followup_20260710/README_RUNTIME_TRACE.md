# OLM Runtime Trace Request Package

Run only request
`olmdistancegradation_0010_compose_single_site_followup_20260710`.

Start with these separate commands from the extracted package root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1 -Site field -X 6 -Y 40
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_olmdistancegradation_0010_compose_single_site_followup_20260710.ps1 -Site source -X 6 -Y 40
```

Run `-Site writer` only after field and source are stable. Do not combine the
sites in one debugger invocation.

The authoritative contract is
`refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md`.
Fill `RETURN_RUNTIME_TRACE_TEMPLATE.json`, include every referenced console
artifact, and zip the result for return.
