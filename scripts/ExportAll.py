# Ghidra post-script: dump disasm + decompiled C for every function
# @category OLM
# @runtime Jython

import os
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

out_dir = os.environ.get("OLM_OUT_DIR", "/tmp/olm_out")
prog = currentProgram
name = prog.getName()

disasm_path = os.path.join(out_dir, "disasm", name + ".asm.txt")
decomp_path = os.path.join(out_dir, "decomp", name + ".c.txt")

for p in (disasm_path, decomp_path):
    d = os.path.dirname(p)
    if not os.path.isdir(d):
        os.makedirs(d)

listing = prog.getListing()
fm = prog.getFunctionManager()
monitor = ConsoleTaskMonitor()

print("[ExportAll] %s: writing %s / %s" % (name, disasm_path, decomp_path))

with open(disasm_path, "w") as f:
    f.write("; program: %s\n" % name)
    f.write("; language: %s\n\n" % prog.getLanguageID())
    for func in fm.getFunctions(True):
        f.write("\n; === %s @ %s ===\n" % (func.getName(), func.getEntryPoint()))
        body = func.getBody()
        it = listing.getInstructions(body, True)
        while it.hasNext():
            ins = it.next()
            f.write("%s  %s\n" % (ins.getAddress(), ins.toString()))

decomp = DecompInterface()
decomp.openProgram(prog)
with open(decomp_path, "w") as f:
    f.write("// program: %s\n\n" % name)
    for func in fm.getFunctions(True):
        res = decomp.decompileFunction(func, 60, monitor)
        if res is not None and res.decompileCompleted():
            f.write("// === %s @ %s ===\n" % (func.getName(), func.getEntryPoint()))
            f.write(res.getDecompiledFunction().getC())
            f.write("\n")
        else:
            f.write("// FAILED %s @ %s\n\n" % (func.getName(), func.getEntryPoint()))

print("[ExportAll] done: %s" % name)
