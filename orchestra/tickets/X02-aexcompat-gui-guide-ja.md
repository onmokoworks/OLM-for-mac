depends: X01-aexcompat-platform-parity
# X02: AEXCompat GUI guide in Japanese (primary), with an English translation

## Why
- The user wants the GUI guidelines in Japanese too. The current docs are English-only (`docs/WINDOWS_GUI_EFFECT_CHAIN.md`, `analysis/MACOS_WINDOWS_GUI_PARITY_*`, README sections and `docs/images/aexcompat-gui.png`).

## Do
- Write `docs/GUI_GUIDE_JA.md` in AEXCompat as the primary text, and `docs/GUI_GUIDE.md` (English) as its translation. Cover both Windows and macOS **as one guide**, because X01 made the features the same. Where a difference remains, say so plainly in one line.
- Contents:
  - what the GUI is for;
  - starting it on each OS;
  - choosing an AEX and an image;
  - Effect Controls (editing, reset, live render);
  - viewing (input/output/compare, zoom/pan);
  - pixel depth;
  - effect chains;
  - export (PNG and raw sidecars);
  - the diagnostics/report panel;
  - common errors and what to do.
  Use screenshots only if they can be produced locally on macOS. Keep the existing image.
- Style (the user's preferences, same as OLM's docs):
  - plain, direct Japanese;
  - no AI-ish phrasing ("〜のは〜です" clefts, padded meta-sentences);
  - do not explain the obvious;
  - say concretely what to do.
  Proofread with the yomiyasu skill's lint (`~/.claude/skills/yomiyasu/scripts/yomiyasu_lint.py --doc-type manual`), and fix what it flags where it makes sense.
- Link both guides from the README. Same AEXCompat branch rules as X01 (stack on its branch; drafts only for claim/PR).

## Rules
- Docs only, plus README links. Use 1 process.
