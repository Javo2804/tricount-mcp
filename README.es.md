# tricount-mcp

[![CI](https://github.com/Javo2804/tricount-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Javo2804/tricount-mcp/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/tricount-mcp)](https://pypi.org/project/tricount-mcp/) [![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Javo2804/tricount-mcp/blob/main/LICENSE)

[English](README.md) · **Español**

Servidor [MCP](https://modelcontextprotocol.io) para consultar y editar
[Tricount](https://tricount.com) desde cualquier asistente de IA compatible con MCP: Claude, Cursor,
VS Code (GitHub Copilot), Windsurf, Gemini CLI, Codex CLI, LM Studio, ChatGPT (como conector
remoto) y otros.

Puedes pedirle cosas como:

- "¿Quién le debe a quién en este tricount? https://tricount.com/tXXXX"
- "¿Qué gastos incluyen a Beto?"
- "Agrega Pizza, $24.000, pagué yo, entre todos menos Caro"
- "Registra que Ana me transfirió $5.000"

> **¿No programas?** Sigue la [guía rápida](QUICKSTART.es.md): instalación paso a paso en tu
> asistente de IA, sin saber programar.

> **Proyecto no oficial.** No está afiliado a Tricount ni a bunq. Usa una API privada que se
> descubrió analizando la app móvil, y puede dejar de funcionar sin aviso. Lee los
> [avisos](#avisos) antes de usarlo.

## Qué puede hacer

| Herramienta | Qué hace |
|---|---|
| `connect_tricount` | Primer paso: valida el link y devuelve los miembros |
| `get_tricount_summary` | Miembros, gasto total, balances y transferencias sugeridas para saldar |
| `list_expenses` | Movimientos con filtros: quién pagó, a quién incluye, texto y fechas |
| `get_member_detail` | Cuánto pagó una persona, cuánto le corresponde y su gasto por categoría |
| `create_expense` | Crea un gasto: partes iguales, montos exactos o proporciones |
| `create_reimbursement` | Registra un reembolso entre dos miembros |
| `delete_entry` | Borra un movimiento |

No necesita cuenta de Tricount ni contraseña: basta con el link del tricount, igual que en la app.

## Cómo se usa

El servidor le entrega al asistente una guía de uso al conectarse, y las reglas importantes
también se validan en el código:

1. El asistente te pide el link del tricount y se conecta con `connect_tricount`.
2. Te muestra los miembros y **te pregunta cuál eres tú**. No lo adivina: hay nombres parecidos y
   equivocarse carga gastos a otra persona.
3. Para crear o borrar movimientos exige `acting_as` (el miembro que eres) y rechaza nombres que
   no estén en el tricount.
4. **Nunca guarda directo**: primero muestra una vista previa y solo guarda cuando la confirmas.

Los montos se reparten en unidades enteras de la moneda (pesos en CLP, centavos en EUR o USD), así
que las partes siempre suman exactamente el total.

## Instalación

### Instalación rápida con uv (recomendada)

Con [uv](https://docs.astral.sh/uv/) instalado no necesitas clonar nada ni instalar Python:
el cliente descarga y ejecuta el servidor desde [PyPI](https://pypi.org/project/tricount-mcp/). Todos los clientes MCP usan el
mismo comando:

```bash
uvx tricount-mcp
```

La mayoría (Claude Desktop, Cursor, Windsurf, Gemini CLI, LM Studio, Cline…) lo reciben en este
formato:

```json
{
  "mcpServers": {
    "tricount": {
      "command": "uvx",
      "args": ["tricount-mcp"]
    }
  }
}
```

La [guía rápida](QUICKSTART.es.md#paso-2-agregar-tricount-a-tu-asistente) indica dónde guarda la
configuración cada app, e incluye los formatos de VS Code, Codex CLI y Claude Code.

### Instalación manual (para modificar el código)

Necesitas **Python 3.10 o superior** y **git**.

```bash
git clone https://github.com/Javo2804/tricount-mcp.git
cd tricount-mcp
python -m venv .venv
```

Instala las dependencias.

En Windows:

```bash
.venv\Scripts\python -m pip install -r requirements.txt
```

En macOS o Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Comprueba que funciona con el tricount de ejemplo que publicó Tricount (solo lee):

```bash
.venv/bin/python test_stdio.py https://tricount.com/tMjbqgwJxaikhUbkNz
```

(En Windows, usa `.venv\Scripts\python` en lugar de `.venv/bin/python`.)

## Conectarlo a tu asistente (instalación manual)

Cualquier cliente que acepte servidores MCP locales (stdio) sirve. En vez de `uvx`, usa dos
**rutas absolutas**:

- **Comando:** el Python del entorno virtual, `.../tricount-mcp/.venv/bin/python`, o en Windows
  `...\tricount-mcp\.venv\Scripts\python.exe`.
- **Argumento:** `.../tricount-mcp/server.py`.

En el formato común `mcpServers`:

```json
{
  "mcpServers": {
    "tricount": {
      "command": "/ruta/a/tricount-mcp/.venv/bin/python",
      "args": ["/ruta/a/tricount-mcp/server.py"]
    }
  }
}
```

En Windows, escribe las rutas con doble barra invertida, por ejemplo:
`"C:\\Users\\tu-usuario\\tricount-mcp\\.venv\\Scripts\\python.exe"`. Para otros formatos (VS
Code, Codex CLI, Claude Code), mira la [guía rápida](QUICKSTART.es.md#paso-2-agregar-tricount-a-tu-asistente)
y reemplaza el comando y los argumentos. Reinicia el cliente después de cambiar su configuración.

### ChatGPT y clientes web

Los clientes web no pueden lanzar procesos en tu computador: necesitan el servidor publicado en
internet con HTTP. Ver [Desplegar tu propia instancia](#desplegar-tu-propia-instancia).

## Configuración opcional

| Variable | Para qué sirve |
|---|---|
| `TRICOUNT_DEFAULT` | Link o key de un tricount que se usa cuando no indicas ninguno |
| `TRICOUNT_USER_AGENT` | User-Agent enviado a la API (ver [avisos](#avisos)) |
| `PORT` | Si está definida, el servidor usa HTTP en `/mcp` en ese puerto en vez de stdio |

En el formato `mcpServers`, las variables se agregan con
`"env": {"TRICOUNT_DEFAULT": "https://tricount.com/tXXXX"}` dentro de la entrada del servidor.

## Desplegar tu propia instancia

Para usarlo desde ChatGPT, claude.ai o varias personas, despliégalo como servidor HTTP:

```bash
PORT=8080 .venv/bin/python server.py
```

El endpoint MCP queda en `http://<host>:8080/mcp` (streamable HTTP, sin estado). El repositorio
incluye un `Dockerfile`. Por ejemplo, en Google Cloud Run:

```bash
gcloud run deploy tricount-mcp --source . --project <tu-proyecto> --region <tu-region> --allow-unauthenticated --max-instances 3 --memory 512Mi
```

Después agrega `https://<tu-servicio>/mcp` como conector personalizado en tu cliente.

**Importante:** así desplegado, el servidor **no tiene autenticación**. Cualquiera que conozca la
URL puede usarlo, aunque solo con tricounts cuyo link tenga. Comparte la URL solo con quien
corresponda. Si necesitas control de acceso, agrega OAuth (el SDK de MCP lo soporta) o ponlo
detrás de un proxy autenticado.

Cada escritura confirmada genera una línea de registro JSON en stderr, con el miembro declarado
(`acting_as`), el tricount y el movimiento. En Cloud Run se guarda en Cloud Logging:

```bash
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.audit.action:*" --project <tu-proyecto> --limit 20
```

## Pruebas

- `test_stdio.py [link]`: prueba de lectura sobre un tricount existente.
- `test_write.py [url-http]`: crea su **propio tricount desechable**, prueba todas las escrituras,
  verifica los balances y lo borra al final. Sin argumentos usa stdio; con una URL
  (`http://localhost:8080/mcp`) prueba un servidor HTTP.

## Avisos

- **API no oficial.** Tricount no publica esta API. Puede cambiar o bloquearse en cualquier
  momento, y usarla podría no estar permitido por sus términos de servicio. Úsala bajo tu
  responsabilidad y con moderación.
- **User-Agent.** La API solo acepta escrituras de clientes que se presentan como la app Android
  de Tricount; con otro User-Agent responde "Group Expenses is no longer available in the bunq
  app". Por eso el servidor envía el mismo User-Agent que la app, igual que los proyectos en que se
  basa. Puedes cambiarlo con `TRICOUNT_USER_AGENT`.
- **Cualquiera con el link puede editar.** Así funciona Tricount. El servidor puede cargar gastos a
  nombre de cualquier miembro. `acting_as` evita equivocaciones, pero no verifica identidad.
- **Sesión local.** El servidor se registra ante la API como un dispositivo anónimo y guarda esa
  sesión en `~/.tricount-mcp/session.json`. No guarda tus tricounts ni tus datos.

## Detalles técnicos

- Autenticación: registra un "dispositivo" con un UUID y una clave RSA pública
  (`POST /v1/session-registry-installation`) y usa el token que recibe. Si el token vence, se
  registra de nuevo automáticamente.
- Para escribir, primero sincroniza el tricount con la sesión (`registry-synchronization`).
- Los reembolsos se guardan con **monto negativo**, igual que en la app oficial. Parte de la
  documentación comunitaria dice que van en positivo, pero así quedan invertidos.
- Las lecturas se guardan en caché 60 segundos por tricount.

## Créditos

Basado en la investigación de:

- [mlaily/TricountApi](https://github.com/mlaily/TricountApi): autenticación y lectura.
- [elrandar/tricount-api](https://github.com/elrandar/tricount-api): endpoints de escritura.

## Licencia

[MIT](LICENSE)
