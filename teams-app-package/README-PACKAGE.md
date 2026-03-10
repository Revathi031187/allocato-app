# Create the Teams app package (for upload)

This folder is used to build the **.zip** you upload in Teams so the bot app is installed and the direct link works.

---

## Step 1: Create the two icon files

You need **outline.png** (32×32) and **color.png** (192×192) in this folder.

**Option A – Generate placeholder icons (quick)**

From this folder (`teams-app-package`) run:

```bash
cd teams-app-package
python create_icons.py
```

This creates `outline.png` and `color.png` using matplotlib. Replace them later with your own icons if you want.

**Option B – Use your own icons**

- **outline.png**: 32×32 pixels, PNG (e.g. logo on transparent or white background).
- **color.png**: 192×192 pixels, PNG (full-color app icon).

Put both files in the `teams-app-package` folder.

---

## Step 2: Check the folder contents

Inside `teams-app-package` you should have:

- `manifest.json` (already there)
- `outline.png`
- `color.png`

No subfolders. No extra files required.

---

## Step 3: Zip the contents (not the folder)

The zip must contain the **files** at the top level, not a folder named `teams-app-package`.

### Windows (PowerShell)

```powershell
cd d:\teams-genie-bot\teams-app-package
Compress-Archive -Path manifest.json, outline.png, color.png -DestinationPath ..\TeamsGenieAssistant.zip
```

The zip will be created as `d:\teams-genie-bot\TeamsGenieAssistant.zip`.

### Windows (Explorer)

1. Open the folder `teams-app-package` in File Explorer.
2. Select **manifest.json**, **outline.png**, and **color.png** (Ctrl+Click each).
3. Right-click → **Send to** → **Compressed (zipped) folder**.
4. Name it e.g. `TeamsGenieAssistant.zip`.
5. **Important:** Open the zip and confirm you see the three files at the **top level** (no `teams-app-package` folder inside). If you see a folder inside, instead: open `teams-app-package`, select the three files, then right-click → Send to → Compressed folder.

### Windows (Command prompt)

```cmd
cd d:\teams-genie-bot\teams-app-package
tar -a -c -f ..\TeamsGenieAssistant.zip manifest.json outline.png color.png
```

---

## Step 4: Upload in Teams

1. Open **Microsoft Teams**.
2. Go to **Apps** (left sidebar).
3. Click **Manage your apps** (bottom left) or **More apps** → **Manage your apps**.
4. Click **Upload an app** → **Upload a custom app** (or **Upload for me**).
5. Select **TeamsGenieAssistant.zip**.
6. After upload, the app appears in **Apps**. Open it to start a 1:1 chat with the bot.
7. You can also try the direct link again; it should work once the app is installed.

---

## Checklist

- [ ] `outline.png` and `color.png` are in `teams-app-package` (created or copied).
- [ ] Zip contains **only** `manifest.json`, `outline.png`, `color.png` at the top level.
- [ ] Uploaded the zip in Teams via **Manage your apps** → **Upload an app**.
- [ ] Opened the app or used the direct link to chat with the bot.
