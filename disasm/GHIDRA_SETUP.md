# Ghidra Setup

Ghidra is installed at:

```txt
/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless
```

The shared project is:

```txt
ghidra_proj/OLM2025.gpr
```

Current 2025 AEX inputs are in:

```txt
plugins_2025/
```

Exported outputs are:

```txt
decomp/<Plugin>.aex.c.txt
disasm/<Plugin>.aex.asm.txt
```

## Commands

Check what has already been exported:

```sh
python3 scripts/ghidra_status.py
```

Re-export one plug-in:

```sh
scripts/ghidra_export_one.sh OLMBlur
scripts/ghidra_export_one.sh plugins_2025/OLMBlur.aex
```

Re-export every 2025 plug-in:

```sh
scripts/ghidra_export_all_2025.sh
```

## Notes

- Large decompiler/disassembly dumps are local artifacts and ignored by git.
- `ExportAll.py` writes one full asm dump and one full decompiled-C dump per
  AEX.
- The GhidraMCP bridge lives under `mcp/`, but interactive MCP use still needs
  Ghidra GUI running with a program open and the GhidraMCP plugin enabled.

## LaurieWired/GhidraMCP

Requested upstream:

```txt
https://github.com/LaurieWired/GhidraMCP
```

The official 1.4 tag has been cloned locally for reference at:

```txt
tools/GhidraMCP/
```

That directory is ignored by git because it is an external tool checkout. The
current local bridge script matches the upstream bridge:

```txt
mcp/bridge_mcp_ghidra.py
```

Direct HTTP smoke checks:

```sh
python3 scripts/ghidra_http.py methods --limit 10
python3 scripts/ghidra_http.py current-function
python3 scripts/ghidra_http.py decompile entryPointFunc
```

Ghidra must have a program open and `GhidraMCPPlugin` enabled. The plugin should
listen on `127.0.0.1:8080`.
