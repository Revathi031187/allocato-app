# Deploy Teams Genie Bot as an Azure Databricks App

This app is set up to run on [Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/) so you can host it using your Azure Databricks workspace and credentials.

## Prerequisites

- **Azure Databricks workspace** on **Premium** tier (required for Apps).
- **Genie space** already created in the workspace.
- **Microsoft Teams bot** registered in Azure (App ID and password) for the messaging endpoint.

## 1. Create the app in Databricks

1. In your Azure Databricks workspace, go to **Compute** → **Apps** → **Create app**.
2. Choose **Custom app** (from scratch).
3. Give it a name (e.g. `teams-genie-bot`).

## 2. Provide configuration (choose one)

### Option A – Use a `.env` file in the workspace (simplest, no resources)

1. In Databricks **Workspace**, go to the folder where your app code lives (e.g. `Users/<you>/teams-genie-bot` or the path you deploy from).
2. Create a file named **`.env`** in that folder (same folder as `app.py`).
3. Put these three lines in `.env` (replace with your real values; no quotes needed):
   ```
   GENIE_SPACE_ID=<your-genie-space-id>
   MICROSOFT_APP_ID=<your-azure-bot-app-id>
   MICROSOFT_APP_PASSWORD=<your-azure-bot-client-secret>
   ```
4. Redeploy the app. The app loads these via `load_dotenv()` and no App resources are required.

**Security:** Don’t commit `.env` to Git. Add it only in the workspace. If you sync from your machine, keep `.env` in `.databricksignore` and create `.env` manually in the workspace.

### Option B – Use App resources (recommended for production)

In the app configuration, **Add resource** for:

| Resource type | Key (reference name) | Purpose |
|---------------|----------------------|---------|
| **Genie space** | `genie-space` | Provides `GENIE_SPACE_ID`. Grant **Can run**. |
| **Secret** | `microsoft-app-id` | Your Azure Bot **Application (client) ID**. |
| **Secret** | `microsoft-app-password` | Your Azure Bot **Client secret**. |

- **Where:** Your app → **Edit** / **Configure** → step where you manage **App resources** → **+ Add resource**.
- **Keys must be exactly:** `genie-space`, `microsoft-app-id`, `microsoft-app-password` (lowercase, hyphens).
- For secrets: use [Databricks secrets](https://learn.microsoft.com/en-us/azure/databricks/security/secrets/) (scope + secret key) and add each as a **Secret** resource with the key above.
- Then use the resources-based config: rename `app.yaml.with-resources` to `app.yaml` (replace the current one), commit/sync, and redeploy.

You do **not** need a `GENIE_TOKEN` when using the Genie space resource; the app uses the app’s service principal to call Genie.

## 3. Deploy from a workspace folder

1. Upload the app code into a workspace folder (e.g. `Workspace` → `Users` → `<your-email>` → `teams-genie-bot`):
   - `app.py`
   - `app.yaml`
   - `requirements.txt`

   You can use **Import** in the workspace UI or the CLI:

   ```bash
   databricks sync . /Workspace/Users/<your-email>@org.com/teams-genie-bot
   ```

2. In the app configuration, set **Source** to **Workspace folder** and choose that folder.

3. Click **Deploy**.

The platform will:

- Run `pip install -r requirements.txt`
- Run `python app.py`
- Set `DATABRICKS_APP_PORT` and `DATABRICKS_HOST` automatically; the app already uses these.

## 4. Set the Teams messaging endpoint

After the app is deployed and **Running**:

1. Open the app (click the app name). The URL will look like:
   `https://<workspace-host>/apps/<app-name>`  
   or similar (see the app details for the exact URL).

2. The Bot Framework expects a **messaging endpoint** that receives `POST /api/messages`.  
   In Azure Portal → your **Bot** resource → **Configuration**:
   - Set **Messaging endpoint** to:  
     `https://<your-databricks-apps-host>/api/messages`  
   Use the host and path that Databricks gives for your app (e.g. from the app URL or from **Networking** / **Embed** docs).  
   If your app is only reachable via a path like `/apps/teams-genie-bot`, the endpoint might be:  
   `https://<workspace>.azuredatabricks.net/apps/teams-genie-bot/api/messages`  
   (confirm the exact base URL and path in the Databricks Apps docs or from your admin.)

3. Ensure the bot’s **Microsoft App ID** and **Client secret** match the values you stored in the Databricks secrets `microsoft-app-id` and `microsoft-app-password`.

## 5. Connect the bot to Teams

- In the Azure Bot resource, open **Channels** → add **Microsoft Teams**.
- Install the bot in Teams (via the channel’s “Open in Teams” or your Teams app manifest).

## 6. Test

In Teams, open a chat with the bot and send a question about your data (e.g. “Top 5 categories by revenue”). The bot will call Genie in your workspace and reply with the answer.

## Troubleshooting

- **App won’t start**: Check **Logs** on the app details page. Typical issues: missing resources (e.g. `genie-space`, `microsoft-app-id`, `microsoft-app-password`) or wrong secret keys in `app.yaml`.
- **Teams doesn’t get a response**: Confirm the **messaging endpoint** URL is exactly what Bot Framework uses (HTTPS, correct host and path including `/api/messages`). Some Databricks Apps URLs require authentication; confirm with your admin whether the app URL is callable by Azure (e.g. allowed for webhook callbacks).
- **Genie errors**: Ensure the app’s service principal has **Can run** on the Genie space and has access to the underlying data (catalog/schema/tables) used by that space.

## Optional: Deploy from Git

You can point the app at a Git repo instead of a workspace folder. In the app configuration, add your Git repository and set the branch/tag, then deploy. Ensure the repo contains `app.py`, `app.yaml`, and `requirements.txt` at the root.
