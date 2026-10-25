try { var f=new File("/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/A03e-ae-watcher-workspace-and-live/orchestra/state/A03e-ae-watcher-workspace-and-live/live-dispatch/next-clean-launch/jsx-marker.txt");
if (!f.open("w")) throw new Error("marker open failed: " + f.error);
f.write("A03c JSX executed; scripting=" + app.preferences.getPrefAsLong("Main Pref Section v2", "Pref_SCRIPTING_FILE_NETWORK_SECURITY")); f.close();
} catch (e) { $.writeln("A03c marker error: " + e); }
finally { app.quit(); }
