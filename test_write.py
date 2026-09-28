"""Prueba de escritura sobre un tricount desechable creado por el propio script.

Crea "tricount-mcp TEST" (CLP, 3 miembros ficticios), ejercita las herramientas de
escritura vía MCP/stdio, verifica balances y al final borra el tricount de prueba.
"""

import asyncio
import json
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from tricount_client import TricountClient

HERE = Path(__file__).parent


async def call(s: ClientSession, name: str, **args) -> dict:
    r = await s.call_tool(name, args)
    text = r.content[0].text if r.content else ""
    if r.is_error:
        raise AssertionError(f"{name} falló: {text}")
    return json.loads(text)


async def run(key: str) -> None:
    if len(sys.argv) > 1:  # URL de un servidor HTTP, p. ej. http://localhost:8080/mcp
        from mcp.client.streamable_http import streamable_http_client as transport
        ctx = transport(sys.argv[1])
    else:
        ctx = stdio_client(StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], cwd=str(HERE)))
    async with ctx as streams, ClientSession(streams[0], streams[1]) as s:
        await s.initialize()
        print("tools:", [t.name for t in (await s.list_tools()).tools])

        # 1. Vista previa: no debe guardar nada.
        p = await call(s, "create_expense", tricount=key, acting_as="Ana", description="Pizza", amount=10000, paid_by="ana")
        print("\npreview:", p)
        assert p["guardado"] is False and p["reparto"] == {"Ana": "3334", "Beto": "3333", "Caro": "3333"}
        assert (await call(s, "get_tricount_summary", tricount=key))["cantidad_gastos"] == 0

        # 2. Gasto en partes iguales (con resto), montos exactos y proporciones.
        g1 = await call(s, "create_expense", tricount=key, acting_as="Ana", description="Pizza", amount=10000,
                        paid_by="Ana", category="FOOD_AND_DRINK", confirm=True)
        g2 = await call(s, "create_expense", tricount=key, acting_as="Ana", description="Uber", amount=6000, paid_by="Beto",
                        exact_amounts={"Ana": 1000, "Beto": 2000, "Caro": 3000}, category="TRANSPORT", confirm=True)
        g3 = await call(s, "create_expense", tricount=key, acting_as="Ana", description="Vino", amount=9000, paid_by="Caro",
                        ratios={"Ana": 2, "Caro": 1}, category="Carrete 🍷", confirm=True)
        r1 = await call(s, "create_reimbursement", tricount=key, acting_as="Ana", from_member="Caro", to_member="Ana",
                        amount=1500, confirm=True)
        for x in (g1, g2, g3, r1):
            print("guardado:", x)

        # 3. Verificar lo que quedó en Tricount.
        summ = await call(s, "get_tricount_summary", tricount=key)
        print("\nsummary:", json.dumps(summ, ensure_ascii=False))
        # Ana: pagó 10000, parte 3334+1000+6000 = 10334, recibió 1500 -> -334 - 1500 = -1834
        # Beto: pagó 6000, parte 3333+2000 = 5333 -> +667
        # Caro: pagó 9000, parte 3333+3000+3000 = 9333, pagó reembolso 1500 -> -333 + 1500 = +1167
        assert summ["balances"] == {"Ana": "-1834.00", "Beto": "667.00", "Caro": "1167.00"}, summ["balances"]
        assert summ["cantidad_gastos"] == 3 and summ["cantidad_reembolsos"] == 1

        ex = await call(s, "list_expenses", tricount=key)
        vino = next(m for m in ex["movimientos"] if m["descripcion"] == "Vino")
        assert vino["reparto"] == {"Ana": "6000", "Caro": "3000"} and vino["categoria"] == "Carrete 🍷", vino

        # acting_as debe ser un miembro real del tricount.
        r = await s.call_tool("create_expense", {"tricount": key, "acting_as": "Zoe", "description": "x",
                                                  "amount": 1, "paid_by": "Ana"})
        assert r.is_error and "Zoe" in r.content[0].text, r
        c = await call(s, "connect_tricount", tricount=f"https://tricount.com/{key}")
        assert c["miembros"] == ["Ana", "Beto", "Caro"], c

        # 4. Borrar: vista previa y luego de verdad.
        d = await call(s, "delete_entry", tricount=key, acting_as="Ana", entry_id=g2["id"])
        assert d["borrado"] is False
        await call(s, "delete_entry", tricount=key, acting_as="Ana", entry_id=g2["id"], confirm=True)
        assert (await call(s, "get_tricount_summary", tricount=key))["cantidad_gastos"] == 2
        print("\nOK: todas las verificaciones pasaron")


def main() -> None:
    c = TricountClient()
    key = c.create_registry("tricount-mcp TEST", "CLP", ["Ana", "Beto", "Caro"])
    print("tricount de prueba:", f"https://tricount.com/{key}")
    try:
        asyncio.run(run(key))
    finally:
        c.delete_registry(c.get_tricount(key, fresh=True))
        print("tricount de prueba borrado")


if __name__ == "__main__":
    main()
