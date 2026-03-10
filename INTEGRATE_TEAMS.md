# Integrate the Genie Bot in Microsoft Teams

Use these steps so your users can chat with the bot in Teams (1:1, group chat, or in a team channel).

---

## Prerequisites

- The bot is already working in **Test in Web Chat** (Azure Bot → Test in Web Chat).
- You have the **Azure Bot** resource (e.g. **databricks-genie-teams**) and the **Messaging endpoint** is set correctly.

---

## Step 1: Enable the Microsoft Teams channel

1. In **Azure Portal**, open your **Azure Bot** (e.g. **databricks-genie-teams**).
2. In the left menu, go to **Channels** (under **Settings** or **Bot management**).
3. You’ll see a list of channels (Web Chat, Teams, etc.).
4. Click **Microsoft Teams**.
5. Read the notice and click **Apply** (or **Agree** / **Accept**) to enable the Teams channel.
6. The **Microsoft Teams** tile should show **Enabled** (and often an **Open in Teams** link).

---

## Step 2: Use the bot in Teams (quick test)

**Option A – Open in Teams (1:1 chat)**

1. On the same **Channels** page, under **Microsoft Teams**, click **Open in Teams** (or the link shown there).
2. A browser or the Teams app will open and start a **1:1 chat** with the bot.
3. Send a message (e.g. “hi” or “top 5 categories by revenue”). You should get a reply from Genie.

**Option B – Add the bot manually in Teams**

1. Open **Microsoft Teams** (desktop or web).
2. In the left bar, click **Chat** → **New chat** (or the pencil icon).
3. In the **To:** field, type the **bot name** (e.g. **databricks-genie-teams** or the name you gave the Azure Bot).
4. Select the bot when it appears and send a message.

If the bot doesn’t appear in search, complete **Step 3** (install the app) first.

---

## Step 3: Install the bot as a Teams app (so everyone can find it)

To let others in your org use the bot, install it as a **Teams app** from the Azure Bot.

1. In **Azure Portal** → your **Azure Bot** → **Channels**.
2. Under **Microsoft Teams**, click **Open in Teams** (or use the **Install to Teams** / **Add to Teams** link if shown).
3. In the page that opens:
   - Choose **Add** (or **Add to Teams**) to add the app to your Teams.
   - You may be asked: “Add for yourself” or “Add for your team/org”. Pick the scope you want.
4. After adding, the bot will appear under **Apps** in Teams and in chat search.

**Add to a team or group chat**

1. Open the **Team** or **Group chat** where you want the bot.
2. Click **…** (More options) at the top → **Manage team** or **Add members** (wording can vary).
3. Or: in a **channel**, use **+** (Add a tab) or **Apps** → search for your bot by name → add it.
4. For **group chats**: **Chat** → **New chat** → add people → in **To:** also search and add the bot.

---

## Step 4: (Optional) Distribute via Teams Admin Center

If you want to roll the bot out to the whole organization:

1. In **Azure Portal** → **Azure Bot** → **Channels** → **Microsoft Teams**.
2. Use the option to **Download the Teams app package** (manifest + icons) if your portal shows it.  
   Or create a **Teams app manifest** that references your bot’s App ID (see [Microsoft docs](https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/deploy-and-publish/apps-upload)).
3. In **Microsoft 365 admin center** or **Teams admin center** → **Teams apps** → **Manage apps** → **Upload** (or **Submit**), upload the app package so it’s available for your tenant.
4. Admins or users can then install the app from **Apps** in Teams.

Your Azure Bot’s **Channels** page often has a direct link like **Install in Teams** that generates the app for you; use that when available.

---

## Step 5: Publish as a Teams app in Developer Portal (step-by-step)

Use this when you want to build the app in the **Teams Developer Portal** (e.g. with **public developer preview**) so it appears in Teams Apps.

---

### Complete fill-in guide for your custom bot

Use this as a single checklist: every field you need to fill in the Developer Portal, with what to enter and where to get the values.

**Where to get the App ID (use in multiple places below):**

- **Azure Portal** → your **Azure Bot** (e.g. `databricks-genie-teams`) → **Configuration** (or **Settings**) → copy **Microsoft App ID** (full GUID, e.g. `c227e509-5774-44e1-b76b-12669d5914fc`).  
- Or: **Azure Portal** → **App registrations** → your bot’s app registration → **Application (client) ID**.  
- Use this **exact same value** for: **Application (client) ID** (Basic information), **Bot ID** (App features), and anywhere the portal asks for the bot’s app ID.

---

#### 1. Basic information (left menu: **Configure** → **Basic information**)

