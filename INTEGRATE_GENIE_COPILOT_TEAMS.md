# Integrate Genie with Teams Using Copilot Studio (MCP)

This guide shows how to connect **Databricks Genie** to **Microsoft Teams chat** using **Microsoft Copilot Studio** and **Databricks Managed MCP**. Users with Copilot access can ask data questions in Teams; Copilot will use Genie via MCP to answer.

**Why this path:** If your custom bot’s Teams approval is delayed, using Copilot Studio + Genie MCP lets you get Genie in Teams sooner, using the Copilot license you already have.

---

## Easier auth: avoid the OAuth redirect headache

You can reduce or skip the full OAuth (redirect URL) setup:

| Option | OAuth / redirect | What you need | Best for |
|--------|------------------|---------------|----------|
| **Copilot Studio + maker-provided credentials** | No redirect URL if the tool supports it. You still need **Client ID + Client secret** (e.g. Service Principal). | In Copilot Studio, choose **"Maker-provided credentials"** so the bot uses one set of credentials; no per-user login. | Copilot + Genie in Teams with one shared identity. |
| **Power Automate + PAT** | **No OAuth.** | **Personal Access Token (PAT)** from Databricks (User Settings → Developer → Access tokens). HTTP action: `Authorization: Bearer <PAT>`. | Quick check or flow-based bot; no account console. |

- **Copilot (maker credentials):** When adding the Genie/MCP tool, set **"Credentials to use"** → **"Maker-provided credentials"**. You supply one Client ID + Secret; Redirect URL may not be required.
- **Power Automate (PAT):** Skip Copilot/MCP. Use a flow with HTTP action and Bearer PAT. See **"Alternative: Power Automate + PAT"** at the end of this doc.

---

## Quick steps (choose one path)

### Path A: Copilot Studio + Genie (maker-provided credentials)

