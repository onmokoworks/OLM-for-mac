try { var f=new File("/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/A03c-ae-scripting-pref-and-live-proof/orchestra/state/A03c-ae-scripting-pref-and-live-proof/e2e/first-clean-launch/jsx-marker.txt");
if (!f.open("w")) throw new Error("marker open failed: " + f.error);
f.write("A03c JSX executed; scripting=" + app.preferences.getPrefAsLong("Main Pref Section v2", "Pref_SCRIPTING_FILE_NETWORK_SECURITY")); f.close();
} catch (e) { $.writeln("A03c marker error: " + e); }
finally { app.quit(); }