| Field | What to fill in | Notes |
|--------|------------------|--------|
| **App name** | `Databricks Genie Assistant` (or your bot name, e.g. same as Azure Bot) | Shown in Teams app list and chat. |
| **Short description** | `Ask questions about your data in natural language. Powered by Databricks Genie.` | Max 80 characters. Shown in app card. |
| **Long description** | e.g. `Chat with your data in Microsoft Teams. Ask questions in plain English and get answers, SQL, and tables from Databricks Genie. Use for ad‑hoc analysis, reports, and dashboards.` | Max 4000 characters. |
| **Version** | `1.0.0` | Use semantic versioning (e.g. `1.0.1` when you update). |
| **Developer / Company name** | Your company or team name (e.g. `Contoso` or `Data Team`) | Shown in app details. |
| **Website (HTTPS)** | Your company or project URL. Examples: `https://www.yourcompany.com` or your Web App URL `https://<your-webapp>.azurewebsites.net` | Must be HTTPS. |
| **Privacy policy URL** | Your privacy policy page. Examples: `https://www.yourcompany.com/privacy` or `https://<your-webapp>.azurewebsites.net/privacy` | **Required.** Must be HTTPS. |
| **Terms of use URL** | Your terms of use page. Examples: `https://www.yourcompany.com/terms` or `https://<your-webapp>.azurewebsites.net/terms` | **Required.** Must be HTTPS. |
| **Application (client) ID** | Paste your **Azure Bot Microsoft App ID** (full GUID). Example: `c227e509-5774-44e1-b76b-12669d5914fc` | **Required.** Links Teams app to your existing bot. Copy from Azure Bot → Configuration. |
| **Save** | Click **Save** after filling. | |

---

#### 2. App features – Bot (left menu: **Configure** → **App features** → **Bot**)

**Where to fill bot scope and support channel features:**

| What to set | Where to fill it | What to choose |
|-------------|------------------|----------------|
| **Bot scope** (Personal / Team) | **Configure** → **App features** → open the **Bot** card. Look for **"Where people can use your bot"** or **"Scope"** (checkboxes or toggles). | **Personal** = 1:1 chat only. **Team** = bot can be added to channels. Turn **Team** on if you want the bot in channels. |
| **Supports channel features** | **Configure** → **App package editor** (or **Manifest**). In the JSON, at the **root** (same level as `manifestVersion`), add: `"supportsChannelFeatures": "tier1"`. Or, if the portal has a **"Supports channel features"** / **"Channel features"** dropdown under **App features** or **Bot**, set it to **tier1**. | Required when **Team** scope is enabled (manifest 1.25+). Value: **tier1**. |

| Field | What to fill in | Notes |
|--------|------------------|--------|
| **Add a bot** / **Bot** | Choose **Add** or **New bot** (if “Use existing bot” isn’t available, use “New” and set Bot ID below). | |
| **Bot ID** | **Same** Microsoft App ID as in Basic information (your Azure Bot’s App ID). Example: `c227e509-5774-44e1-b76b-12669d5914fc` | Must match Azure Bot. |
| **Bot name** | Same as **App name** or short name, e.g. `Genie Assistant` | Shown in chat. |
| **Bot command list** (optional) | e.g. `query` or `ask` – so users can type `/query what are top 5 products`. Leave empty if you don’t need slash commands. | Optional. |
| **Where people can use your bot** | **Personal** = 1:1 chat. **Team** = in channels. Enable both if you want 1:1 and channels. | If you enable **Team**, you must set **supportsChannelFeatures** in Manifest (section 4). |
| **Scope** | Usually **Personal** and/or **Team** (as above). | |
| **Capabilities** | For a chat-only Genie bot: leave **Read and download files**, **Notification**, **Audio/Video calls** **unchecked** unless you need them. | Reduces consent prompts. |
| **Save** | Click **Save**. | |

---

#### 3. Distribution / Developer preview (left menu: **Configure** → **Distribution** or **Publish**)

| Field | What to fill in | Notes |
|--------|------------------|--------|
| **Public developer preview** | Turn **On** | So you (and others with developer preview) can install without store submission. |
| **Make available in developer preview** | **On** | Same as above (wording may vary). |
| **Save** | Click **Save**. | |
| **Publish** / **Distribute** | Choose **Publish to org (preview)** or **Distribute** → **Developer preview** | Makes the app installable in Teams for preview users. |

**In Teams (each user):** **Settings** → **General** → **Developer preview** → **On**, so the app appears in **Apps**.

---

#### 4. Manifest – supportsChannelFeatures (if bot is used in **Team** / channels)

