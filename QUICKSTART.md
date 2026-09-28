# Quick start: use Tricount from your AI assistant (no coding needed)

**English** · [Español](QUICKSTART.es.md)

With this you can ask your AI assistant things like "who owes whom in our tricount?" or tell it
"add last night's pizza, $24, I paid, split among everyone", and it does it for you in Tricount.

It works with any assistant that supports **MCP**, the open standard for connecting tools to an
AI. For example: Claude Desktop, Claude Code, Cursor, VS Code (GitHub Copilot), Windsurf, Gemini
CLI, Codex CLI, LM Studio, Cline and others.

Setup takes about 10 minutes and you only do it once.

> This is a community project, **not an official** Tricount product. It relies on a private API
> that may change without notice.

## What you need

- **An AI assistant that supports MCP**, installed on your computer (see the list above). If
  you're not sure whether yours does, look for "MCP" in its settings or documentation.
- **Your tricount link.** In the Tricount app, open the tricount and use the share or invite
  option to copy its link. It looks like `https://tricount.com/tAbCdEf123`.

> **Using ChatGPT or another assistant in the browser?** Those can't run programs on your
> computer. See [Web assistants](#web-assistants-chatgpt-claudeai-etc) at the end.

## Shortcut: if your assistant can run commands

Some assistants, like Claude Code, Codex CLI, Gemini CLI or the agent mode in Cursor and VS Code,
can install programs for you. If you use one of them, paste this message and follow its
instructions:

```text
Install the tricount-mcp MCP server from https://github.com/Javo2804/tricount-mcp for me, following its QUICKSTART guide, and register it in this app. If you need to install anything (like uv), explain what it is and ask for my permission first.
```

When it's done, restart the app and go to [How to use it](#how-to-use-it). If it doesn't work,
follow the manual steps.

## Step 1: install uv

uv is a free tool that downloads and runs the program for you, without you having to install
Python. You install it once.

**On Windows:**

1. Press the Windows key, type **PowerShell** and open it.
2. Paste this line and press Enter:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. When it finishes, close the window.

**On Mac or Linux:**

1. Open the **Terminal** app (on Mac, search for it with Cmd + Space).
2. Paste this line and press Enter:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. When it finishes, close the window.

## Step 2: add tricount to your assistant

Every app asks for the same two things, although each stores them in a different place:

| Setting | Value |
|---|---|
| Command (`command`) | `uvx` |
| Arguments (`args`) | `tricount-mcp` |

Find your app below. Locations may change between versions; if they don't match, look for "MCP"
in your app's documentation.

### Apps with an `mcpServers` file (the most common format)

Claude Desktop, Cursor, Windsurf, Gemini CLI, LM Studio, Cline and many others use this block:

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

Where it goes, by app:

| App | Where to edit it |
|---|---|
| Claude Desktop | Settings → Developer → Edit Config (`claude_desktop_config.json`) |
| Cursor | Settings → MCP → add server (`~/.cursor/mcp.json`) |
| Windsurf | Settings → MCP (`~/.codeium/windsurf/mcp_config.json`) |
| Gemini CLI | `~/.gemini/settings.json` |
| LM Studio | Program tab → Install → Edit `mcp.json` |

`~` means your user folder. For example, `C:\Users\YOUR-USER` on Windows or `/Users/YOUR-USER` on
Mac.

**How to paste it without breaking the file:**
- **If the file is empty or only contains `{}`**, replace everything with the block above.
- **If it already has content**, don't delete it. Add `"mcpServers": { ... }` inside the outer
  braces `{ }`, separated from the rest with a comma.
- **If there's already an `"mcpServers"` entry**, add only `"tricount": { ... }` inside it,
  separated by a comma from what was already there.

Save the file.

### VS Code (GitHub Copilot)

VS Code uses `"servers"` instead of `"mcpServers"`. Open the command palette (Ctrl/Cmd + Shift +
P), choose **MCP: Open User Configuration** and add:

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

Add this at the end of `~/.codex/config.toml`:

```toml
[mcp_servers.tricount]
command = "uvx"
args = ["tricount-mcp"]
```

### Claude Code

Run this in a terminal:

```bash
claude mcp add tricount --scope user -- uvx tricount-mcp
```

### Other apps

Look for the MCP or "tool servers" section in its settings and use the command and arguments
from the table at the start of this step.

## Step 3: restart the app

Quit the app **completely** and open it again:
- **Windows:** if it has an icon next to the clock, quit it from there too (right-click → Quit).
- **Mac:** with Cmd + Q.

The first time takes a bit longer, because it downloads what it needs. To check that it worked,
look for **tricount** in your app's tools, connectors or MCP menu.

## How to use it

Write something like this to your assistant:

> Who owes whom in this tricount? https://tricount.com/tAbCdEf123

The assistant shows you the members and **asks which one is you**. Answer with your name as it
appears in the tricount. From then on you can ask things like:

- "How much have I spent in total?"
- "Show me the October expenses that Bob paid"
- "Add Groceries, $32.50, I paid, split among Alice, Carol and me"
- "Record that Alice sent me $10"
- "Delete yesterday's 'Uber' expense"

Before saving or deleting anything, the assistant shows you what it will look like and **asks for
your confirmation**. Check the amount, who paid and how it's split before saying yes.

> Some assistants ask for permission every time they use a tool. That's normal: accept it when
> the tool is from tricount.

## Tips

- **Always check the preview.** It keeps you from charging an expense to the wrong person.
- **Anyone with a tricount's link can edit it.** That's how Tricount works: only share the link
  with your group.
- **Changes show up right away in the Tricount app** for every member.
- **More capable models work better.** With small or local models the assistant may skip steps.
  That's why the important rules (identifying yourself and confirming) are also enforced by the
  server itself.

## Troubleshooting

**"tricount" doesn't show up in my assistant.**
Make sure you quit the app completely (step 3). If it still doesn't show up, check the config
file: a common mistake is a missing or extra comma. You can paste its content into the chat and
ask the assistant to check it.

**My assistant says it can't find `uvx`.**
Sometimes the app can't find uv even though it's installed. Replace `"uvx"` with its full path:
- **Windows:** `"C:\\Users\\YOUR-USER\\.local\\bin\\uvx.exe"` (replace YOUR-USER with your
  Windows user name).
- **Mac or Linux:** `"/Users/YOUR-USER/.local/bin/uvx"` (on Linux: `/home/YOUR-USER/...`).

**The first answer takes a long time.**
That's normal the first time: it's downloading what it needs. After that it's fast.

**I want to update to the latest version.**
Open PowerShell (Windows) or Terminal (Mac or Linux), run this command and restart the app:

```bash
uv cache clean tricount-mcp
```

## Web assistants (ChatGPT, claude.ai, etc.)

Assistants you use in the browser can't run programs on your computer. To use tricount-mcp from
them, someone has to publish the server on the internet and add it as a "custom connector" or
"MCP connector" in that assistant. It's a technical step: see "Deploy your own instance" in the
[README](README.md).
