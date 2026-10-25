var f=new File("/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/A03b-ae-crash-flags-and-ocr/orchestra/state/A03b-ae-crash-flags-and-ocr/e2e/first-clean-launch/jsx-marker.txt");
if (!f.open("w")) throw new Error("marker open failed");
f.write("A03b JSX executed"); f.close();
$.sleep(5000); app.quit();
