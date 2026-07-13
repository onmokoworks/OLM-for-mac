#!/usr/bin/env python3
"""Synthetic end-to-end smoke for compilation, validation, and bundling."""

from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.windows_witness.compiler import compile_witness
from tools.windows_witness.runtime import bundle_return, read_json, validate_trace


ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "examples" / "synthetic" / "witness-spec.json"


def trace(contract: dict) -> str:
    common = (
        "run_id=synth-smoke ae_pid=5150 module_base=0x7ff900000000 "
        f"aex_sha256={contract['plugin']['aex_sha256']} project_bpc=16 renderer=Software"
    )
    return "\n".join(
        f"SYNTH_CAPTURE {common} case_id={case['id']} sample={case['template_values']['sample']} value={index + 1}"
        for index, case in enumerate(contract["cases"])
    ) + "\n"


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        package_a, zip_a = compile_witness(SPEC, root / "package-a", root / "a.zip")
        _, zip_b = compile_witness(SPEC, root / "package-b", root / "b.zip")
        assert zip_a.read_bytes() == zip_b.read_bytes(), "package ZIP is not deterministic"
        contract = read_json(package_a / "witness-contract.json")
        identity = {"run_id": "synth-smoke", "ae_pid": 5150, "module_base": "0x7ff900000000"}
        answered = validate_trace(contract, trace(contract), identity)
        assert answered["status"] == "answered", answered
        bad = validate_trace(contract, trace(contract).splitlines()[0] + "\n", identity)
        assert bad["status"] == "exact_bind_failure", bad
        work_a = root / "work-a"
        work_b = root / "work-b"
        for work in (work_a, work_b):
            for case in contract["cases"]:
                artifact = work / "exports" / case["id"] / f"{case['id']}.png"
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_bytes(("synthetic-" + case["id"]).encode("ascii"))
        result_a, return_a = bundle_return(contract, copy.deepcopy(answered), work_a)
        result_b, return_b = bundle_return(contract, copy.deepcopy(answered), work_b)
        assert result_a["status"] == result_b["status"] == "answered"
        assert return_a.read_bytes() == return_b.read_bytes(), "return ZIP is not deterministic"
        launcher = (package_a / "artifacts" / "run_witness.ps1").read_text(encoding="utf-8")
        queue = (package_a / "scripts" / "ae_witness_queue.jsx").read_text(encoding="utf-8")
        assert '"root=" + root + "\\n" +' in queue
        assert '"queue_sha256=" + queueSha256 + "\\n", false);' in queue
        assert 'env("WINDOWS_WITNESS_QUEUE_SHA256")' in queue
        assert 'rename("queue_bootstrap.log")' in queue
        assert 'runId + "\\n"' in queue
        assert 'runId + "\n"' not in queue
        assert "-ArgumentList @('-m', '-r', $queuePath)" not in launcher
        assert "function ConvertTo-WindowsCommandLineArgument" in launcher
        assert "$launchArgumentValues = @('/d', '/s', '/c', $launchWrapper)" in launcher
        assert "'-cf', $bootstrapCdbScript, '--', $AfterFxPath" not in launcher
        assert "$env:ComSpec -ArgumentList $launchArguments" in launcher
        assert "'-o', '-pd', '-g', '-G'" not in launcher
        assert "$afterFxCommandLine = Join-WindowsCommandLine @($AfterFxPath, '-m', '-r', $normalizedQueuePath)" in launcher
        assert "$launchArguments = Join-WindowsCommandLine $launchArgumentValues" in launcher
        assert "$observedCommandLine.IndexOf($normalizedQueuePath" not in launcher
        assert "'jsx_command_line_preflight'" not in launcher
        assert "('OLMWitness\\w_' + $shortId)" in launcher
        assert "$bootstrapCdbTrace = Join-Path $launchDir 'boot.log'" in launcher
        assert "Start-Process -FilePath $env:ComSpec -ArgumentList $launchArguments" in launcher
        assert "ld:AfterFX.exe" not in launcher
        assert "WITNESS_CDB_PLUGIN_LOADED" not in launcher
        assert "sxi ibp" not in launcher
        assert "Copy-WitnessLaunchEvidence" in launcher
        assert "-FilePath $CdbPath" in launcher
        assert "$dispatchArguments" not in launcher
        assert "afterfx_process_diagnostics.json" in launcher
        assert "'jsx_launch'" in launcher
        assert "Read-QueueBootstrapBinding $queueBootstrap" in launcher
        assert "[string]$queueBootstrapBinding.queue_sha256 -cne $queueHash" in launcher
        assert "bootstrap_plugin_load_claimed = [bool]$bootstrapPluginLoadClaimed" in launcher
        assert launcher.index("if ($code -eq 0) { Stop-WitnessProcesses }") > launcher.index("& py -3 $runtimePath bundle")
        for template in (package_a / "cdb").glob("*.cdb.in"):
            assert '.logopen /t "{{TRACE_PATH}}"' in template.read_text(encoding="ascii")
    print("[OK] windows_witness synthetic smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
