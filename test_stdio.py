"""Prueba de humo: levanta server.py por stdio y llama a cada herramienta."""

import asyncio
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

HERE = Path(__file__).parent
SAMPLE = sys.argv[1] if len(sys.argv) > 1 else "https://tricount.com/tMjbqgwJxaikhUbkNz"


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], cwd=str(HERE))
    async with stdio_client(params) as (read, write), ClientSession(read, write) as s:
        await s.initialize()
        tools = await s.list_tools()
        print("tools:", [t.name for t in tools.tools])
        for name, args in [
            ("get_tricount_summary", {"tricount": SAMPLE}),
            ("list_expenses", {"tricount": SAMPLE, "paid_by": "alex", "limit": 5}),
            ("get_member_detail", {"tricount": SAMPLE, "member": "Julia"}),
        ]:
            r = await s.call_tool(name, args)
            print(f"\n== {name} (error={r.is_error})")
            print(r.content[0].text if r.content else r)


asyncio.run(main())
