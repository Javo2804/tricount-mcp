# tricount-mcp

**English** · [Español](README.es.md)

An [MCP](https://modelcontextprotocol.io) server to read and edit [Tricount](https://tricount.com)
from an AI assistant: Claude, ChatGPT or any MCP-compatible client.

Ask things like:

- "Who owes whom in this tricount? https://tricount.com/tXXXX"
- "Which expenses include Bob?"
- "Add Pizza, $24, I paid, split among everyone except Carol"
- "Record that Alice sent me $5"

> **Unofficial project.** Not affiliated with Tricount or bunq. It uses a private API that was
> reverse-engineered from the mobile app, and it may stop working without notice. Read the
> [disclaimers](#disclaimers) before using it.

## Features

| Tool | What it does |
|---|---|
| `connect_tricount` | First step: validates the link and returns the members |
| `get_tricount_summary` | Members, total spent, balances and suggested transfers to settle up |
| `list_expenses` | Transactions, filtered by who paid, who is involved, text and dates |
| `get_member_detail` | How much a person paid, their share and their spending by category |
| `create_expense` | Creates an expense: equal split, exact amounts or ratios |
| `create_reimbursement` | Records a reimbursement between two members |
| `delete_entry` | Deletes a transaction |

No Tricount account or password needed: the tricount link is enough, just like in the app.

## How it works

The server sends the assistant a usage guide when it connects, and the important rules are also
enforced in code:

1. The assistant asks for the tricount link and connects with `connect_tricount`.
2. It shows the members and **asks which one is you**. It doesn't guess: names can be similar,
   and a mistake charges expenses to someone else.
3. Creating or deleting requires `acting_as` (the member you are); names that aren't in the
   tricount are rejected.
4. **It never saves directly**: it first shows a preview and only saves once you confirm.

Amounts are split in whole currency units (pesos in CLP, cents in EUR or USD), so shares always add
up exactly to the total.

## Installation

You need **Python 3.10 or newer** and **git**.

```bash
git clone https://github.com/Javo2804/tricount-mcp.git
cd tricount-mcp
python -m venv .venv
```

Install the dependencies.

On Windows:

```bash
.venv\Scripts\python -m pip install -r requirements.txt
```

On macOS or Linux:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Check that it works with the sample tricount published by Tricount (read-only):

```bash
.venv/bin/python test_stdio.py https://tricount.com/tMjbqgwJxaikhUbkNz
```

(On Windows, use `.venv\Scripts\python` instead of `.venv/bin/python`.)

## Connect it to your assistant

In every case you need two **absolute paths**:

- **Virtual environment's Python:** `.../tricount-mcp/.venv/bin/python`, or on Windows
  `...\tricount-mcp\.venv\Scripts\python.exe`.
- **Server:** `.../tricount-mcp/server.py`.

### Claude Desktop

Go to Settings → Developer → Edit Config. This opens `claude_desktop_config.json`. Add the server:

```json
{
  "mcpServers": {
    "tricount": {
      "command": "/path/to/tricount-mcp/.venv/bin/python",
      "args": ["/path/to/tricount-mcp/server.py"]
    }
  }
}
```

On Windows, write paths with double backslashes, for example:
`"C:\\Users\\your-user\\tricount-mcp\\.venv\\Scripts\\python.exe"`.

Restart Claude Desktop and the `tricount` connector will show up among your tools.

### Claude Code

```bash
claude mcp add tricount --scope user -- /path/to/tricount-mcp/.venv/bin/python /path/to/tricount-mcp/server.py
```

### Other clients (Cursor, VS Code, Windsurf, etc.)

Any client that supports local (stdio) MCP servers works. Configure it with the same `command`
(the virtual environment's Python) and `args` (path to `server.py`) as above.

### ChatGPT and web clients

Web clients can't launch processes on your computer: they need the server published on the
internet over HTTP. See [Deploy your own instance](#deploy-your-own-instance).

## Optional settings

| Variable | Purpose |
|---|---|
| `TRICOUNT_DEFAULT` | Link or key of a tricount to use when you don't specify one |
| `TRICOUNT_USER_AGENT` | User-Agent sent to the API (see [disclaimers](#disclaimers)) |
| `PORT` | If set, the server uses HTTP at `/mcp` on that port instead of stdio |

In Claude Desktop, add variables with `"env": {"TRICOUNT_DEFAULT": "https://tricount.com/tXXXX"}`
inside the server entry.

## Deploy your own instance

To use it from ChatGPT, claude.ai or with several people, deploy it as an HTTP server:

```bash
PORT=8080 .venv/bin/python server.py
```

The MCP endpoint is `http://<host>:8080/mcp` (streamable HTTP, stateless). The repository includes
a `Dockerfile`. For example, on Google Cloud Run:

```bash
gcloud run deploy tricount-mcp --source . --project <your-project> --region <your-region> --allow-unauthenticated --max-instances 3 --memory 512Mi
```

Then add `https://<your-service>/mcp` as a custom connector in your client.

**Important:** deployed this way, the server has **no authentication**. Anyone who knows the URL
can use it, although only with tricounts whose link they have. Share the URL only with the right
people. If you need access control, add OAuth (the MCP SDK supports it) or put it behind an
authenticated proxy.

Every confirmed write emits a JSON log line on stderr with the declared member (`acting_as`), the
tricount and the transaction. On Cloud Run it goes to Cloud Logging:

```bash
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.audit.action:*" --project <your-project> --limit 20
```

## Tests

- `test_stdio.py [link]`: read test against an existing tricount.
- `test_write.py [http-url]`: creates its **own throwaway tricount**, exercises every write,
  checks the balances and deletes it at the end. Without arguments it uses stdio; with a URL
  (`http://localhost:8080/mcp`) it tests an HTTP server.

## Disclaimers

- **Unofficial API.** Tricount doesn't publish this API. It may change or be blocked at any time,
  and using it may not be allowed by their terms of service. Use it at your own risk and in
  moderation.
- **User-Agent.** The API only accepts writes from clients that identify as Tricount's Android
  app; with any other User-Agent it replies "Group Expenses is no longer available in the bunq
  app". That's why the server sends the app's User-Agent, like the projects it builds on. You can
  change it with `TRICOUNT_USER_AGENT`.
- **Anyone with the link can edit.** That's how Tricount works. The server can add expenses on
  behalf of any member. `acting_as` prevents mix-ups, but it doesn't verify identity.
- **Local session.** The server registers with the API as an anonymous device and stores that
  session in `~/.tricount-mcp/session.json`. It doesn't store your tricounts or your data.

## Technical notes

- Authentication: registers a "device" with a UUID and an RSA public key
  (`POST /v1/session-registry-installation`) and uses the token it gets back. If the token
  expires, it registers again automatically.
- Before writing, it syncs the tricount to the session (`registry-synchronization`).
- Reimbursements are stored with a **negative amount**, like the official app does. Some community
  documentation says they're positive, but that reverses them.
- Reads are cached for 60 seconds per tricount.

## Credits

Built on the research of:

- [mlaily/TricountApi](https://github.com/mlaily/TricountApi): authentication and reading.
- [elrandar/tricount-api](https://github.com/elrandar/tricount-api): write endpoints.

## License

[MIT](LICENSE)
