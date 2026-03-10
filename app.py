import io
import os
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests
from aiohttp import web
from botbuilder.core import ActivityHandler, BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity, ActivityTypes, Attachment
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Optional: custom credentials for single-tenant to avoid "Unable to get authority configuration"
try:
    from botframework.connector.auth import AppCredentials
except ImportError:
    AppCredentials = None

# Load .env from the same directory as this script (works when CWD differs, e.g. on Databricks Apps)
load_dotenv(Path(__file__).resolve().parent / ".env")


def _get_required_env(name: str) -> str:
    v = (os.environ.get(name) or "").strip()
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _format_markdown_table(headers: list, rows: list[list]) -> str:
    """Format headers and rows as a markdown table (like Genie / Teams)."""
    if not headers or not rows:
        return ""
    # Escape pipe in cell content so it doesn't break the table
    def cell(s):
        s = str(s).replace("|", "\\|").replace("\n", " ").strip() if s is not None else ""
        return s[:200]  # limit cell width for readability
    h = [cell(h) for h in headers]
    header_line = "| " + " | ".join(h) + " |"
    sep_line = "| " + " | ".join(["---"] * len(h)) + " |"
    body_lines = []
    for row in rows:
        cells = [cell(row[i]) if i < len(row) else "" for i in range(len(headers))]
        body_lines.append("| " + " | ".join(cells) + " |")
    return header_line + "\n" + sep_line + "\n" + "\n".join(body_lines)


def _suggest_chart_type_gemini(cols: list[str], sample_row: list) -> str:
    """Use Gemini to suggest chart type: bar, line, or pie. Returns 'bar' on error or if no key."""
    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return "bar"
    try:
        # Gemini API: generateContent with a short prompt
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        payload = {
            "contents": [{
                "parts": [{
                    "text": (
                        f"Column names: {cols}. Sample row: {sample_row}. "
                        "Reply with exactly one word: bar, line, or pie. "
                        "Use bar for categories vs values, line for time series, pie for proportions."
                    )
                }]
            }],
            "generationConfig": {"maxOutputTokens": 10}
        }
        r = requests.post(f"{url}?key={api_key}", json=payload, timeout=10)
        if r.status_code != 200:
            return "bar"
        data = r.json()
        text = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "bar") or "bar"
        word = re.search(r"\b(bar|line|pie)\b", text.lower())
        return word.group(1) if word else "bar"
    except Exception:
        return "bar"


def _generate_chart_png(cols: list[str], rows: list[list], description: str) -> bytes | None:
    """Generate a PNG chart from query result. Returns None if generation fails."""
    if len(cols) < 2 or not rows:
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    # Use first column as labels, second as values (or first numeric column as values)
    labels = []
    values = []
    for row in rows[:30]:  # limit for chart readability
        lbl = row[0] if row else ""
        try:
            val = float(row[1]) if len(row) > 1 else 0
        except (TypeError, ValueError):
            val = 0
        labels.append(str(lbl)[:30])
        values.append(val)
    if not values:
        return None
    chart_type = "bar"
    if (os.environ.get("GEMINI_API_KEY") or "").strip():
        chart_type = _suggest_chart_type_gemini(cols, rows[0] if rows else [])
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    if chart_type == "pie":
        ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
        ax.axis("equal")
    elif chart_type == "line":
        ax.plot(range(len(values)), values, marker="o")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel(cols[1] if len(cols) > 1 else "Value")
    else:
        ax.bar(range(len(values)), values, color="steelblue", edgecolor="white")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel(cols[1] if len(cols) > 1 else "Value")
    ax.set_title((description or "Result")[:80])
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# In-memory chart cache for attachment URLs: id -> (bytes, timestamp)
_chart_cache: dict[str, tuple[bytes, float]] = {}
_chart_cache_lock = threading.Lock()
_CHART_CACHE_MAX_AGE_SEC = 600


def _chart_store(png_bytes: bytes) -> str:
    """Store chart bytes and return a unique ID."""
    cid = str(uuid.uuid4())
    with _chart_cache_lock:
        now = time.time()
        # Evict old entries
        for k in list(_chart_cache):
            if now - _chart_cache[k][1] > _CHART_CACHE_MAX_AGE_SEC:
                del _chart_cache[k]
        _chart_cache[cid] = (png_bytes, now)
    return cid


