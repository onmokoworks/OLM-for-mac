# T14: triage — is the Classic (PF_Cmd_RENDER) route reachable, and why does it mismatch?

## Facts
F18 established Smart is the route AE uses for these SmartFX plugins, so all exactness work targeted Smart. But Classic
still mismatches heavily: I03 fresh seed 777 Classic mismatches ColorKeep 132, ColorKey 300, DirectionalBlur 299,
DistanceGradation 294, KiraKira 39, RadialBlur 130 (witnesses in `I03-evidence.tar.gz`; S01 has 5,873 more in
`orchestra/reports/S01-wide-mismatch-sweep/classic-witnesses.tar.gz`). Smoother v1 is Classic-only and exact.

## Questions (answer with evidence; no production changes)
1. Reachability: from each original AEX's PiPL/global-setup out_flags/out_flags2 and the AE SDK docs, under which hosts
   or conditions can PF_Cmd_RENDER be called for a plugin that sets SUPPORTS_SMART_RENDER (AE versions, Premiere Pro,
   other AE-plugin hosts, render-queue/proxy paths)? Does the original declare Premiere/other-host support? Do the Mac
   ports declare the same flags?
2. For the three largest plugins (ColorKey, DirectionalBlur, DistanceGradation): take 3 witnesses each and find whether the
   Classic difference is (a) a Mac Classic implementation gap, (b) an oracle/fake-host Classic contract difference
   (e.g. world layout, ROI, extent_hint, downsampling), or (c) intended (e.g. Mac Classic delegating to Smart code).
3. Recommend: fix Classic to match, make Mac Classic refuse, or leave as-is. Estimate the effort per plugin.

## Rules
1-2 processes; read-only except the report and evidence.
