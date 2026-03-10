# Deploy Teams Genie Bot to Azure App Service

Use these steps so the Bot Framework can reach your bot. The app runs on Azure and calls Databricks Genie API.

---

## Prerequisites

- Azure subscription (same tenant as the Azure Bot is best).
- Your repo or a copy of: `app.py`, `requirements.txt`, and optionally `.env` values for reference.
- Azure Bot already created (Configuration has the correct App ID and Client secret).

---

## Step 1: Create the Web App in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com) → **Create a resource**.
2. Search for **Web App** → **Create**.
3. Fill in:
   - **Subscription:** Your (or your manager’s) subscription.
   - **Resource group:** Create new or use existing (e.g. `teams-genie-rg`).
   - **Name:** e.g. `teams-genie-bot` (must be globally unique; add numbers if needed).
   - **Publish:** **Code**.
   - **Runtime stack:** **Python 3.10** or **3.11**.
   - **Operating System:** **Linux**.
   - **Region:** Choose one close to you or your users.
   - **Pricing:** **Basic B1** (or Free F1 for testing; Free has limits).
4. Click **Review + create** → **Create**.
5. Wait for deployment, then go to the resource.

---

## Step 2: Set the startup command

Azure must run `python app.py` (your app listens on the port Azure provides).

1. In the Web App, go to **Settings** → **Configuration**.
2. Open the **Stack settings** tab (not General settings).
3. Find **Startup Command** and set it to:
   ```bash
   python app.py
   ```
4. If there is no Startup Command field, add an **Application setting** instead:
   - **Name:** `WEBSITE_STARTUP_COMMAND`
   - **Value:** `python app.py`
5. Click **Save**.

---

## Step 3: Add application settings (environment variables)

1. In the same Web App, go to **Settings** → **Configuration** → **Application settings**.
2. Click **+ New application setting** and add each of these (use your real values):

   | Name | Value | Notes |
   |------|--------|--------|
   | `DATABRICKS_HOST` | `https://<your-workspace>.azuredatabricks.com` | Your Databricks workspace URL, no trailing slash |
   | `GENIE_SPACE_ID` | Your Genie space ID | From Databricks Genie |
   | `GENIE_TOKEN` | Your Databricks PAT (personal access token) | Must have access to Genie and the space’s data |
   | `MICROSOFT_APP_ID` | Azure Bot Application (client) ID | From Azure Bot → Configuration |
   | `MICROSOFT_APP_PASSWORD` | Azure Bot **client secret value** | From App registration → Certificates & secrets. Use the **Value** (long string), **not** the Secret ID (GUID). Copy the value when you create the secret; it is shown only once. |
   | `MICROSOFT_APP_TENANT_ID` | Your Azure AD tenant ID | **Required for single-tenant.** From App registration → Overview → Directory (tenant) ID (e.g. `1f2ba1f6-02f7-4293-8c3b-c063d07e7ef9`) |
   | `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | So Azure runs `pip install` on deploy |
   | `WEBSITES_PORT` | `8000` | So Azure pings the correct port (avoids ContainerTimeout) |
   | `AZURE_REGION` | `southindia` | Set if your Web App is in South India; avoids "Region configured (None) != region detected" and can help Bot Framework routing |
   | `BOT_PUBLIC_URL` | `https://<your-web-app-name>.azurewebsites.net` | **Optional.** Required for chart image attachments in Teams (e.g. `https://teams-genie-bot-xxx.azurewebsites.net`). No trailing slash. |
   | `GEMINI_API_KEY` | Your Gemini API key | **Optional.** If set, the bot uses Gemini to suggest chart type (bar/line/pie) for query results. Get a key from Google AI Studio. |

3. Click **Save** at the top.

---

## Step 4: Deploy your code

**No GitHub write permission or identity?** Use **Option B (zip deploy)** or **Option C (VS Code)**. They do not need Deployment Center, GitHub Actions, or a managed identity.

Pick one of the options below.

### Option A: Deploy from GitHub (recommended if you have permissions)