def _chart_get(cid: str) -> bytes | None:
    """Retrieve chart bytes by ID; returns None if missing or expired."""
    with _chart_cache_lock:
        if cid not in _chart_cache:
            return None
        data, ts = _chart_cache[cid]
        if time.time() - ts > _CHART_CACHE_MAX_AGE_SEC:
            del _chart_cache[cid]
            return None
        return data


def _genie_via_sdk(space_id: str, prompt: str) -> dict:
    """Use Databricks SDK when running in Databricks Apps (service principal auth). Returns dict with 'text' and optional 'chart_bytes'."""
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        return {"text": "Genie SDK not available (install databricks-sdk).", "chart_bytes": None}
    w = WorkspaceClient()
    response = w.genie.start_conversation_and_wait(space_id=space_id, content=prompt)
    if not response.attachments:
        return {"text": "Genie completed but returned no attachments.", "chart_bytes": None}
    first = response.attachments[0]
    if getattr(first, "text", None) and getattr(first.text, "content", None):
        out = (first.text.content or "").strip()
        if out:
            return {"text": out, "chart_bytes": None}
    if getattr(first, "query", None):
        q = first.query
        desc = (getattr(q, "description", None) or "").strip()
        sql = (getattr(q, "query", None) or "").strip()
        att_id = (getattr(first, "attachment_id", None) or "").strip()
        header = ""
        if desc:
            header += f"{desc}\n\n"
        if sql:
            header += f"```sql\n{sql}\n```\n\n"
        if att_id:
            try:
                conv_id = getattr(response, "conversation_id", None) or getattr(response, "conversation", None)
                msg_id = getattr(response, "message_id", None) or getattr(response, "id", None)
                result = w.genie.get_message_attachment_query_result(
                    space_id=space_id,
                    conversation_id=conv_id,
                    message_id=msg_id,
                    attachment_id=att_id,
                )
            except Exception as e:
                return {"text": header + f"Query result fetch failed: {e}", "chart_bytes": None}
            stmt = getattr(result, "statement_response", None)
            res = getattr(stmt, "result", None) if stmt else None
            rows = getattr(res, "data_array", None) or []
            manifest = getattr(stmt, "manifest", None) if stmt else None
            schema = getattr(manifest, "schema", None) if manifest else None
            cols = []
            if schema:
                for c in getattr(schema, "columns", None) or []:
                    cols.append(getattr(c, "name", ""))
            if cols and rows:
                table_md = _format_markdown_table([str(c).upper() for c in cols], rows)
                chart_bytes = _generate_chart_png(cols, rows, desc)
                return {"text": header + "\n\n" + table_md, "chart_bytes": chart_bytes}
        return {"text": header + "_No data returned._" if not header else header.rstrip(), "chart_bytes": None}
    return {"text": "Genie returned an unsupported attachment type.", "chart_bytes": None}


