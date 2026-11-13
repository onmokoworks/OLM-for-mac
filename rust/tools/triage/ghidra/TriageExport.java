// Headless function fingerprints. No decompiler or network/PDB downloads required.
// @category OLM
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.lang.OperandType;
import com.google.gson.GsonBuilder;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

public class TriageExport extends GhidraScript {
    String hash(String s) throws Exception {
        byte[] d = MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8));
        StringBuilder b = new StringBuilder();
        for (byte v : d) b.append(String.format("%02x", v & 255));
        return b.toString();
    }
    String stable(String s) { return s.replaceAll("::h[0-9a-f]{16}$", ""); }
    String hex(byte[] b) {
        StringBuilder s = new StringBuilder();
        for (byte v : b) s.append(String.format("%02x", v & 255));
        return s.toString();
    }
    String target(Address a, Function f, Map<Address,Integer> indices) {
        if (indices.containsKey(a)) return "local:" + indices.get(a);
        Function other = getFunctionAt(a);
        if (other != null) {
            if (other.isThunk()) other = other.getThunkedFunction(true);
            if (other != null && other.isExternal()) return "import:" + stable(other.getName(true));
            return "function"; // Call graph retained separately; never bake RVAs into code hash.
        }
        Symbol sym = getSymbolAt(a);
        if (a.isExternalAddress()) return "import:" + (sym == null ? "unknown" : sym.getName(true));
        // Preserve referenced literal changes while removing pointers in read-only data.
        try {
            if (currentProgram.getMemory().contains(a)) {
                if (currentProgram.getRelocationTable().hasRelocation(a)) return "relocated-data";
                Data data = getDataAt(a);
                if (data != null && data.isPointer()) return "pointer-data";
                int n = data != null && data.isDefined() ? Math.min(32, data.getLength()) : 8;
                byte[] bytes = new byte[n];
                int read = currentProgram.getMemory().getBytes(a, bytes);
                // A reference can point into a record containing a relocated pointer,
                // not just to the pointer's first byte. Mask every overlapping fixup.
                AddressSet span = new AddressSet(a.subtract(currentProgram.getDefaultPointerSize() - 1), a.add(read - 1));
                Iterator<ghidra.program.model.reloc.Relocation> relocs = currentProgram.getRelocationTable().getRelocations(span);
                while (relocs.hasNext()) {
                    ghidra.program.model.reloc.Relocation r = relocs.next();
                    int start = (int)r.getAddress().subtract(a);
                    int length = r.getBytes() == null ? currentProgram.getDefaultPointerSize() : r.getBytes().length;
                    for (int j=Math.max(0,start); j<Math.min(read,start+length); j++) bytes[j]=0;
                }
                return "data:" + hex(Arrays.copyOf(bytes, read));
            }
        } catch (Exception ignored) {}
        return "address";
    }
    @Override public void run() throws Exception {
        List<Map<String,Object>> functions = new ArrayList<>();
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        while (it.hasNext()) {
            monitor.checkCancelled();
            Function f = it.next();
            if (f.isExternal()) continue;
            List<Instruction> ins = new ArrayList<>();
            Map<Address,Integer> indices = new HashMap<>();
            InstructionIterator ii = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (ii.hasNext()) { Instruction i = ii.next(); indices.put(i.getAddress(), ins.size()); ins.add(i); }
            StringBuilder norm = new StringBuilder(), code = new StringBuilder(), shape = new StringBuilder();
            Set<String> calls = new TreeSet<>();
            for (Instruction i : ins) {
                byte[] bytes = i.getBytes();
                StringBuilder refs = new StringBuilder();
                for (int op=0; op<i.getNumOperands(); op++) {
                    Reference[] rr = i.getOperandReferences(op);
                    boolean address = false;
                    for (Reference r : rr) {
                        if (r.isStackReference() || r.isRegisterReference()) continue;
                        Address a = r.getToAddress();
                        address = true;
                        refs.append(op).append(':').append(target(a, f, indices)).append(';');
                        if (r.getReferenceType().isCall()) {
                            Function callee = getFunctionAt(a);
                            calls.add(callee == null ? a.toString() : callee.getEntryPoint().toString());
                        }
                    }
                    if (address) {
                        byte[] mask = i.getPrototype().getOperandValueMask(op).getBytes();
                        for (int j=0; j<Math.min(bytes.length,mask.length); j++) bytes[j] &= ~mask[j];
                    }
                    shape.append(i.getOperandType(op) & ~OperandType.ADDRESS).append(',');
                }
                // Absolute PE relocations can occur without an operand reference.
                for (int j=0; j<bytes.length; j++) {
                    for (ghidra.program.model.reloc.Relocation r : currentProgram.getRelocationTable().getRelocations(i.getAddress().add(j))) {
                        int n = r.getBytes() == null ? currentProgram.getDefaultPointerSize() : r.getBytes().length;
                        for (int k=j; k<Math.min(bytes.length,j+n); k++) bytes[k]=0;
                    }
                }
                norm.append(i.getMnemonicString()).append(':').append(hex(bytes)).append(':').append(refs).append('\n');
                code.append(i.getMnemonicString()).append(':').append(hex(bytes)).append(':')
                    .append(refs.toString().replaceAll("data:[0-9a-f]+", "data")).append('\n');
                shape.append(i.getMnemonicString()).append(';');
            }
            Map<String,Object> row = new LinkedHashMap<>();
            row.put("address", f.getEntryPoint().toString());
            row.put("rva", f.getEntryPoint().subtract(currentProgram.getImageBase()));
            row.put("name", stable(f.getName(true)));
            row.put("named", f.getSymbol().getSource() != SourceType.DEFAULT);
            row.put("size", f.getBody().getNumAddresses());
            row.put("instructions", ins.size());
            row.put("hash", hash(norm.toString()));
            row.put("code_hash", hash(code.toString()));
            row.put("shape_hash", hash(shape.toString()));
            row.put("calls", calls);
            functions.add(row);
        }
        Map<String,List<String>> callers = new HashMap<>();
        for (Map<String,Object> f : functions) for (String a : (Set<String>)f.get("calls"))
            callers.computeIfAbsent(a, k -> new ArrayList<>()).add((String)f.get("address"));
        for (Map<String,Object> f : functions) f.put("callers", callers.getOrDefault(f.get("address"), new ArrayList<>()));
        Map<String,Object> root = new LinkedHashMap<>();
        root.put("schema_version", 1);
        root.put("ghidra_version", ghidra.framework.Application.getApplicationVersion());
        root.put("language", currentProgram.getLanguageID().toString());
        root.put("functions", functions);
        try (Writer w = new OutputStreamWriter(new FileOutputStream(getScriptArgs()[0]), StandardCharsets.UTF_8)) {
            new GsonBuilder().setPrettyPrinting().create().toJson(root, w);
        }
    }
}
