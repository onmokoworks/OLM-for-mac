"""Minimal stdlib MCP client for the NExpression AE bridge (localhost:9224).

Mirrors the Windows T18 package's tools/ae_mcp.py Client exactly, so scripts
written against one work against the other.
"""
from __future__ import annotations

import json
import time
import urllib.request


class Client:
    def __init__(self, endpoint="http://127.0.0.1:9224/mcp", timeout=15):
        self.endpoint, self.timeout, self.session, self.sequence = endpoint, timeout, None, 0
        self.rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                "clientInfo": {"name": "claude-code-olm", "version": "1"}})
        self.rpc("notifications/initialized", notification=True)

    def rpc(self, method, params=None, notification=False):
        self.sequence += 1
        body = {"jsonrpc": "2.0", "method": method}
        if not notification:
            body["id"] = self.sequence
        if params is not None:
            body["params"] = params
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        request = urllib.request.Request(self.endpoint, json.dumps(body).encode(), headers)
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            self.session = response.headers.get("Mcp-Session-Id", self.session)
            if notification or response.status == 202:
                return None
            if "text/event-stream" in response.headers.get("Content-Type", ""):
                data = []
                while True:
                    line = response.readline()
                    if not line:
                        raise RuntimeError("MCP stream ended before response")
                    line = line.decode("utf-8").rstrip("\r\n")
                    if line.startswith("data:"):
                        data.append(line[5:].lstrip())
                    elif not line and data:
                        payload = "\n".join(data)
                        data = []
                        if not payload.strip():
                            continue
                        item = json.loads(payload)
                        if item.get("id") == self.sequence:
                            break
            else:
                item = json.load(response)
        if "error" in item:
            raise RuntimeError(item["error"])
        return item["result"]

    def call(self, name, **arguments):
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise RuntimeError(result)
        blocks = [c["text"] for c in result.get("content", []) if c["type"] == "text"]
        text = "\n".join(blocks)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def execute(self, script, timeout=300, poll=0.5):
        state = self.call("get_bridge_status")
        if (state.get("runningScriptJobId") is not None or state.get("scriptJobsQueued")
                or state.get("mainThreadLastTickMsAgo", 1_000_000) > 5000):
            raise RuntimeError(f"AE already busy: {state}")
        job = self.call("execute_script_async", script=script)
        start = time.monotonic()
        while True:
            time.sleep(poll)
            state = self.call("get_bridge_status")
            if (state.get("runningScriptJobId") is None and not state.get("scriptJobsQueued")
                    and state.get("mainThreadLastTickMsAgo", 1_000_000) < 1000):
                result = self.call("get_script_job", jobId=job["jobId"])
                if result["status"] == "error":
                    raise RuntimeError(result)
                if result["status"] == "done":
                    return result
            if time.monotonic() - start > timeout:
                raise TimeoutError(f"AE no progress for {timeout}s; job={job}; bridge={state}")