def get_genie_response(prompt: str) -> dict:
    """Calls Databricks Genie (REST API or SDK). Returns dict with 'text' and optional 'chart_bytes'."""
    space_id = _get_required_env("GENIE_SPACE_ID")

    prompt = (prompt or "").strip()
    if not prompt:
        return {"text": "Ask a question about your dataset (e.g. \"Top 5 categories by revenue\").", "chart_bytes": None}

    print(f"[{datetime.utcnow().isoformat()}] Genie prompt: {prompt!r}")

    # In Databricks Apps use SDK when GENIE_TOKEN is not set (service principal auth)
    if os.environ.get("DATABRICKS_CLIENT_ID") and not (os.environ.get("GENIE_TOKEN") or "").strip():
        return _genie_via_sdk(space_id, prompt)

    host = _get_required_env("DATABRICKS_HOST").rstrip("/")
    token = _get_required_env("GENIE_TOKEN")

    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Step 1: Start conversation
    start_url = f"{host}/api/2.0/genie/spaces/{space_id}/start-conversation"
    start_resp = session.post(start_url, headers=headers, json={"content": prompt})
    if start_resp.status_code != 200:
        return {"text": f"Genie API error: {start_resp.status_code} - {start_resp.text}", "chart_bytes": None}

    start_json = start_resp.json()
    conversation_id = (start_json.get("conversation") or {}).get("id")
    message_id = (start_json.get("message") or {}).get("id")
    if not conversation_id or not message_id:
        return {"text": f"Genie: missing conversation/message id. Raw response: {start_json}", "chart_bytes": None}

    # Step 2: Poll for completion
    for _ in range(100):
        poll_url = f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"
        poll_resp = session.get(poll_url, headers=headers)
        if poll_resp.status_code != 200:
            return {"text": f"Polling error: {poll_resp.status_code} - {poll_resp.text}", "chart_bytes": None}

        poll_json = poll_resp.json()
        if poll_json.get("status") != "COMPLETED":
            time.sleep(2)
            continue

        attachments = poll_json.get("attachments") or []
        if not attachments:
            return {"text": "Genie completed but returned no attachments.", "chart_bytes": None}
        first = attachments[0] or {}

        # Text answer
        if "text" in first and isinstance(first["text"], dict):
            text = (first["text"].get("content") or "").strip() or "Genie returned an empty text answer."
            return {"text": text, "chart_bytes": None}

        # Query answer (SQL + result table)
        if "query" in first and isinstance(first["query"], dict):
            query_info = first["query"]
            description = (query_info.get("description") or "").strip()
            sql_stmt = (query_info.get("query") or "").strip()
            attachment_id = (first.get("attachment_id") or "").strip()

            header = ""
            if description:
                header += f"{description}\n\n"
            if sql_stmt:
                header += f"```sql\n{sql_stmt}\n```\n\n"

            if not attachment_id:
                return {"text": header + "Genie returned SQL but no attachment_id to fetch results.", "chart_bytes": None}

            result_url = (
                f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"
                f"/query-result/{attachment_id}"
            )
            result_resp = session.get(result_url, headers=headers)
            if result_resp.status_code != 200:
                return {"text": header + f"Failed to retrieve query results: {result_resp.status_code} - {result_resp.text}", "chart_bytes": None}

            result_json = result_resp.json()
            statement_response = result_json.get("statement_response") or {}
            result_obj = (statement_response.get("result") or {})
            rows = result_obj.get("data_array") or []

            manifest = statement_response.get("manifest") or {}
            cols_info = ((manifest.get("schema") or {}).get("columns") or [])
            cols = [((c or {}).get("name") or "") for c in cols_info]

            if not cols or not rows:
                return {"text": header + "_No data returned._", "chart_bytes": None}

            table_md = _format_markdown_table([c.upper() for c in cols], rows)
            chart_bytes = _generate_chart_png(cols, rows, description)
            return {"text": header + "\n\n" + table_md, "chart_bytes": chart_bytes}

        # Fallback: show raw attachment keys
        return {"text": f"Genie returned an unsupported attachment shape. Keys: {list(first.keys())}", "chart_bytes": None}

    return {"text": "Genie response not completed in time (timeout).", "chart_bytes": None}


class TeamsGenieBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        user_input = (turn_context.activity.text or "").strip()
        result = get_genie_response(user_input)
        if isinstance(result, str):
            result = {"text": result, "chart_bytes": None}
        reply_text = result.get("text") or "No response."
        chart_bytes = result.get("chart_bytes")
        attachments = []
        if chart_bytes:
            base_url = (os.environ.get("BOT_PUBLIC_URL") or "").strip().rstrip("/")
            if base_url:
                cid = _chart_store(chart_bytes)
                chart_url = f"{base_url}/api/chart/{cid}"
                attachments.append(Attachment(content_type="image/png", content_url=chart_url, name="chart.png"))
        activity = Activity(type=ActivityTypes.message, text=reply_text)
        if attachments:
            activity.attachments = attachments
        await turn_context.send_activity(activity)

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Hi — ask me a question and I’ll query Databricks Genie for you."
                )


MICROSOFT_APP_ID = (os.environ.get("MICROSOFT_APP_ID") or "").strip()
MICROSOFT_APP_PASSWORD = (os.environ.get("MICROSOFT_APP_PASSWORD") or "").strip()
# Required for single-tenant app: SDK must request token from your tenant, not "Bot Framework"
MICROSOFT_APP_TENANT_ID = (os.environ.get("MICROSOFT_APP_TENANT_ID") or "").strip()


