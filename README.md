# LangGraph Sales Agent — a learning project

A small but complete **AI agent** built with **LangChain + LangGraph**, powered by a **Groq** LLM.
It chats with you in the terminal and can use **3 tools**:

| Tool | What it does | External service |
|---|---|---|
| `search_web` | Searches the internet for recent information | [Tavily](https://tavily.com) |
| `get_odoo_leads` | Reads CRM leads (pipeline, clients, opportunities) | [Odoo](https://www.odoo.com) XML-RPC API |
| `send_email` | Sends an email **after you approve it** | Gmail API + Google OAuth |

The goal is to be **easy to read**: every file is short and commented, and the graph is built by hand
so you can see how an agent loop really works.

---

## 1. How it works (the 2-minute version)

```
            +----------+   tool calls?   +---------+
  START --> |  agent   | ---- yes -----> |  tools  |
            |  (LLM)   | <-------------- |         |
            +----------+                 +---------+
                 | no
                 v
                END
```

1. Your message goes to the **agent node**. The LLM (Groq) sees your question and the
   **description of each tool** (taken from the tool's docstring).
2. The LLM either answers directly, or replies with a **tool call**, for example
   `get_odoo_leads(limit=3, search="Acme")`.
3. `tools_condition` routes the tool call to the **tools node** (`ToolNode`), which runs the Python function.
4. The tool's result is added to the conversation, and the graph goes **back to the agent**.
5. This loop repeats until the LLM answers without calling a tool. Then the graph goes to `END`.

Two more LangGraph ideas you will see:

- **Memory / checkpointer**: `InMemorySaver` saves the conversation per `thread_id`, so the agent
  remembers what you said earlier (until you quit).
- **Human-in-the-loop**: `send_email` calls `interrupt(...)`. The graph **pauses**, `main.py` shows you
  the email, and continues with `Command(resume="yes")` or `"no"`. The agent can never send an email
  without your approval.

---

## 2. Project structure

```
.
├── main.py                  # Terminal chat loop (+ email approval prompt)
├── agent/
│   ├── llm.py               # Groq LLM configuration
│   ├── graph.py             # The LangGraph graph + system prompt
│   └── tools/
│       ├── __init__.py      # TOOLS list: the agent's toolbox
│       ├── web_search.py    # Tool 1: Tavily web search
│       ├── odoo_crm.py      # Tool 2: Odoo CRM leads
│       └── gmail.py         # Tool 3: Gmail send (Google OAuth)
├── pyproject.toml           # Dependencies
├── uv.lock                  # Exact locked versions (reproducible install)
├── .python-version          # Python version used by uv (3.12)
├── .env.example             # Template for your API keys
└── .gitignore               # Keeps .env, credentials.json, token.json out of git
```

---

## 3. Installation

### Prerequisites

- **[uv](https://docs.astral.sh/uv/)**, the Python package manager. It also installs the right Python version for you.
  - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **git**

### Steps

```bash
git clone <this-repo-url>
cd <repo-folder>

# Installs Python 3.12 if needed, creates .venv and installs the EXACT versions from uv.lock
uv sync

# Create your own config file
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

Then fill in `.env` (see the next section) and run:

```bash
uv run main.py
```

> `uv run` automatically uses the project's `.venv`, so there is no need to activate it.
> To add a library later, run `uv add <package>`. This updates `pyproject.toml` **and** `uv.lock`; commit both.

---

## 4. Configuration: what to put in `.env`

| Variable | Required for | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | the LLM (always) | <https://console.groq.com/keys> → *Create API Key* |
| `GROQ_MODEL` | the LLM | Optional. Default `llama-3.3-70b-versatile`. Any model with **tool use** from <https://console.groq.com/docs/models> (e.g. `openai/gpt-oss-120b`) |
| `TAVILY_API_KEY` | `search_web` | <https://app.tavily.com> (free tier available) |
| `ODOO_URL` | `get_odoo_leads` | Your Odoo address, e.g. `https://mycompany.odoo.com` (no trailing `/`) |
| `ODOO_DB` | `get_odoo_leads` | Database name. On Odoo Online it is usually the subdomain (`mycompany`). Also visible at `/web/database/selector` |
| `ODOO_USER` | `get_odoo_leads` | The login (email) of the Odoo user |
| `ODOO_PASSWORD` | `get_odoo_leads` | That user's password, or better, an **API key**: Odoo → *My Profile → Account Security → New API Key* |
| `GMAIL_CREDENTIALS_FILE` | `send_email` | Path to the OAuth client file from Google Cloud (default `credentials.json`), see below |
| `GMAIL_TOKEN_FILE` | `send_email` | Where the login token is saved (default `token.json`). Created automatically |

You don't need to configure every tool to start. A tool with missing settings returns an error
message to the agent, and the agent tells you about it. The other tools keep working.

---

## 5. The tools in detail

A tool is a normal Python function with the `@tool` decorator. LangChain turns:

- the **function name** into the tool name,
- the **docstring** into the description the LLM reads to decide *when* to use the tool,
- the **type hints** (`limit: int = 5`) into a JSON schema the LLM must follow.

👉 **The docstring is a prompt.** If the agent uses a tool at the wrong moment, improve the docstring first.

### Tool 1: `search_web(query)`: [`agent/tools/web_search.py`](agent/tools/web_search.py)

- Uses `TavilySearch` from `langchain-tavily`, a search API built for LLMs (it returns clean text, not HTML).
- Returns the top 3 results: title, URL and a text snippet.
- **Use it for:** news, market prices, competitor info, anything not in the CRM.
- Example: *"Quelles sont les nouveautés d'Odoo 18 pour le CRM ?"*

### Tool 2: `get_odoo_leads(limit=5, search="")`: [`agent/tools/odoo_crm.py`](agent/tools/odoo_crm.py)

Gets CRM leads from Odoo. **Use it for:** viewing the pipeline, finding a client, checking open opportunities.

| Arg | Meaning |
|---|---|
| `limit` | Number of leads to fetch (default: 5) |
| `search` | Optional. Filters on lead name **or** client name (case-insensitive) |

How it works (Odoo's [External API](https://www.odoo.com/documentation/18.0/developer/reference/external_api.html), XML-RPC, Python standard library only):

1. `common.authenticate(db, user, password)` → returns your numeric user id (`uid`).
2. Builds a **domain** (Odoo's filter syntax), e.g. `["|", ("name","ilike","acme"), ("partner_name","ilike","acme")]`.
3. `execute_kw(..., "crm.lead", "search_read", [domain], {"fields": [...], "limit": limit})`.
4. Formats each lead on one line: name, client, email, stage, expected revenue, probability.

Requirements: the **CRM app must be installed**, and the user must have access rights to it.
The tool is **read-only**. It never changes data in Odoo.

Example: *"Montre-moi les 10 dernières opportunités"* or *"Est-ce qu'on a un lead pour Acme ?"*

### Tool 3: `send_email(to, subject, body)`: [`agent/tools/gmail.py`](agent/tools/gmail.py)

Sends a plain-text email from **your** Gmail account using the Gmail API and Google OAuth 2.0.

- Scope requested: `gmail.send` only. The app **cannot read** your inbox.
- **Human approval**: the tool calls `interrupt()` first. You see the recipient, subject and body in
  the terminal and must type `yes` to send. Anything else cancels the send.

#### One-time Google setup (about 5 minutes)

1. Go to <https://console.cloud.google.com/> and create a project (or pick an existing one).
2. **APIs & Services → Library**: search **Gmail API** and click **Enable**.
3. **APIs & Services → OAuth consent screen** (Google Auth Platform):
   - User type **External** (or *Internal* for a Google Workspace org), then fill in the app name and your email.
   - Under **Audience / Test users**, **add your own Gmail address**. While the app is in *Testing* mode, only test users can log in.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   - Application type: **Desktop app**.
   - Download the JSON file, rename it to **`credentials.json`** and put it in the project root.
5. Ask the agent to send an email. On the **first** run, a browser window opens: log in, accept the
   *"Send email on your behalf"* permission (click *Advanced → Go to app* if Google warns that the app
   is unverified, which is expected for your own test app). A `token.json` file is created, and later runs reuse it.

> ⚠️ `credentials.json` and `token.json` are **secrets** (they are in `.gitignore`). Never commit them.
> If the login stops working (e.g. "invalid_grant"), delete `token.json` and log in again.
> Note: tokens of apps in *Testing* mode expire after 7 days.

Example: *"Envoie un mail à client@example.com pour le relancer sur notre proposition"*

---

## 6. Example session

```
Assistant commercial prêt. Tape 'exit' pour quitter.

Toi > quels sont mes 3 derniers leads ?
Agent > Voici vos 3 derniers leads : ...

Toi > envoie un mail de relance au premier
--- Email à envoyer ---
À      : contact@acme.com
Objet  : Suite à notre échange
...
-----------------------
Envoyer ? (yes/no) > yes

Agent > Email envoyé à contact@acme.com.
```

---

## 7. Exercises to go further

1. **Add a 4th tool**: create `agent/tools/my_tool.py` with an `@tool` function and add it to `TOOLS` in
   `agent/tools/__init__.py`. Also mention it in `SYSTEM_PROMPT` in `graph.py`.
2. **Write to Odoo**: add a `create_odoo_lead(name, email)` tool using `execute_kw(..., "crm.lead", "create", [{...}])`.
   Should it also require human approval?
3. **Streaming**: replace `graph.invoke` with `graph.stream(..., stream_mode="updates")` in `main.py` to print each step (agent → tools → agent).
4. **Persistent memory**: replace `InMemorySaver` with `SqliteSaver` (`langgraph-checkpoint-sqlite`) so conversations survive a restart.
5. **Compare** with the one-liner `langchain.agents.create_agent(model, tools, system_prompt=...)`.
6. **Observe**: set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY=...` in `.env` to see every LLM call and tool call in [LangSmith](https://smith.langchain.com).

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `GROQ_API_KEY` / auth error | Check `.env` exists (not only `.env.example`) and the key is correct |
| `model ... does not support tool use` / model decommissioned | Change `GROQ_MODEL` to a current tool-use model from the Groq docs |
| `Erreur Odoo : authentification refusée` | Check `ODOO_DB` (exact database name), user, and password/API key |
| `Erreur Odoo : ... crm.lead ...` | The CRM app is not installed, or the user has no CRM access |
| Google: `access_denied` / "app not verified" | Add your address as a **test user** on the OAuth consent screen |
| Google: `invalid_grant` | Delete `token.json` and log in again |
| Rate limit (429) from Groq | Free-tier limits; wait a minute or switch to a smaller model |
