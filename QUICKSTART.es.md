# Guía rápida: usa Tricount desde tu asistente de IA (sin saber programar)

[English](QUICKSTART.md) · **Español**

Con esto puedes preguntarle a tu asistente de IA cosas como "¿quién le debe a quién en nuestro
tricount?" o pedirle "agrega la pizza de anoche, $24.000, pagué yo, entre todos", y lo hace por ti
en Tricount.

Funciona con cualquier asistente compatible con **MCP**, el estándar abierto que permite conectar
herramientas a una IA. Por ejemplo: Claude Desktop, Claude Code, Cursor, VS Code (GitHub
Copilot), Windsurf, Gemini CLI, Codex CLI, LM Studio, Cline y otros.

La instalación toma unos 10 minutos y se hace una sola vez.

> Es un proyecto hecho por la comunidad, **no oficial** de Tricount. Funciona con una API
> privada que puede cambiar sin aviso.

## Qué necesitas

- **Un asistente de IA compatible con MCP** instalado en tu computador (ver la lista de arriba).
  Si no sabes si el tuyo lo es, busca "MCP" en su configuración o en su documentación.
- **El link de tu tricount.** En la app de Tricount, abre el tricount y usa la opción de
  compartir o invitar para copiar el link. Se ve así: `https://tricount.com/tAbCdEf123`.

