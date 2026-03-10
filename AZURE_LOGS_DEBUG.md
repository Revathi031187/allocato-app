# Use Azure logs to debug the bot

When the bot doesn’t reply in Web Chat or Teams, use these logs to see what’s happening.

---

## 1. Web App – Log stream (real-time)

**Where:** Azure Portal → **teams-genie-bot** (Web App) → **Monitoring** → **Log stream**.

**What to do:**

1. Open **Log stream** and select **Runtime** (not Platform).
2. Leave it open and send a message in **Test in Web Chat** (e.g. type **hi** and send).
3. Watch the log for new lines.

**What you should see (in order):**

| Log line | Meaning |
|----------|--------|
| `INCOMING: OPTIONS /api/messages` | Browser CORS preflight – normal. |
| `INCOMING: POST /api/messages` | Request reached your app. |
| `Received POST /api/messages` | Your handler got the request. |
| `Reply sent successfully` | Bot sent a reply (if you still don’t see it in chat, the issue is on the channel side). |
| `Bot error processing activity: ...` | Error in the bot (auth, Genie, etc.) – the rest of the line is the cause. |

**If you see:**

- **No new lines** when you send a message → Request is not reaching the app (wrong endpoint, firewall, or Bot not calling your URL).
- **INCOMING: POST** but no **Received POST** → Request reaches the server but fails before your handler (e.g. body parsing). Check for a traceback right after.
- **Received POST** then **Bot error** → Copy the full error line; that’s the root cause (credentials, env var, Genie, etc.).

---

## 2. Web App – Logs (query past data)

**Where:** **teams-genie-bot** → **Monitoring** → **Logs**.

**What to do:**

1. Close the Queries hub if it’s in the way.
2. In the query box, run (adjust time if needed):

```kusto
AppServiceConsoleLogs
| where TimeGenerated > ago(2h)
| order by TimeGenerated desc
| take 200
```

3. Click **Run**. Look for lines containing `INCOMING`, `Received POST`, `Reply sent`, or `Bot error`.

**If you get “table not found”:** Ensure **Application logging** is On (Web App → **Monitoring** → **App Service logs** → Application logging = **File System**) and that the app has been running and logging for a bit.

---

## 3. Bot – Activity / diagnostic logs (optional)

**Where:** **databricks-genie-teams** (Bot) → **Monitoring** or **Diagnose and solve problems** (if available).

Some Bot resources show channel activity or errors (e.g. “Bot returned an error”, “Unauthorized”). Check for any errors when you send a message.

---

## 4. Checklist from logs

1. **Log stream** open, send **hi** in Web Chat.
2. Do you see **INCOMING: POST /api/messages**?  
   - **No** → Endpoint or networking: confirm Messaging endpoint URL and Web App **Networking** (e.g. no blocking rules).
3. Do you see **Received POST /api/messages**?  
   - **No** → Request reaches the app but fails early (check for exception in the next lines).
4. Do you see **Reply sent successfully** or **Bot error**?  
   - **Bot error** → Use that message to fix (credentials, env vars, Genie).
   - **Reply sent** but no message in chat → Channel/connector issue; try different browser or Teams.

---

## 5. Quick credential check from logs

If you see **Bot error processing activity: Unauthorized** or **401**, the Web App’s **MICROSOFT_APP_ID** or **MICROSOFT_APP_PASSWORD** doesn’t match the Bot. Update them in the Web App’s **Configuration** → **Application settings**, Save, and Restart.