1. In the Web App, go to **Deployment** → **Deployment center**.
2. **Source:** **GitHub** → authorize if needed → choose your repo and branch (e.g. `jaison-samuel-d/teams-genie`, `main`).
3. **Build provider:** **App Service build service** (or GitHub Actions if you prefer).
4. **Save**. Azure will build and deploy. Wait until the deployment succeeds.
5. Ensure the repo has at least `app.py` and `requirements.txt` at the **root** of the branch (or in the path you configured). The startup command runs from the repo root.

### Option B: Zip deploy from your PC (no GitHub, no identity needed)

Use this if Deployment Center asks for write permission or an identity you don’t have.

1. Install [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) and log in:
   ```bash
   az login
   ```
2. From your project folder (where `app.py` and `requirements.txt` are), create a zip with only the files Azure needs:
   ```powershell
   # Windows PowerShell (run from D:\teams-genie-bot or your repo folder):
   Compress-Archive -Path app.py, requirements.txt -DestinationPath deploy.zip -Force
   ```
3. Deploy the zip (use your Web App name and resource group):
   ```bash
   az webapp deploy --resource-group <your-resource-group> --name teams-genie-bot --src-path deploy.zip --type zip
   ```
   Example if resource group is `teams-genie-rg`:
   ```bash
   az webapp deploy --resource-group teams-genie-rg --name teams-genie-bot --src-path deploy.zip --type zip
   ```
4. Azure will unpack the zip, run `pip install -r requirements.txt` (if configured), and restart the app. No GitHub or identity is used.

### Option C: Deploy with VS Code

1. Install the **Azure App Service** extension.
2. Right-click your project folder → **Deploy to Web App**.
3. Select the subscription and the Web App you created. Deploy.

---

## Step 5: Set the Bot messaging endpoint

1. Go to **Azure Portal** → your **Azure Bot** (eams-genie) → **Configuration**.
2. Set **Messaging endpoint** to:
   ```
   https://<your-app-name>.azurewebsites.net/api/messages
   ```
   Example: if the Web App name is `teams-genie-bot`, use:
   ```
   https://teams-genie-bot.azurewebsites.net/api/messages
   ```
3. **Save**.

---

## Step 5b: Fix "Application not found in directory 'Bot Framework'" (AADSTS700016)

If you see in **Log stream**:

```text
Bot error processing activity: Failed to get access token with error: unauthorized_client, error_description: AADSTS700016: Application with identifier '...' was not found in the directory 'Bot Framework'.
```

the Bot Framework is requesting a token from the wrong Azure AD tenant. Your app is registered in **your** tenant, but the connector is using the "Bot Framework" tenant. Fix it in the **Azure Bot** resource:

1. In **Azure Portal**, open your **Azure Bot** (e.g. **databricks-genie-teams**) → **Configuration**.
2. Set **Microsoft App Type** to **Single Tenant** (not Multi Tenant).
3. Set **Microsoft App Tenant ID** to your **Azure AD tenant ID** (the tenant where the app registration for this bot lives).
   - To find it: **Microsoft Entra ID** (Azure Active Directory) → **Overview** → copy **Tenant ID**.
   - Or: open your **App registration** for this bot → **Overview** → **Directory (tenant) ID**.
4. **Save** and restart the Web App if needed.

Ensure the **App registration** (same App ID as in the Bot) is set to **Accounts in this organizational directory only** (single tenant). Also add **MICROSOFT_APP_TENANT_ID** in the Web App’s Application settings (see Step 3) so the bot code requests the token from your tenant.

---

## Step 6: Test

1. **Test in Web Chat**
   - Azure Bot → **Test in Web Chat**.
   - Send e.g. **hello** or **top 5 categories by revenue**.
   - You should get a reply (and see logs in Step 7).

2. **Check logs**
   - Web App → **Monitoring** → **Log stream**, or **Development Tools** → **Advanced Tools (Kudu)** → **Debug console** → **CMD** and tail the log files.
   - You should see lines like: `Bot starting: POST /api/messages on port ...` and `Received POST /api/messages` when you send a message.

