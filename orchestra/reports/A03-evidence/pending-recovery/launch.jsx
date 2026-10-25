var f=new File("/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/A03-ae-dialog-watcher/orchestra/state/A03-ae-dialog-watcher/e2e/pending-recovery/jsx-marker.txt");
if (!f.open("w")) throw new Error("marker open failed");
f.write("A03 JSX executed"); f.close();
$.sleep(5000); app.quit();
