"""One localhost HTTP listener: Streamable HTTP MCP and a small Python JSON API."""
import asyncio
from contextlib import asynccontextmanager
import os
import time

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
import psutil
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn

from backend import Hub
from runtime import HOME, atomic_json

METHODS = {'programs_list', 'list_functions', 'decompile_batch', 'xrefs', 'call_graph',
           'data_types', 'bulk_edit', 'export_function', 'add_version', 'add_program', 'reset_decompilers'}
_owned_job = None
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


def contain_process_tree():
    """Own only this server and its future descendants; kill children even after a crash."""
    global _owned_job
    if os.name != 'nt':
        return
    import win32api
    import win32job
    job = win32job.CreateJobObject(None, '')
    limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
    limits['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)
    win32job.AssignProcessToJobObject(job, win32api.GetCurrentProcess())
    _owned_job = job  # Retained until process exit, after the ASGI shutdown saves/closes Ghidra.


def serve(port, token, workers):
    contain_process_tree()
    hub = Hub(workers=workers)
    server = None

    mcp = FastMCP('OLM Ghidra Hub', host='127.0.0.1', port=port,
                  stateless_http=True, json_response=True)

    @mcp.tool(annotations=READ_ONLY)
    async def list_programs() -> list[dict]:
        """List all persistent analyzed programs and binary hashes."""
        return await asyncio.to_thread(hub.programs_list)

    @mcp.tool(annotations=READ_ONLY)
    async def list_functions(programs: list[str] | None = None, query: str = '',
                             offset: int = 0, limit: int = 100) -> dict:
        """Search function names across all programs (or selected program names)."""
        return await asyncio.to_thread(hub.list_functions, programs, query, offset, limit)

    @mcp.tool(annotations=READ_ONLY)
    async def decompile_batch(items: list[dict[str, str]], parallel: bool = True, timeout: int = 60) -> dict:
        """Decompile [{program, function: address-or-name}, ...] using a shared bounded pool."""
        return await asyncio.to_thread(hub.decompile_batch, items, parallel, timeout)

    @mcp.tool(annotations=READ_ONLY)
    async def xrefs(program: str, address: str) -> dict:
        """Incoming and outgoing references at an address."""
        return await asyncio.to_thread(hub.xrefs, program, address)

    @mcp.tool(annotations=READ_ONLY)
    async def call_graph(program: str, functions: list[str] | None = None, depth: int = 1) -> dict:
        """Static function call graph; indirect calls may be missing."""
        return await asyncio.to_thread(hub.call_graph, program, functions, depth)

    @mcp.tool(annotations=READ_ONLY)
    async def data_types(program: str, query: str = '', offset: int = 0, limit: int = 100) -> dict:
        """Search types and inspect structure fields."""
        return await asyncio.to_thread(hub.data_types, program, query, offset, limit)

    @mcp.tool()
    async def bulk_edit(rows: list[dict], provenance: str = 'MCP client') -> list[dict]:
        """Transaction per program. Row: program,function,name/signature/comment,optional expected_name."""
        return await asyncio.to_thread(hub.bulk_edit, rows, provenance)

    @mcp.tool()
    async def export_function(program: str, function: str) -> dict:
        """Write decompiled C, disassembly, signature and callees to an owned export directory."""
        return await asyncio.to_thread(hub.export_function, program, function)

    @mcp.tool()
    async def add_program(aex: str, name: str | None = None) -> dict:
        """Import and fully analyze an additional binary once, then persist it."""
        return await asyncio.to_thread(hub.add_program, aex, name)

    @mcp.tool()
    async def add_version(aex: str, like: str) -> dict:
        """Import/analyze a new binary and conservatively carry over knowledge from like."""
        return await asyncio.to_thread(hub.add_version, aex, like)

    @mcp.custom_route('/health', methods=['GET'])
    async def health(_: Request):
        return JSONResponse(dict(pid=os.getpid(), ready=True, programs=len(hub.programs), port=port))

    @mcp.custom_route('/api/call', methods=['POST'])
    async def call(request: Request):
        if request.headers.get('origin') or request.headers.get('host') not in {f'127.0.0.1:{port}', f'localhost:{port}'}:
            return JSONResponse({'error': 'Local non-browser clients only'}, status_code=403)
        try:
            body = await request.json()
            if body['method'] not in METHODS:
                raise ValueError('Unknown method')
            result = await asyncio.to_thread(getattr(hub, body['method']), **body.get('params', {}))
            return JSONResponse({'result': result})
        except Exception as error:
            return JSONResponse({'error': str(error)}, status_code=400)

    @mcp.custom_route('/shutdown', methods=['POST'])
    async def shutdown(request: Request):
        if request.headers.get('x-hub-token') != token:
            return JSONResponse({'error': 'Wrong instance token'}, status_code=403)
        server.should_exit = True
        return JSONResponse({'stopping': os.getpid()})

    identity = dict(pid=os.getpid(), created=psutil.Process().create_time(), port=port,
                    token=token, started=time.time())
    atomic_json(HOME/'hub.pid.json', identity)
    app = mcp.streamable_http_app()
    mcp_lifespan = app.router.lifespan_context
    @asynccontextmanager
    async def lifespan(app):
        try:
            async with mcp_lifespan(app):
                yield
        finally:
            await asyncio.to_thread(hub.close)
    app.router.lifespan_context = lifespan
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port,
                                          log_level='info', timeout_graceful_shutdown=300))
    server.run()


