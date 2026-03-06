import os
import time
from datetime import datetime
from pathlib import Path

import requests
from aiohttp import web
from botbuilder.core import ActivityHandler, BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity, ActivityTypes
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tabulate import tabulate

# Load .env from the same directory as this script (works when CWD differs, e.g. on Databricks Apps)
load_dotenv(Path(__file__).resolve().parent / ".env")


def _get_required_env(name: str) -> str:
    v = (os.environ.get(name) or "").strip()
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _genie_via_sdk(space_id: str, prompt: str) -> str:
    """Use Databricks SDK when running in Databricks Apps (service principal auth)."""
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        return "Genie SDK not available (install databricks-sdk)."
    w = WorkspaceClient()
    response = w.genie.start_conversation_and_wait(space_id=space_id, content=prompt)
    if not response.attachments:
        return "Genie completed but returned no attachments."
    first = response.attachments[0]
    if getattr(first, "text", None) and getattr(first.text, "content", None):
        out = (first.text.content or "").strip()
        if out:
            return out
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
                return header + f"Query result fetch failed: {e}"
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
                table = tabulate(rows, headers=[str(c).upper() for c in cols], tablefmt="fancy_grid")
                return header + f"```text\n{table}\n```"
        return header + "_No data returned._" if not header else header.rstrip()
    return "Genie returned an unsupported attachment type."


def get_genie_response(prompt: str) -> str:
    """Calls Databricks Genie (REST API or SDK) and returns markdown-friendly text."""
    space_id = _get_required_env("GENIE_SPACE_ID")

    prompt = (prompt or "").strip()
    if not prompt:
        return "Ask a question about your dataset (e.g. “Top 5 categories by revenue”)."

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
        return f"Genie API error: {start_resp.status_code} - {start_resp.text}"

    start_json = start_resp.json()
    conversation_id = (start_json.get("conversation") or {}).get("id")
    message_id = (start_json.get("message") or {}).get("id")
    if not conversation_id or not message_id:
        return f"Genie: missing conversation/message id. Raw response: {start_json}"

    # Step 2: Poll for completion
    for _ in range(100):
        poll_url = f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"
        poll_resp = session.get(poll_url, headers=headers)
        if poll_resp.status_code != 200:
            return f"Polling error: {poll_resp.status_code} - {poll_resp.text}"

        poll_json = poll_resp.json()
        if poll_json.get("status") != "COMPLETED":
            time.sleep(2)
            continue

        attachments = poll_json.get("attachments") or []
        if not attachments:
            return "Genie completed but returned no attachments."
        first = attachments[0] or {}

        # Text answer
        if "text" in first and isinstance(first["text"], dict):
            return (first["text"].get("content") or "").strip() or "Genie returned an empty text answer."

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
                return header + "Genie returned SQL but no attachment_id to fetch results."

            result_url = (
                f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"
                f"/query-result/{attachment_id}"
            )
            result_resp = session.get(result_url, headers=headers)
            if result_resp.status_code != 200:
                return header + f"Failed to retrieve query results: {result_resp.status_code} - {result_resp.text}"

            result_json = result_resp.json()
            statement_response = result_json.get("statement_response") or {}
            result_obj = (statement_response.get("result") or {})
            rows = result_obj.get("data_array") or []

            manifest = statement_response.get("manifest") or {}
            cols_info = ((manifest.get("schema") or {}).get("columns") or [])
            cols = [((c or {}).get("name") or "") for c in cols_info]

            if not cols or not rows:
                return header + "_No data returned._"

            # Teams renders code blocks fine; tabulate output is readable in monospace
            table = tabulate(rows, headers=[c.upper() for c in cols], tablefmt="fancy_grid")
            return header + f"```text\n{table}\n```"

        # Fallback: show raw attachment keys
        return f"Genie returned an unsupported attachment shape. Keys: {list(first.keys())}"

    return "Genie response not completed in time (timeout)."


class TeamsGenieBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        user_input = (turn_context.activity.text or "").strip()
        reply_text = get_genie_response(user_input)
        await turn_context.send_activity(Activity(type=ActivityTypes.message, text=reply_text))

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Hi — ask me a question and I’ll query Databricks Genie for you."
                )


MICROSOFT_APP_ID = (os.environ.get("MICROSOFT_APP_ID") or "").strip()
MICROSOFT_APP_PASSWORD = (os.environ.get("MICROSOFT_APP_PASSWORD") or "").strip()

adapter_settings = BotFrameworkAdapterSettings(MICROSOFT_APP_ID, MICROSOFT_APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)
bot = TeamsGenieBot()


async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def aux(turn_context: TurnContext):
        await bot.on_turn(turn_context)

    try:
        await adapter.process_activity(activity, auth_header, aux)
        return web.Response(status=201)
    except Exception as err:
        print(f"Bot error processing activity: {err}")
        return web.Response(status=500, text=str(err))


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/api/messages", messages)
    return app


if __name__ == "__main__":
    # Databricks Apps set DATABRICKS_APP_PORT; otherwise use PORT or default 3978
    port = int(
        (os.environ.get("DATABRICKS_APP_PORT") or os.environ.get("PORT") or "3978").strip()
    )
    web.run_app(create_app(), host="0.0.0.0", port=port)