> **¿Usas ChatGPT u otro asistente en el navegador?** Esos no pueden ejecutar programas en tu
> computador. Ver [Asistentes web](#asistentes-web-chatgpt-claudeai-etc) al final.

## Atajo: si tu asistente puede ejecutar comandos

Algunos asistentes, como Claude Code, Codex CLI, Gemini CLI o el modo agente de Cursor y VS Code,
pueden instalar programas por ti. Si usas uno de ellos, pégale este mensaje y sigue lo que te
pida:

```text
Instala el servidor MCP tricount-mcp de https://github.com/Javo2804/tricount-mcp para mí, siguiendo su guía QUICKSTART, y regístralo en esta app. Si necesitas instalar algo (como uv), explícame qué es y pídeme permiso antes.
```

Cuando termine, reinicia la app y pasa a [Cómo se usa](#cómo-se-usa). Si no funciona, sigue los
pasos manuales.

## Paso 1: instalar uv

uv es una herramienta gratuita que descarga y ejecuta el programa por ti, sin que tengas que
instalar Python. Se instala una vez.

**En Windows:**

1. Presiona la tecla Windows, escribe **PowerShell** y ábrelo.
2. Pega esta línea y presiona Enter:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. Cuando termine, cierra la ventana.

**En Mac o Linux:**

1. Abre la app **Terminal** (en Mac, búscala con Cmd + Espacio).
2. Pega esta línea y presiona Enter:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Cuando termine, cierra la ventana.

## Paso 2: agregar tricount a tu asistente

Todas las apps piden los mismos dos datos, aunque cada una los guarda en un lugar distinto:

| Dato | Valor |
|---|---|
| Comando (`command`) | `uvx` |
| Argumentos (`args`) | `tricount-mcp` |

Busca tu app a continuación. Las ubicaciones pueden cambiar entre versiones; si no calzan, busca
"MCP" en la documentación de tu app.

### Apps con archivo `mcpServers` (el formato más común)

Claude Desktop, Cursor, Windsurf, Gemini CLI, LM Studio, Cline y muchas otras usan este bloque:

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

Dónde va, según la app:

| App | Dónde se edita |
|---|---|
| Claude Desktop | Configuración → Desarrollador → Editar configuración (`claude_desktop_config.json`) |
| Cursor | Configuración → MCP → agregar servidor (`~/.cursor/mcp.json`) |
| Windsurf | Configuración → MCP (`~/.codeium/windsurf/mcp_config.json`) |
| Gemini CLI | `~/.gemini/settings.json` |
| LM Studio | Pestaña Program → Install → Edit `mcp.json` |

`~` significa tu carpeta de usuario. Por ejemplo, `C:\Users\TU-USUARIO` en Windows o
`/Users/TU-USUARIO` en Mac.

**Cómo pegarlo sin romper el archivo:**
- **Si el archivo está vacío o solo tiene `{}`**, reemplaza todo por el bloque de arriba.
- **Si ya tiene contenido**, no lo borres. Agrega `"mcpServers": { ... }` dentro de las llaves
  exteriores `{ }`, separado del resto con una coma.
- **Si ya existe un `"mcpServers"`**, agrega solo `"tricount": { ... }` dentro de él, separado
  con una coma de lo que ya había.

Guarda el archivo.

### VS Code (GitHub Copilot)

VS Code usa `"servers"` en vez de `"mcpServers"`. Abre la paleta de comandos (Ctrl/Cmd + Shift +
P), elige **MCP: Open User Configuration** y agrega:

```json
{
  "servers": {
    "tricount": {
      "type": "stdio",
      "command": "uvx",
      "args": ["tricount-mcp"]
    }
  }
}
```

### Codex CLI

Agrega esto al final de `~/.codex/config.toml`:

```toml
[mcp_servers.tricount]
command = "uvx"
args = ["tricount-mcp"]
```

### Claude Code

Ejecuta esto en una terminal:

```bash
claude mcp add tricount --scope user -- uvx tricount-mcp
```

### Otras apps

Busca la sección de MCP o "servidores de herramientas" en su configuración y usa el comando y
los argumentos de la tabla del comienzo de este paso.

## Paso 3: reiniciar la app

Cierra la app **por completo** y vuelve a abrirla:
- **Windows:** si tiene un ícono junto al reloj, ciérrala también desde ahí (clic derecho → Salir).
- **Mac:** con Cmd + Q.

La primera vez tarda un poco más, porque descarga lo necesario. Para comprobar que quedó bien,
busca **tricount** en el menú de herramientas, conectores o MCP de tu app.

## Cómo se usa

Escríbele a tu asistente algo como:

> ¿Quién le debe a quién en este tricount? https://tricount.com/tAbCdEf123

El asistente te mostrará los miembros y **te preguntará cuál eres tú**. Contéstale con tu nombre
tal como aparece en el tricount. Desde ahí puedes pedirle cosas como:

- "¿Cuánto he gastado yo en total?"
- "Muéstrame los gastos de octubre que pagó Beto"
- "Agrega Supermercado, $32.500, pagué yo, entre Ana, Caro y yo"
- "Registra que Ana me transfirió $10.000"
- "Borra el gasto 'Uber' de ayer"

Antes de guardar o borrar algo, el asistente te muestra cómo quedaría y **te pide confirmación**.
Revisa el monto, quién pagó y cómo se reparte antes de decir que sí.

> Algunos asistentes piden permiso cada vez que van a usar una herramienta. Es normal: acepta
> cuando la herramienta sea de tricount.

## Consejos

- **Revisa siempre la vista previa.** Así evitas cargarle un gasto a la persona equivocada.
- **Cualquiera que tenga el link de un tricount puede editarlo.** Así funciona Tricount: comparte
  el link solo con tu grupo.
- **Los cambios se ven de inmediato en la app de Tricount** para todos los miembros.
- **Los modelos más capaces funcionan mejor.** Con modelos pequeños o locales, el asistente puede
  saltarse pasos. Por eso las reglas importantes (identificarte y confirmar) también se validan en
  el propio servidor.

## Problemas frecuentes

**No aparece "tricount" en mi asistente.**
Asegúrate de haber cerrado la app por completo (paso 3). Si sigue sin aparecer, revisa el archivo
de configuración: un error típico es que falte o sobre una coma. Puedes pegar su contenido en el
chat y pedirle al asistente que lo revise.

**Mi asistente dice que no encuentra `uvx`.**
A veces la app no encuentra uv aunque esté instalado. Reemplaza `"uvx"` por su ruta completa:
- **Windows:** `"C:\\Users\\TU-USUARIO\\.local\\bin\\uvx.exe"` (cambia TU-USUARIO por tu usuario
  de Windows).
- **Mac o Linux:** `"/Users/TU-USUARIO/.local/bin/uvx"` (en Linux: `/home/TU-USUARIO/...`).

**La primera respuesta tarda mucho.**
Es normal la primera vez: está descargando lo necesario. Después es rápido.

**Quiero actualizar a la última versión.**
Abre PowerShell (Windows) o Terminal (Mac o Linux), ejecuta este comando y reinicia la app:

```bash
uv cache clean tricount-mcp
```

## Asistentes web (ChatGPT, claude.ai, etc.)

Los asistentes que se usan en el navegador no pueden ejecutar programas en tu computador. Para
usar tricount-mcp desde ellos, alguien tiene que publicar el servidor en internet y agregarlo como
"conector personalizado" o "conector MCP" en ese asistente. Es un paso técnico: ver "Desplegar tu
propia instancia" en el [README](README.es.md).