| Where | What to do | Notes |
|--------|------------|--------|
| **Manifest** (left menu: **Configure** → **Manifest** or **Export**) | If you use **Team** scope and manifest version **1.25+**, add at the **root** of the JSON: `"supportsChannelFeatures": "tier1"` | Required to avoid “must include the 'supportsChannelFeatures' property”. |
| **Edit manifest** / **Download** | Download manifest → add the line above (e.g. after `"manifestVersion": "1.25"`) → **Save** or **Upload** | See **teams-manifest-snippet.json** in the repo. |
| **Supports channel features** (if the portal has a toggle) | Set to **tier1** | Same as above. |

---

#### 5. Icons and color (optional but recommended)

| Field | What to fill in | Notes |
|--------|------------------|--------|
| **Outline icon** | Upload a 32×32 px PNG (transparent background). | Shown in Teams app list. |
| **Color icon** | Upload a 192×192 px PNG. | App tile in Teams. |
| **Accent color** | Hex color, e.g. `#6264A7` (Teams default) or your brand color. | Theme for your app. |

If you don’t upload icons, the portal may use defaults.

---

#### 6. Final save and test

| Step | Action |
|--------|--------|
| **Save** | Click **Save** at the top (or in each section) so nothing is lost. |
| **Publish** | **Distribution** / **Publish** → **Publish to org (preview)** or **Developer preview**. |
| **Preview in Teams** | In the portal, use **Preview in Teams** or **See in Teams** to open Teams and install the app. |
| **Install in Teams** | Or: Teams → **Apps** → search for your **App name** → **Add** / **Install**. |
| **Chat** | Open the bot (1:1 or in a channel) and send a message; the bot should reply via your Web App. |

---

### Step-by-step (short version)

### 5.1 Open the Developer Portal