| Step | What to do |
|------|------------|
| 1 | Get **Client ID** and **Client secret** from your admin (Databricks account console → Settings → App connections → create OAuth app or use Service Principal). Or create the OAuth app yourself if you have account console access. |
| 2 | Open **[Copilot Studio](https://copilotstudio.microsoft.com)** → create or open an **agent**. |
| 3 | Go to **Tools** → **Add a tool** → **Model Context Protocol (MCP)**. |
| 4 | Configure the MCP connection: **Credentials to use** → **Maker-provided credentials**. Enter **Client ID** and **Client secret**. Set **Authorization URL** and **Token URL** to your workspace (e.g. `https://<workspace-host>/oidc/v1/authorize` and `.../oidc/v1/token`). Set **Server URL** to `https://<workspace-host>/api/2.0/mcp/genie/<GENIE_SPACE_ID>`. Save. |
| 5 | If Copilot shows a **Redirect URL**, add it to the OAuth app in the Databricks account console (Redirect URLs). Otherwise skip if using maker credentials. |
| 6 | **Publish** the agent → **Channels** → add **Microsoft Teams** → **See agent in Teams** to test. |

### Path B: Power Automate + PAT (no OAuth)

| Step | What to do |
|------|------------|
| 1 | In **Databricks workspace**: click your **profile** (top right) → **User settings** → **Developer** → **Access tokens** → **Generate new token**. Copy the PAT and store it securely. |
| 2 | Open **Power Automate** ([flow.microsoft.com](https://flow.microsoft.com)) → **Create** → **Automated cloud flow**. Choose a trigger (e.g. "When a message is posted in a chat" for Teams, or "When an HTTP request is received"). |
| 3 | Add an **HTTP** action (or **Invoke an HTTP request**). Set **Method** to **POST** (or as required by the Genie API). **URI** = your Genie/Databricks API endpoint (e.g. `https://<workspace-host>/api/2.0/sql/statements` or the Genie/MCP endpoint you use). |
| 4 | In **Headers** add: **Name** = `Authorization`, **Value** = `Bearer <paste your PAT>`. Add **Content-Type** = `application/json` if needed. In **Body** add the JSON for your request (query text, etc.). |
| 5 | Add a step to parse the response and post the result back to Teams (e.g. "Post message in a chat or channel"). Save and test the flow. |
| 6 | In **Teams**, add the flow (e.g. as a Power Automate bot or trigger from a channel/chat) so users can run it. |

---

## Prerequisites

- **Copilot Studio** access (you have Copilot access for the person who will set this up).
- **Databricks workspace** with a **Genie space** and the **Genie space ID** (from the Genie UI URL: `.../rooms/<SPACE_ID>?o=...`).
- **Databricks account admin** (or someone who can create OAuth applications in the Databricks account console).
- **Power Platform / Copilot Studio** permission to create agents and add MCP tools.

---

## Step 1: Create a Databricks OAuth application

Databricks will issue tokens so Copilot Studio can call the Genie MCP server.

1. Log in to the **Databricks account console** (not the workspace):  
   `https://accounts.azuredatabricks.com/` (or your cloud’s account URL).
2. Go to **Settings** → **App connections** (or **OAuth applications** / **Service principals** depending on your UI).
3. **Create** a new OAuth / app connection:
   - **Name:** e.g. `Copilot Studio Genie MCP`
   - **Redirect URLs:** Leave blank for now. You will get a redirect URL from Copilot Studio in Step 2 and add it here later.
   - **Access / scopes:** Select **All APIs** (or the scope that allows Genie/MCP access).
   - **Generate client secret:** Yes. Copy and save the **Client ID** and **Client secret**; the secret is shown only once.
4. Click **Add** / **Create**.

**Reference:** [Databricks OAuth / enable OAuth](https://docs.databricks.com/en/administration-guide/oauth2.html) (exact path may vary by account).

### If "App connections" doesn’t show (you’re in the workspace)

**App connections** and **OAuth applications** exist only in the **Databricks account console**, not in workspace Settings. In the workspace you only see things like Identity and access, Security, User profile, etc. — no "App connections" there.

- **Try opening the account console:** In the workspace, click your **profile/avatar** (top right) → look for **"Manage account"**, **"Account settings"**, or **"Go to account console"**. That link may open the account console in a new tab.
- **Try the URL directly:** Open `https://accounts.azuredatabricks.com/` in a new tab (sometimes it works from the same browser once you’re logged in to the workspace). If your org uses a different region or domain, ask your admin for the correct account console URL.
- **Ask your Databricks account admin:** Request either (1) access to the account console so you can create an OAuth app under **Settings** → **App connections**, or (2) that they create an OAuth application for "Copilot Studio Genie MCP" and share the **Client ID** and **Client secret** with you (you’ll use these in Copilot Studio in Step 2). Without this OAuth app, the Copilot Studio ↔ Genie MCP integration cannot be completed.

**If the account console won't open:** Use the **"Request for admin"** text below to ask your admin to create the OAuth app and share Client ID and secret with you.

---

### Request for admin: create OAuth app (Copilot + Teams Genie)

If you don't have access to the Databricks account console, send this to your **Databricks account admin** (or Azure/Databricks platform owner):

**Subject:** OAuth app for Copilot Studio + Databricks Genie (Teams)

**Body:**

- We need an **OAuth application** created in the **Databricks account console** so we can connect **Microsoft Copilot Studio** to **Databricks Genie** for Teams chat.
- **Where:** Databricks **account console** (e.g. https://accounts.azuredatabricks.com/) → **Settings** → **App connections** (or **OAuth applications**) → **Create**.
- **Details to use:**
  - **Name:** `Copilot Studio Genie MCP` (or similar).
  - **Redirect URLs:** Leave empty initially. We will get a redirect URL from Copilot Studio and send it to you to add.
  - **Access / scopes:** **All APIs** (or the scope that allows Genie/MCP).
  - **Generate client secret:** Yes.
- **Please share with us (securely):** The **Client ID** and **Client secret** (secret is shown only once). We will use them in Copilot Studio to connect to Genie MCP. We will also send you the **Redirect URL** from Copilot Studio to add to this OAuth app.

Once we have the Client ID and secret, we can complete the connection in Copilot Studio and add the redirect URL for you to register.

---

## Step 2: Add the Genie MCP tool in Copilot Studio

1. Open **Microsoft Copilot Studio**: [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com).
2. Create a **new agent** (or open an existing one) that will answer data questions.
3. In the agent, go to **Tools** (or **Actions** / **Skills**) → **Add a tool**.
4. Choose **Model Context Protocol** (MCP).
5. Configure the MCP connection to Databricks:
   - **Credentials to use:** If you see **"Maker-provided credentials"** (or "Use my credentials"), select it so the bot uses one set of credentials and you may not need a Redirect URL in Databricks.
   - **Authentication:** **OAuth 2.0** → **Manual** (or **Configure** and pick manual).
   - **Client ID:** The Databricks OAuth **Client ID** from Step 1 (or Service Principal Client ID).
   - **Client Secret:** The Databricks OAuth **Client secret** from Step 1.
   - **Authorization URL:**  
     `https://<your-databricks-workspace-host>/oidc/v1/authorize`  
     Example: `https://adb-1234567890123456.7.azuredatabricks.net/oidc/v1/authorize`
   - **Token URL:**  
     `https://<your-databricks-workspace-host>/oidc/v1/token`
   - **Refresh URL** (if asked):  
     `https://<your-databricks-workspace-host>/oidc/v1/token`
   - **Scopes:** e.g. `all-apis` and `offline_access` (or as required by your Databricks OAuth setup).
6. When Copilot Studio shows a **Redirect URL**, copy it. Then in the **Databricks account console**, edit the OAuth app from Step 1 and add this URL to **Redirect URLs**. Save.
7. **Server URL** (Genie MCP):  
   `https://<your-databricks-workspace-host>/api/2.0/mcp/genie/<GENIE_SPACE_ID>`  
   Replace `<your-databricks-workspace-host>` with your workspace host (e.g. `adb-1234567890123456.7.azuredatabricks.net`) and `<GENIE_SPACE_ID>` with your Genie space ID (from the Genie UI).
8. **Server name / description:** e.g. “Genie – ask questions about our data” so Copilot knows when to use this tool.
9. **Create** / **Save** the MCP tool. If the tool list loads, you should see Genie-related tools.

**Note:** If you see “redirect URL not registered”, wait 30–60 seconds after adding the URL in Databricks and try again.

**Reference:** [Databricks managed MCP](https://docs.databricks.com/en/generative-ai/mcp/managed-mcp.html) (Genie space server).

---

## Step 3: Publish the agent and add the Teams channel

1. In Copilot Studio, **Publish** the agent (e.g. **Publish** → **Publish** or **Publish again**).
2. Open the **Channels** (or **Publish** → **Channels**) tab.
3. Select **Teams and Microsoft 365 Copilot** (or **Microsoft Teams**).
4. Optionally turn off “Make agent available in Microsoft 365 Copilot” if you only want it in Teams.
5. Click **Add channel** (or **See agent in Teams**). Follow the prompts to connect the agent to Teams.
6. When done, use **See agent in Teams** to open Teams and start a chat with the agent.

---

## Step 4: Use Genie in Teams chat

1. In **Teams**, open a chat with the Copilot agent (from **Apps** or the channel you added).
2. Ask a data question in natural language (e.g. “What are the top 5 categories by revenue?” or “Summarize sales by region”).
3. Copilot will use the Genie MCP tool to query your Genie space and reply in the same chat.

Users who have **Copilot** (or the specific Copilot Studio agent) available in Teams can use this flow without waiting for a custom bot to be approved in the Teams app catalog.

---

## Summary checklist

- [ ] Databricks OAuth app created; Client ID and Client secret saved.
- [ ] Copilot Studio agent created; MCP tool added with Databricks OAuth and Genie server URL.
- [ ] Redirect URL from Copilot Studio added to the Databricks OAuth app.
- [ ] Agent published; Teams channel added; “See agent in Teams” used to test.
- [ ] Test question asked in Teams; answer comes from Genie via Copilot.

---

## Troubleshooting

| Issue | What to do |
|--------|------------|
| “Redirect URL not registered” | Add the exact URL from Copilot Studio to the Databricks OAuth app and wait a minute before retrying. |
| Copilot doesn’t call Genie | Check the MCP server URL (workspace host + `/api/2.0/mcp/genie/<space_id>`). Ensure the agent has the Genie MCP tool and a clear description so it’s invoked for data questions. |
| No Genie tools listed | Confirm the OAuth connection works (test in Copilot Studio). Ensure the Databricks user/service has access to the Genie space. |
| Agent not in Teams | In Copilot Studio, confirm the Teams channel is added and the agent is published. In Teams, check **Apps** or the channel where the agent was added. |

For Genie or Databricks errors, check Databricks workspace logs and Unity Catalog permissions on the Genie space.

---

## Alternative: Power Automate + PAT (no OAuth)

If you want to **skip OAuth and the account console entirely**, you can use **Power Automate** with a **Personal Access Token (PAT)**.

**How it works**

- You build a **Power Automate flow** (triggered by Teams or a button) that calls the **Genie/Databricks API** with an **HTTP** action.
- **Authentication:** In the HTTP request header set:  
  `Authorization: Bearer <your_personal_access_token>`
- **No OAuth app** is required. You only need a PAT from **Databricks** → **User Settings** (profile) → **Developer** → **Access tokens** → **Generate new token**.

**Steps (high level)**

1. In **Databricks workspace**, create a PAT and copy it.
2. In **Power Automate**, create a flow (e.g. "When a Teams message is posted" or "When someone sends a message to the bot").
3. Add an **HTTP** action: method **POST** (or as required by the Genie API), URL = your Genie/MCP or REST endpoint (e.g. workspace host + path to Genie API).
4. In **Headers** add: `Authorization` = `Bearer <paste your PAT>`.
5. Body: JSON for the Genie query (depends on the API you call).
6. Add the flow to **Teams** (e.g. as an adaptive card or bot) so users can trigger it from chat.

**Trade-off**

- **Setup:** No OAuth, no account console; you only need the PAT and the API URL. Slightly more manual (you define the HTTP request and response handling).
- **Experience:** Flow-based (workflow logic) rather than a single “chat with Copilot” experience. Good for a quick integration check or a simple bot.

For a **chat-style** experience with minimal setup, the **custom bot (app.py)** in this repo also uses a PAT or token (no OAuth) and is already built for Teams.

---

### Power Automate: "Invalid connection" for Teams trigger

If the trigger **"When a new message is added to a chat or channel"** shows **"Invalid connection, please update your connection"** or **"Message type is required"**:

1. **Fix the Teams connection**
   - In the trigger box, click **"Change connection"** (or the connection name / link icon).
   - Choose **Sign in** or **Create new connection**.
   - Sign in with the **Microsoft account** that has access to the Teams tenant where the flow will run (same org as your Teams). This is a one-time OAuth to **Microsoft**, not to Databricks.
   - After signing in, the connection should show as valid and the **Message type** dropdown will load.

2. **Set Message type (threadType)**
   - In the trigger **Parameters** tab, set **Message type** (or **Choose message type**):
     - **Chat** – 1:1 and group chats only.
     - **Channel** – channel messages only.
     - Or the option that matches both if you want chat and channel.
   - In code view, this is the `threadType` parameter (e.g. `"chat"`, `"channel"`, or leave as needed per your connector version).

3. **Save the flow** and test. Once the Teams connection is valid, you can add the HTTP action with your Databricks PAT for the Genie API call.
