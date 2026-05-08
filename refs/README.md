# Reference Render Diff Harness

`fixtures/test_cellanim.png` is the shared input image for Win/Mac renders.

Expected local-only folders:

- `win/` Windows reference PNG sequence
- `mac/` macOS port PNG sequence
- `diff/` amplified diff output

These folders are ignored by git.

Usage:

```sh
python3 refs/scripts/make_test_cellanim.py
refs/scripts/diff_all.sh
```

For a single file:

```sh
refs/scripts/diff_one.py refs/win/frame.png refs/mac/frame.png refs/diff/frame.diff.png
```