1. Go to **[Teams Developer Portal](https://dev.teams.microsoft.com/)**.
2. Sign in with the same Microsoft 365 account as your Azure Bot tenant.
3. **Create new app** or **Apps** → **New app** → **Create**.

### 5.2 Basic information

1. Left menu → **Basic information** (or **Configure** → **Basic information**).
2. Fill every field as in the **Complete fill-in guide** table above (App name, Short/Long description, Version, Developer, Website, Privacy policy URL, Terms of use URL, **Application (client) ID** = Azure Bot App ID).
3. Click **Save**.

### 5.3 Configure the bot

1. Left menu → **Configure** → **App features** (or **Bot** / **Capabilities**).
2. **Bot:** **New bot** (if needed); **Bot ID** = same Microsoft App ID as in 5.2.
3. **Where people can use your bot:** **Personal** and/or **Team**.
4. **Capabilities:** leave extra ones unchecked for chat-only.
5. **Save**.

### 5.4 Use public developer preview

1. **Distribution** or **Publish** → **Public developer preview** (or **Make available in developer preview**) → **On**.
2. **Save**. Then **Publish to org (preview)** or **Distribute** → **Developer preview**.

### 5.5 Manifest and supportsChannelFeatures (required if team scope)

1. If **Team** scope is enabled and manifest is 1.25+: open **Manifest**, add `"supportsChannelFeatures": "tier1"` at root of JSON (see **teams-manifest-snippet.json**).
2. Save or upload the manifest.

### 5.6 Save and distribute

1. **Save** everywhere, then **Publish** (developer preview).
2. **Preview in Teams** or Teams → **Apps** → install your app → chat with the bot.

### 5.7 Quick checklist

- [ ] Basic information filled (all fields including **Application (client) ID** = Azure Bot App ID).
- [ ] Bot configured with same **Bot ID**; **Personal** and/or **Team**; capabilities as needed.
- [ ] **Public developer preview** On; published to developer preview.
- [ ] If team scope: **supportsChannelFeatures** = `tier1` in manifest.
- [ ] Tested in Teams (install app → chat with bot).

---

## Summary checklist

- [ ] **Channels** → **Microsoft Teams** → **Apply** so the channel is **Enabled**.
- [ ] Click **Open in Teams** and send a test message (1:1).
- [ ] **Add** / **Install** the bot in Teams (for yourself or your team) so it appears in **Apps** and chat search.
- [ ] (Optional) Upload the app via **Teams admin center** for org-wide use.

---

## Troubleshooting

| Issue | What to do |
|--------|------------|
| Bot doesn’t appear in Teams search | Install the app first (Step 3). Ensure you’re in the same tenant as the Azure Bot / App registration. |
| “Open in Teams” opens but bot doesn’t reply | Check **Web App** → **Log stream** when you send a message. If you see `Reply sent successfully`, the problem is on the Teams side (e.g. cache; try another client). |
| Bot works in Web Chat but not in Teams | Confirm the **Microsoft Teams** channel is **Enabled** and the **Messaging endpoint** is correct. Restart the Web App and try again. |
| Need to add bot to a channel | In the channel, use **+** (Add a tab) or **Apps** → find your bot → add. Or add the bot to the team and @mention it in the channel. |
| "must include the 'supportsChannelFeatures' property" (manifest 1.25+, team scope) | Add `"supportsChannelFeatures": "tier1"` to the **root** of your app manifest. In Teams Developer Portal: open your app → **Manifest** or **App features** / **Configure** → if there’s an option to edit the manifest or **Download** it, add this property and **Save** or re-upload. See **teams-manifest-snippet.json** in the repo. |

| App and bot don't show in Teams (search / Apps) | See **"When the app and bot don't show in Teams"** below. |
| **"You cannot send messages to this bot"** | The bot appears but the message box is disabled. See **"Fix: You cannot send messages to this bot"** below. |

### Fix: "You cannot send messages to this bot"

If the Genie Data Assistant (or your bot) opens in Teams but the input shows **"You cannot send messages to this bot"** and you can't type:

1. **Check the app manifest – `isNotificationOnly`**  
   The bot must **not** be notification-only. In the app manifest (Developer Portal or your package), under `bots` ensure:  
   `"isNotificationOnly": false`  
   If it is `true`, Teams treats the bot as send-only and blocks user messages. Update the manifest to `false`, re-package/re-upload the app, and re-install in Teams.

2. **Ensure "Personal" scope is enabled**  
   The app must allow 1:1 chat. In Developer Portal → **App features** → **Bot** → **Where people can use your bot**, enable **Personal** (and **Team** / **Group chat** if needed). Save and update the app.

3. **Reinstall the app**  
   In Teams: **Apps** → find your app → **Remove** (or right-click → Uninstall). Then **Add** / **Install** again and open a new 1:1 chat with the bot. Sometimes an old cached manifest keeps the restriction.

4. **Org or app policy**  
   Your tenant may restrict which bots users can message. Ask your **Teams admin** if there is a policy blocking conversation with this app. They may need to allow the app in **Teams admin center** → **Manage apps** or **Permission policies**.

5. **Use the correct app**  
   If you have more than one app (e.g. one from Developer Portal with a different manifest), make sure you're opening the one that has `isNotificationOnly: false` and **Personal** scope. The **direct chat link** (e.g. `https://teams.microsoft.com/l/chat/0/0?users=28:<BOT_APP_ID>`) should open a chat with the Azure Bot; if that link also shows "You cannot send messages", the issue is manifest or tenant policy.

### When the app and bot don't show in Teams

If **New chat** search and **Apps** → search both don't show your bot or app, try these in order.

**1. Open 1:1 chat via direct link (no search needed)**

Use this URL in your browser (replace the GUID with your Azure Bot's **Microsoft App ID**). It should open Teams and start a 1:1 chat with the bot:

```
https://teams.microsoft.com/l/chat/0/0?users=28:c227e509-5774-44e1-b76b-12669d5914fc
```

- If your bot's App ID is different, change the part after `28:` to your App ID (no spaces).
- You must be signed into Teams in that browser (or it will prompt login).
- If you get "tenant" errors, add your tenant ID: `https://teams.microsoft.com/l/chat/0/0?tenantId=<YOUR_TENANT_ID>&users=28:<BOT_APP_ID>`

**2. Enable Developer preview (if you use developer preview distribution)**

- In Teams: **Settings** (click your profile) → **General** → **Developer preview** → turn **On**.
- Restart Teams, then try **Apps** → search again and **New chat** → type bot name.

**3. Same tenant**

- The account you use in Teams must be in the **same Microsoft 365 tenant** as the Azure Bot and the app registration. Different tenant = app/bot won't appear.

**4. Install from Developer Portal**

- Go to **[Teams Developer Portal](https://dev.teams.microsoft.com/)** → open your app → click **Preview in Teams** (top right). That should open Teams and install the app for you, then you can chat.

**5. Upload the app package yourself**

- Build the app package (manifest JSON + outline.png + color.png in a .zip).
- In Teams: **Apps** → **Manage your apps** → **Upload an app** → **Upload a custom app**.
- Select your .zip. After upload, the app appears under **Apps**; open it to start 1:1 chat.

**6. Confirm the bot works**

- **Azure Portal** → your **Azure Bot** → **Test in Web Chat**. Send a message. If the bot replies there, the backend is fine and the issue is only Teams app discovery/install.

For bot or Genie errors, use **Web App** → **Log stream** and the main deploy doc (**DEPLOY_AZURE_APP_SERVICE.md**).