def _make_bot_credentials():
    """Build credentials for the adapter. Uses direct tenant token URL when tenant is set to avoid authority-config errors."""
    if not MICROSOFT_APP_TENANT_ID or AppCredentials is None:
        return None
    # Custom credential that POSTs directly to tenant token endpoint (no OpenID discovery)
    token_url = f"https://login.microsoftonline.com/{MICROSOFT_APP_TENANT_ID}/oauth2/v2.0/token"
    scope = "https://api.botframework.com/.default"
    app_id = MICROSOFT_APP_ID
    app_password = MICROSOFT_APP_PASSWORD

    class _SingleTenantBotCredentials(AppCredentials):
        _lock = threading.Lock()
        _cached_token: str | None = None
        _cached_expiry: float = 0
        _TOKEN_LIFETIME_SEC = 3000  # refresh a bit before 1h

        def __init__(self):
            # Base expects (app_id, channel_auth_tenant=None, oauth_scope=None)
            super().__init__(app_id, MICROSOFT_APP_TENANT_ID, scope)

        def get_access_token(self, force_refresh: bool = False) -> str:
            with _SingleTenantBotCredentials._lock:
                now = time.time()
                if not force_refresh and _SingleTenantBotCredentials._cached_token and _SingleTenantBotCredentials._cached_expiry > now:
                    return _SingleTenantBotCredentials._cached_token
            body = (
                "grant_type=client_credentials"
                f"&client_id={quote(app_id, safe='')}"
                f"&client_secret={quote(app_password, safe='')}"
                f"&scope={quote(scope, safe='')}"
            )
            resp = requests.post(
                token_url,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            token = data["access_token"]
            expires_in = int(data.get("expires_in", 3600))
            with _SingleTenantBotCredentials._lock:
                _SingleTenantBotCredentials._cached_token = token
                _SingleTenantBotCredentials._cached_expiry = time.time() + min(expires_in, _SingleTenantBotCredentials._TOKEN_LIFETIME_SEC)
            return token

    return _SingleTenantBotCredentials()


_adapter_kw: dict = {}
if MICROSOFT_APP_TENANT_ID:
    _adapter_kw["channel_auth_tenant"] = MICROSOFT_APP_TENANT_ID
_custom_creds = _make_bot_credentials()
if _custom_creds is not None:
    _adapter_kw["app_credentials"] = _custom_creds
adapter_settings = BotFrameworkAdapterSettings(MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD, **_adapter_kw)
adapter = BotFrameworkAdapter(adapter_settings)
bot = TeamsGenieBot()


async def messages(req: web.Request) -> web.Response:
    print(f"[{datetime.utcnow().isoformat()}] Received POST /api/messages", flush=True)
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def aux(turn_context: TurnContext):
        await bot.on_turn(turn_context)

    try:
        await adapter.process_activity(activity, auth_header, aux)
        print(f"[{datetime.utcnow().isoformat()}] Reply sent successfully")
        return web.Response(status=201)
    except Exception as err:
        print(f"Bot error processing activity: {err}")
        return web.Response(status=500, text=str(err))


async def health(_req: web.Request) -> web.Response:
    """GET / for health checks and to avoid 404 when opening the root URL."""
    return web.Response(text="Bot is running. POST to /api/messages for the Teams webhook.", status=200)


async def chart_image(req: web.Request) -> web.Response:
    """GET /api/chart/<id> returns a previously stored chart PNG (for Teams attachment contentUrl)."""
    cid = req.match_info.get("id") or ""
    data = _chart_get(cid)
    if data is None:
        return web.Response(status=404, text="Chart not found or expired.")
    return web.Response(body=data, content_type="image/png")


def _cors_headers() -> dict:
    """CORS headers so Web Chat (browser) can POST to /api/messages."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS, GET",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }


@web.middleware
async def cors_middleware(request: web.Request, handler):
    """Handle CORS preflight (OPTIONS) and add CORS headers to responses."""
    if request.method == "OPTIONS":
        return web.Response(status=200, headers=_cors_headers())
    resp = await handler(request)
    for k, v in _cors_headers().items():
        resp.headers[k] = v
    return resp


@web.middleware
async def log_all_requests(request: web.Request, handler):
    """Log every request as soon as it hits the server (before auth or body parsing)."""
    print(f"[{datetime.utcnow().isoformat()}] INCOMING: {request.method} {request.path}", flush=True)
    return await handler(request)


def create_app() -> web.Application:
    app = web.Application(middlewares=[cors_middleware, log_all_requests])
    app.router.add_get("/", health)
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/api/chart/{id}", chart_image)
    return app


if __name__ == "__main__":
    import sys
    print("Starting teams-genie-bot...", flush=True)
    try:
        # Databricks Apps set DATABRICKS_APP_PORT; otherwise use PORT or default 3978
        port = int(
            (os.environ.get("DATABRICKS_APP_PORT") or os.environ.get("PORT") or "3978").strip()
        )
        print(f"Bot starting: POST /api/messages on port {port}", flush=True)
        web.run_app(create_app(), host="0.0.0.0", port=port)
    except Exception as e:
        import traceback
        print(f"Failed to start: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
