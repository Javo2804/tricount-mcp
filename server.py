"""Servidor MCP para Tricount: consulta y creación de movimientos."""

from __future__ import annotations

import functools
import json
import os
import sys
from datetime import date, datetime, time, timezone
from decimal import Decimal

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from tricount_client import Entry, Tricount, TricountClient, fmt, split_amount

TYPE_LABELS = {"NORMAL": "gasto", "INCOME": "ingreso", "BALANCE": "reembolso"}
CATEGORIES = {"TRAVEL", "ENTERTAINMENT", "GROCERIES", "HEALTHCARE", "INSURANCE", "RENT_AND_UTILITIES",
              "FOOD_AND_DRINK", "SHOPPING", "TRANSPORT", "OTHER", "UNCATEGORIZED"}
CONFIRM_NOTE = ("VISTA PREVIA: no se guardó nada. Muéstrale este resumen al usuario y, solo si lo "
                "confirma explícitamente, vuelve a llamar con confirm=true.")
ACTING_AS_DOC = ("acting_as: el miembro del tricount que es el usuario con quien conversas, tal como lo "
                 "confirmó tras connect_tricount. \"Yo\", \"me\" o \"conmigo\" se refieren a este miembro.")

# Guía de uso. Se entrega a cualquier cliente MCP (Claude, ChatGPT, etc.) al conectarse; las reglas
# críticas además se validan en código (acting_as obligatorio y confirm=true para escribir).
INSTRUCTIONS = """\
Servidor para consultar y editar tricounts (gastos compartidos). Sigue este flujo:

1. Tricount: si el usuario no ha dado el link de un tricount (https://tricount.com/tXXXX), pídeselo.
   No inventes ni reutilices keys de otras conversaciones.
2. Conectar: llama a connect_tricount con ese link. Muéstrale los miembros y PREGÚNTALE cuál de ellos
   es. No lo deduzcas de su nombre de cuenta, su correo ni de conversaciones anteriores: pregunta y
   espera la respuesta. Hay nombres parecidos y equivocarse carga gastos a otra persona.
3. Identidad: usa ese miembro como acting_as en toda escritura. "Yo", "me", "conmigo" = acting_as.
   Si el usuario cambia de tricount, repite los pasos 2 y 3.
4. Escribir (create_expense, create_reimbursement, delete_entry): llama primero SIN confirm; muestra
   la vista previa (monto, quién pagó, reparto, fecha) y solo si el usuario confirma explícitamente
   vuelve a llamar con confirm=true. Cada confirmación vale para un único movimiento.
5. Ambigüedad: si un nombre no calza o coincide con varios miembros, pregunta; no adivines.
6. Borrar: identifica el movimiento con list_expenses y confirma con el usuario cuál es antes de borrar.

Notas: los montos van en la moneda del tricount (CLP sin decimales). En los balances, positivo
significa que al miembro le deben y negativo que debe.
"""

server = MCPServer("tricount", instructions=INSTRUCTIONS)
_register = server.tool


