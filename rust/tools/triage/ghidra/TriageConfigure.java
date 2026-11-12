// @category OLM
import ghidra.app.script.GhidraScript;
public class TriageConfigure extends GhidraScript {
    @Override public void run() throws Exception {
        // Fingerprints depend only on the supplied image, not mutable external PDBs.
        setAnalysisOption(currentProgram, "PDB Universal", "false");
    }
}
