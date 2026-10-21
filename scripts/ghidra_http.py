#!/usr/bin/env python3
"""Small CLI for the GhidraMCP HTTP endpoint.

Ghidra must be running with GhidraMCPPlugin enabled. The default endpoint is
127.0.0.1:8080; use --base to query another CodeBrowser instance.
This is useful even when the MCP bridge is not loaded as a Codex tool.
"""

import argparse
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE = "http://127.0.0.1:8080/"


def request(base, method, endpoint, data=None, params=None):
    url = base.rstrip("/") + "/" + endpoint.lstrip("/")
    if params:
        url += "?" + urlencode(params)
    body = None if data is None else data.encode("utf-8")
    req = Request(url, data=body, method=method)
    with urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base", default=DEFAULT_BASE,
        help=f"GhidraMCP HTTP base URL (default: {DEFAULT_BASE})"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("methods")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=50)

    p = sub.add_parser("exports")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=50)

    sub.add_parser("current-function")
    sub.add_parser("current-address")
    sub.add_parser("info")

    p = sub.add_parser("decompile")
    p.add_argument("name")

    p = sub.add_parser("decompile-address")
    p.add_argument("address")

    p = sub.add_parser("disassemble")
    p.add_argument("address")

    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()

    if args.cmd == "methods":
        text = request(args.base, "GET", "methods", params={"offset": args.offset, "limit": args.limit})
    elif args.cmd == "exports":
        text = request(args.base, "GET", "exports", params={"offset": args.offset, "limit": args.limit})
    elif args.cmd == "current-function":
        text = request(args.base, "GET", "get_current_function")
    elif args.cmd == "current-address":
        text = request(args.base, "GET", "get_current_address")
    elif args.cmd == "info":
        text = request(args.base, "GET", "info")
    elif args.cmd == "decompile":
        text = request(args.base, "POST", "decompile", data=args.name)
    elif args.cmd == "decompile-address":
        text = request(args.base, "GET", "decompile_function", params={"address": args.address})
    elif args.cmd == "disassemble":
        text = request(args.base, "GET", "disassemble_function", params={"address": args.address})
    elif args.cmd == "search":
        text = request(args.base, "GET", "searchFunctions", params={"query": args.query, "offset": args.offset, "limit": args.limit})
    else:
        parser.error(args.cmd)

    sys.stdout.write(text)
    if text and not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
