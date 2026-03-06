# Teams ↔ Databricks Genie Bot (Python)

This is a **standalone Microsoft Teams bot** that forwards user messages to **Databricks Genie** (Conversation REST API) and returns:
- plain text answers, or
- SQL + query results (rendered as a monospace table)

It exists because Copilot Studio publish access/licensing wasn’t available.

---

## What this project does

- **Teams user** sends a question in chat
- **Bot Framework** receives the message at `POST /api/messages`
- The bot calls Databricks Genie:
  - `POST /api/2.0/genie/spaces/{space_id}/start-conversation`
  - polls the message until `COMPLETED`
  - optionally calls `GET .../query-result/{attachment_id}` to fetch the table rows
- Bot replies to Teams with a markdown-friendly response

---

## Files

- `app.py`: Teams bot + Genie API client
- `app.yaml`: Databricks Apps runtime config (for hosting in Azure Databricks)
- `requirements.txt`: Python dependencies
- `.env.example`: environment variable template (no secrets)
- `DEPLOY_DATABRICKS_APPS.md`: Deploy as an Azure Databricks App
- `PUSH_INSTRUCTIONS.md`: Push code to GitHub and sync to Databricks workspace

---

## Setup (local run)

### 1) Create a venv and install deps

```bash
cd /d D:\teams-genie-bot
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Create `.env`

Copy `.env.example` to `.env` and fill values:

- `DATABRICKS_HOST` (workspace URL)
- `GENIE_SPACE_ID` (your Genie space id)
- `GENIE_TOKEN` (Databricks PAT with access to Genie)
- `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD` (from Azure Bot registration)

### 3) Run the bot

```bash
python app.py
```

Default port is `3978`.

---

## Azure + Teams (what to do next)

You need an Azure Bot identity so Teams can talk to your bot endpoint.

### Step A — Create/register the bot in Azure

1. Azure Portal → create an **Azure Bot** (Bot Channels Registration / Azure Bot).
2. Create or use an **App registration**.
3. Create a **client secret**.
4. Note these values:
   - `MICROSOFT_APP_ID` = Application (client) ID
   - `MICROSOFT_APP_PASSWORD` = the client secret value

### Step B — Expose your local bot to the internet (dev)

Use **ngrok** to tunnel `3978`:

```bash
ngrok http 3978
```

Copy the **https** forwarding URL, e.g. `https://xxxx.ngrok-free.app`.

In Azure Bot → **Configuration**:
- **Messaging endpoint** = `https://xxxx.ngrok-free.app/api/messages`

### Step C — Enable the Teams channel

In Azure Bot → **Channels**:
- Add/enable **Microsoft Teams**

### Step D — Test

Options:
- Use **Bot Framework Emulator** against `http://localhost:3978/api/messages` (basic test).
- Or add the bot to Teams (once Teams channel is enabled) and message it.

---

## Production deployment (recommended)

Instead of ngrok:
- Deploy this app to **Azure App Service (Web App)** or another HTTPS host.
- Set the bot’s **Messaging endpoint** to `https://<your-host>/api/messages`.
- Put all secrets in **App Service configuration** (never in code).

---

## Notes / troubleshooting

### 401 / Unauthorized from Genie

- Ensure `GENIE_TOKEN` is a valid Databricks PAT.
- Ensure the PAT has permission to use the Genie space and its SQL warehouse.

### Bot replies with “Missing required env var …”

- Your `.env` is missing a required variable; copy `.env.example` and fill it.

---

## Security

- Do **not** commit `.env` or any tokens.
- If you previously pasted tokens into chat/code, rotate them.

