#!/usr/bin/env python3
"""Sample algorithm CLI used to smoke-test the AE-free harness.

Contract:
  identity_image_cli.py --input input.png --params params.json --output output.png
"""

import argparse
import json
from pathlib import Path

from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--params", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with Path(args.params).open(encoding="utf-8") as handle:
        json.load(handle)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.open(args.input).convert("RGBA").save(output)
    print(f"wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