3. **Test in Teams**
   - In the Bot, open **Channels** → **Microsoft Teams** → **Open in Teams** (or add the bot to a team/chat).
   - Send a message in Teams; the same app serves the request.

---

## Step 7: Health check

Your app only has `POST /api/messages`. Browsers and some monitors use `GET /`. To avoid 404 on the root URL, you can add a simple health route (optional). If you want, we can add a `GET /` that returns “Bot is running” so the Azure URL loads without error.

---

## Troubleshooting

| Issue | What to do |
|-------|------------|
| 500 or no reply in Web Chat | Check **Log stream** or **Logs** for the Web App; look for “Bot error” or Python tracebacks. |
| 401 Unauthorized | Ensure `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD` in App Service **exactly** match the Azure Bot (no extra spaces; use current secret). |
| AADSTS7000215 "Invalid client secret" | You used the **Secret ID** (GUID) instead of the **Secret Value**. In App registration → Certificates & secrets, use the secret’s **Value** (the long string). If you no longer have it, create a new client secret and copy its Value once. |
| AADSTS700016 "not found in the directory 'Bot Framework'" | In **Azure Bot** → **Configuration**, set **Microsoft App Type** = **Single Tenant** and **Microsoft App Tenant ID** = your Azure AD tenant ID. See **Step 5b** above. |
| “Missing required env var” | Re-check **Configuration** → **Application settings**; all five vars above must be set. |
| App doesn’t start | Confirm **Startup Command** is `python app.py` and that `app.py` and `requirements.txt` are in the deployed root. |
| Genie errors | Verify `GENIE_TOKEN` and `GENIE_SPACE_ID`; token must have access to the Genie space and its data. |

### "Site can't be reached" (browser or bot gets no response)

1. **Web App state** – In the Web App **Overview**, check **Status**. If it is **Stopped**, click **Start**.
2. **No code deployed** – If you never deployed (or deployment failed), the site has nothing to run. Deploy using **Option B (zip deploy)** in Step 4: create `deploy.zip` with `app.py` and `requirements.txt`, then run `az webapp deploy ...`.
3. **Startup or crash** – Open **Monitoring** → **Log stream**. Restart the app (**Overview** → **Restart**). In Log stream you should see Python starting and either "Bot starting..." or an error (e.g. missing module, missing env var). Fix the error shown.
4. **Wrong URL** – Confirm the Web App name in the portal. The URL must be `https://<exact-name>.azurewebsites.net/`. Check **Overview** → **Default domain** for the exact URL.
5. **Different subscription** – If the name is used in another subscription, your app may have a different URL; use **Overview** → **Default domain**.

6. **ContainerTimeout (instance Stopped)** – If **Instances** shows Status **Stopped** and Last error **ContainerTimeout** (“Container did not start within expected time limit of 230s”): (a) Add **Application setting** `WEBSITES_PORT` = `8000` so Azure pings the right port. (b) In **Instances**, click **Repair** for the instance. (c) Open **Log stream** and **Restart** the app; check for startup errors (e.g. missing env var, import error). (d) If `pip install` at startup is slow, ensure **SCM_DO_BUILD_DURING_DEPLOYMENT** = `true` and redeploy so dependencies install during deploy, not at first request.

---

## Summary checklist

- [ ] Web App created (Python 3.10/3.11, Linux).
- [ ] Startup command set to `python app.py`.
- [ ] Application settings set: `DATABRICKS_HOST`, `GENIE_SPACE_ID`, `GENIE_TOKEN`, `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD`, `SCM_DO_BUILD_DURING_DEPLOYMENT=true`.
- [ ] Code deployed (GitHub, zip, or VS Code).
- [ ] Bot **Messaging endpoint** set to `https://<your-app-name>.azurewebsites.net/api/messages`.
- [ ] Test in Web Chat and (optionally) in Teams; check Web App logs if something fails.
image.png