def _tool():
    """Como server.tool(), pero los errores esperados (datos inválidos, respuestas de la API de
    Tricount) llegan al modelo con su mensaje; si no, el SDK solo muestra "Error executing tool"."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except (ValueError, RuntimeError, httpx.HTTPError) as exc:
                raise ToolError(str(exc)) from exc

        return _register()(wrapper)

    return decorator
client = TricountClient()


def _audit(action: str, t: Tricount, acting_as: str, **details) -> None:
    """Registro interno de escrituras. Va a stderr como JSON: Cloud Run lo lleva a Cloud Logging."""
    record = {
        "severity": "NOTICE",
        "message": f"{acting_as} {action} en '{t.title}'",
        "audit": {"action": action, "acting_as": acting_as, "tricount": t.title, "tricount_key": t.key,
                  "time": datetime.now(timezone.utc).isoformat(), **details},
    }
    print(json.dumps(record, ensure_ascii=False, default=str), file=sys.stderr, flush=True)


def _resolve(tricount: str | None) -> str:
    tricount = tricount or os.environ.get("TRICOUNT_DEFAULT")
    if not tricount:
        raise ValueError("Falta el link o key del tricount.")
    return tricount


def _match(name: str, members: list[str]) -> str:
    """Busca un miembro sin distinguir mayúsculas; acepta prefijos únicos."""
    low = name.strip().lower()
    exact = [m for m in members if m.lower() == low]
    if exact:
        return exact[0]
    partial = [m for m in members if m.lower().startswith(low) or low in m.lower()]
    if len(partial) == 1:
        return partial[0]
    raise ValueError(f"Miembro '{name}' no encontrado o ambiguo. Miembros: {', '.join(members)}")


def _entry_dict(e: Entry) -> dict:
    return {
        "id": e.id,
        "fecha": e.date.date().isoformat(),
        "descripcion": e.description,
        "tipo": TYPE_LABELS.get(e.type, e.type),
        "categoria": e.category,
        "pagado_por": e.paid_by,
        "monto": str(e.amount),
        "moneda": e.currency,
        "reparto": {a.member: str(a.amount) for a in e.allocations},
    }


@_tool()
def connect_tricount(tricount: str) -> dict:
    """Primer paso al trabajar con un tricount: valida el link y devuelve su título y miembros.
    Después pregúntale al usuario cuál de esos miembros es él o ella, y usa ese nombre como
    acting_as en las herramientas que escriben.

    Args:
        tricount: link (https://tricount.com/tXXXX) o key del tricount.
    """
    t = client.get_tricount(tricount, fresh=True)
    return {
        "titulo": t.title,
        "key": t.key,
        "moneda": t.currency,
        "miembros": t.members,
        "cantidad_movimientos": len(t.entries),
        "siguiente_paso": ("Muestra los miembros y pregúntale al usuario cuál de ellos es. No lo "
                           "deduzcas; espera su respuesta antes de crear o borrar movimientos."),
    }


@_tool()
def get_tricount_summary(tricount: str | None = None) -> dict:
    """Resumen de un tricount: título, moneda, miembros, gasto total, balances de cada
    miembro y las transferencias sugeridas para saldar las deudas.

    Args:
        tricount: link (https://tricount.com/tXXXX) o key del tricount.
    """
    t = client.get_tricount(_resolve(tricount))
    expenses = [e for e in t.entries if e.type != "BALANCE"]
    total = sum((e.amount_registry for e in expenses), Decimal(0))
    return {
        "titulo": t.title,
        "descripcion": t.description,
        "moneda": t.currency,
        "miembros": t.members,
        "cantidad_gastos": len(expenses),
        "cantidad_reembolsos": len(t.entries) - len(expenses),
        "gasto_total": str(total),
        "primer_movimiento": t.entries[0].date.date().isoformat() if t.entries else None,
        "ultimo_movimiento": t.entries[-1].date.date().isoformat() if t.entries else None,
        "balances": {m: str(v) for m, v in t.balances().items()},
        "como_saldar": t.settlement(),
    }


@_tool()
def list_expenses(
    tricount: str | None = None,
    paid_by: str | None = None,
    involving: str | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    include_reimbursements: bool = True,
    limit: int = 100,
) -> dict:
    """Lista los movimientos de un tricount (más recientes primero), con filtros opcionales.

    Args:
        tricount: link o key del tricount.
        paid_by: solo los que pagó este miembro.
        involving: solo los que incluyen a este miembro en el reparto.
        search: texto a buscar en la descripción o categoría.
        date_from: fecha mínima (YYYY-MM-DD), inclusive.
        date_to: fecha máxima (YYYY-MM-DD), inclusive.
        include_reimbursements: incluir reembolsos entre miembros.
        limit: máximo de resultados.
    """
    t = client.get_tricount(_resolve(tricount))
    entries = list(reversed(t.entries))
    if paid_by:
        who = _match(paid_by, t.members)
        entries = [e for e in entries if e.paid_by == who]
    if involving:
        who = _match(involving, t.members)
        entries = [e for e in entries if any(a.member == who for a in e.allocations)]
    if search:
        s = search.lower()
        entries = [e for e in entries if s in e.description.lower() or s in e.category.lower()]
    if date_from:
        entries = [e for e in entries if e.date.date() >= date_from]
    if date_to:
        entries = [e for e in entries if e.date.date() <= date_to]
    if not include_reimbursements:
        entries = [e for e in entries if e.type != "BALANCE"]
    total = sum((e.amount_registry for e in entries if e.type != "BALANCE"), Decimal(0))
    return {
        "titulo": t.title,
        "moneda": t.currency,
        "coincidencias": len(entries),
        "total_gastos_filtrados": str(total),
        "movimientos": [_entry_dict(e) for e in entries[:limit]],
    }


@_tool()
def get_member_detail(member: str, tricount: str | None = None) -> dict:
    """Detalle de un miembro: cuánto pagó, cuánto le corresponde, su balance,
    a quién debe o quién le debe, y sus gastos por categoría.

    Args:
        member: nombre del miembro (acepta coincidencia parcial).
        tricount: link o key del tricount.
    """
    t = client.get_tricount(_resolve(tricount))
    who = _match(member, t.members)
    expenses = [e for e in t.entries if e.type != "BALANCE"]
    paid = sum((e.amount_registry for e in expenses if e.paid_by == who), Decimal(0))
    share = Decimal(0)
    by_category: dict[str, Decimal] = {}
    for e in expenses:
        ratio = e.amount_registry / e.amount if e.amount else Decimal(1)
        for a in e.allocations:
            if a.member == who:
                part = a.amount * ratio
                share += part
                by_category[e.category] = by_category.get(e.category, Decimal(0)) + part
    reimb_sent = sum((e.amount_registry for e in t.entries if e.type == "BALANCE" and e.paid_by == who), Decimal(0))
    q = Decimal("0.01")
    return {
        "miembro": who,
        "moneda": t.currency,
        "total_pagado": str(paid.quantize(q)),
        "total_que_le_corresponde": str(share.quantize(q)),
        "reembolsos_enviados": str(reimb_sent.quantize(q)),
        "balance": str(t.balances()[who]),
        "transferencias_pendientes": [s for s in t.settlement() if who in (s["from"], s["to"])],
        "gasto_por_categoria": {k: str(v.quantize(q)) for k, v in sorted(by_category.items(), key=lambda x: -x[1])},
    }


def _entry_date(d: date | None) -> str:
    when = datetime.now() if d is None or d == date.today() else datetime.combine(d, time(12, 0))
    return when.strftime("%Y-%m-%d %H:%M:%S.%f")


def _category_fields(category: str | None) -> dict:
    if not category:
        return {}
    if category.upper() in CATEGORIES:
        return {"category": category.upper()}
    return {"category": "OTHER", "category_custom": category}


def _allocation(uuid_: str, value: Decimal, currency: str, ratio: Decimal | None = None) -> dict:
    alloc = {"membership_uuid": uuid_, "amount": {"value": fmt(value, currency), "currency": currency}}
    if ratio is not None:
        alloc |= {"type": "RATIO", "share_ratio": int(ratio) if ratio == int(ratio) else float(ratio)}
    else:
        alloc["type"] = "AMOUNT"
    return alloc


def _with_acting_as_doc(fn):
    """Las docstrings llevan {acting_as} como marcador para no repetir el texto en cada herramienta."""
    fn.__doc__ = fn.__doc__.replace("{acting_as}", ACTING_AS_DOC)
    return fn


def _save_or_preview(t: Tricount, payload: dict, preview: dict, confirm: bool, acting_as: str, action: str) -> dict:
    if not confirm:
        return {"guardado": False, "nota": CONFIRM_NOTE, "solicitado_por": acting_as, **preview}
    entry_id = client.create_entry(t, payload)
    _audit(action, t, acting_as, entry_id=entry_id, **preview)
    return {"guardado": True, "id": entry_id, "solicitado_por": acting_as, **preview}


@_tool()
@_with_acting_as_doc
def create_expense(
    acting_as: str,
    description: str,
    amount: float,
    paid_by: str,
    tricount: str | None = None,
    split_among: list[str] | None = None,
    exact_amounts: dict[str, float] | None = None,
    ratios: dict[str, float] | None = None,
    category: str | None = None,
    expense_date: date | None = None,
    confirm: bool = False,
) -> dict:
    """Crea un gasto en un tricount. Sin confirm=true solo devuelve una vista previa.

    El reparto se define con UNA de estas opciones (si no se da ninguna, se reparte en
    partes iguales entre todos los miembros):
      - split_among: lista de miembros, en partes iguales.
      - exact_amounts: monto exacto por miembro; debe sumar `amount`.
      - ratios: proporción por miembro (p. ej. {"Ana": 2, "Juan": 1}).

    Args:
        {acting_as}
        description: qué se compró.
        amount: monto total (positivo), en la moneda del tricount.
        paid_by: quién pagó ("yo" = acting_as).
        tricount: link o key del tricount.
        category: FOOD_AND_DRINK, GROCERIES, TRANSPORT, TRAVEL, ENTERTAINMENT, SHOPPING,
            RENT_AND_UTILITIES, HEALTHCARE, INSURANCE, OTHER; o un texto libre (categoría personalizada).
        expense_date: fecha del gasto (YYYY-MM-DD); por defecto hoy.
        confirm: true para guardar de verdad.
    """
    if sum(x is not None for x in (split_among, exact_amounts, ratios)) > 1:
        raise ValueError("Usa solo una de split_among, exact_amounts o ratios.")
    t = client.get_tricount(_resolve(tricount), fresh=confirm)
    me = _match(acting_as, t.members)
    cur = t.currency
    total = Decimal(str(amount))
    if total <= 0:
        raise ValueError("El monto debe ser positivo.")
    payer = _match(paid_by, t.members)

    ratio_by_member: dict[str, Decimal] = {}
    if exact_amounts:
        shares = {_match(n, t.members): Decimal(str(v)) for n, v in exact_amounts.items()}
        if sum(shares.values()) != total:
            raise ValueError(f"Los montos exactos suman {sum(shares.values())}, no {total}.")
    else:
        if ratios:
            ratio_by_member = {_match(n, t.members): Decimal(str(v)) for n, v in ratios.items()}
        else:
            names = [_match(n, t.members) for n in split_among] if split_among else list(t.members)
            ratio_by_member = {n: Decimal(1) for n in dict.fromkeys(names)}
        names = list(ratio_by_member)
        shares = dict(zip(names, split_amount(total, [ratio_by_member[n] for n in names], cur)))

    payload = {
        "description": description,
        "amount": {"value": fmt(-total, cur), "currency": cur},
        "membership_uuid_owner": t.member_uuids[payer],
        "allocations": [
            _allocation(t.member_uuids[n], -v, cur, ratio_by_member.get(n) if ratios else None)
            for n, v in shares.items()
        ],
        "type_transaction": "NORMAL",
        "date": _entry_date(expense_date),
        **_category_fields(category),
    }
    preview = {
        "tricount": t.title,
        "descripcion": description,
        "monto": fmt(total, cur),
        "moneda": cur,
        "pagado_por": payer,
        "reparto": {n: fmt(v, cur) for n, v in shares.items()},
        "fecha": payload["date"][:10],
        "categoria": category or "UNCATEGORIZED",
    }
    return _save_or_preview(t, payload, preview, confirm, me, "create_expense")


@_tool()
@_with_acting_as_doc
def create_reimbursement(
    acting_as: str,
    from_member: str,
    to_member: str,
    amount: float,
    tricount: str | None = None,
    description: str = "Reembolso",
    reimbursement_date: date | None = None,
    confirm: bool = False,
) -> dict:
    """Registra un reembolso (transferencia) de un miembro a otro. Sin confirm=true solo
    devuelve una vista previa.

    Args:
        {acting_as}
        from_member: quién paga la deuda.
        to_member: quién recibe el dinero.
        amount: monto transferido (positivo).
        tricount: link o key del tricount.
        description: texto del movimiento.
        reimbursement_date: fecha (YYYY-MM-DD); por defecto hoy.
        confirm: true para guardar de verdad.
    """
    t = client.get_tricount(_resolve(tricount), fresh=confirm)
    me = _match(acting_as, t.members)
    cur = t.currency
    total = Decimal(str(amount))
    if total <= 0:
        raise ValueError("El monto debe ser positivo.")
    payer, receiver = _match(from_member, t.members), _match(to_member, t.members)
    if payer == receiver:
        raise ValueError("Quien paga y quien recibe deben ser distintos.")
    # La app oficial guarda los reembolsos con monto negativo, igual que los gastos
    # (el API.md de elrandar/tricount-api dice positivo, pero así quedan invertidos).
    payload = {
        "description": description,
        "amount": {"value": fmt(-total, cur), "currency": cur},
        "membership_uuid_owner": t.member_uuids[payer],
        "allocations": [
            _allocation(t.member_uuids[receiver], -total, cur),
            _allocation(t.member_uuids[payer], Decimal(0), cur),
        ],
        "type_transaction": "BALANCE",
        "date": _entry_date(reimbursement_date),
    }
    preview = {
        "tricount": t.title,
        "de": payer,
        "para": receiver,
        "monto": fmt(total, cur),
        "moneda": cur,
        "fecha": payload["date"][:10],
        "balance_actual": {payer: str(t.balances()[payer]), receiver: str(t.balances()[receiver])},
    }
    return _save_or_preview(t, payload, preview, confirm, me, "create_reimbursement")


@_tool()
@_with_acting_as_doc
def delete_entry(acting_as: str, entry_id: int, tricount: str | None = None, confirm: bool = False) -> dict:
    """Elimina un movimiento (gasto, ingreso o reembolso) por su id. Sin confirm=true solo
    muestra qué se borraría. El id se obtiene con list_expenses.

    Args:
        {acting_as}
        entry_id: id del movimiento.
        tricount: link o key del tricount.
        confirm: true para borrar de verdad.
    """
    t = client.get_tricount(_resolve(tricount), fresh=True)
    me = _match(acting_as, t.members)
    entry = next((e for e in t.entries if e.id == entry_id), None)
    if entry is None:
        raise ValueError(f"No existe el movimiento {entry_id} en '{t.title}'.")
    preview = {"tricount": t.title, "movimiento": _entry_dict(entry)}
    if not confirm:
        return {"borrado": False, "nota": CONFIRM_NOTE, "solicitado_por": me, **preview}
    client.delete_entry(t, entry_id)
    _audit("delete_entry", t, me, entry_id=entry_id, movimiento=preview["movimiento"])
    return {"borrado": True, "solicitado_por": me, **preview}


def main() -> None:
    port = os.environ.get("PORT")
    if port:  # Cloud Run (o cualquier despliegue HTTP): streamable HTTP sin estado
        server.run("streamable-http", host="0.0.0.0", port=int(port), stateless_http=True, json_response=True)
    else:  # uso local: stdio
        server.run()


if __name__ == "__main__":
    main()
