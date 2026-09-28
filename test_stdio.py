"""Prueba de humo de solo lectura: levanta server.py por stdio y llama a las herramientas de lectura.

Sin argumentos usa el tricount de ejemplo público de Tricount y verifica sus balances conocidos.
Con un link, solo verifica que se pueda leer. Termina con código 1 si algo falla (lo usa el CI).
"""

import asyncio
import json
import sys
from decimal import Decimal
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

HERE = Path(__file__).parent
DEFAULT_SAMPLE = "https://tricount.com/tMjbqgwJxaikhUbkNz"
SAMPLE = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SAMPLE


async def call(s: ClientSession, name: str, **args) -> dict:
    r = await s.call_tool(name, args)
    text = r.content[0].text if r.content else ""
    print(f"\n== {name} (error={r.is_error})\n{text}")
    if r.is_error:
        raise AssertionError(f"{name} falló: {text}")
    return json.loads(text)


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], cwd=str(HERE))
    async with stdio_client(params) as (read, write), ClientSession(read, write) as s:
        init = await s.initialize()
        assert init.instructions, "el servidor no entregó instrucciones de uso"
        tools = [t.name for t in (await s.list_tools()).tools]
        print("tools:", tools)

        conn = await call(s, "connect_tricount", tricount=SAMPLE)
        summary = await call(s, "get_tricount_summary", tricount=SAMPLE)
        balances = {m: Decimal(v) for m, v in summary["balances"].items()}
        assert set(balances) == set(conn["miembros"])
        assert sum(balances.values()) == 0, f"los balances no suman cero: {balances}"

        if SAMPLE == DEFAULT_SAMPLE:  # valores conocidos del tricount de ejemplo
            assert summary["titulo"] == "City trip" and summary["gasto_total"] == "162.00", summary
            assert summary["balances"] == {"Julia": "24.75", "Alex": "45.75", "Brian": "-31.25", "Thomas": "-39.25"}
            exp = await call(s, "list_expenses", tricount=SAMPLE, paid_by="alex", limit=5)
            assert [m["descripcion"] for m in exp["movimientos"]] == ["Hotel"], exp
            member = await call(s, "get_member_detail", tricount=SAMPLE, member="Julia")
            assert member["balance"] == "24.75", member

    print("\nOK: lectura verificada")


try:
    asyncio.run(main())
except Exception as exc:  # incluye ExceptionGroup de anyio, que envuelve los AssertionError
    print(f"\nFALLÓ: {exc!r}", file=sys.stderr)
    sys.exit(1)
