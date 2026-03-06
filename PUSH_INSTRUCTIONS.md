# Push to GitHub and Databricks

## 1. Push to GitHub (`https://github.com/jaison-samuel-d/teams-genie`)

Run these in PowerShell from the project folder:

```powershell
cd D:\teams-genie-bot

# If this is a new repo (no .git yet):
git init
git branch -M main

# Add the GitHub remote (use origin if you haven't set it yet)
git remote add origin https://github.com/jaison-samuel-d/teams-genie.git
# If origin already exists and points elsewhere, use: git remote set-url origin https://github.com/jaison-samuel-d/teams-genie.git

# Stage and commit (only tracked files; .env is ignored)
git add app.py app.yaml requirements.txt README.md DEPLOY_DATABRICKS_APPS.md PUSH_INSTRUCTIONS.md .gitignore .databricksignore .env.example setup_git_and_push.ps1
git status
git commit -m "Teams Genie bot: app, Databricks Apps app.yaml, deploy doc"

# Push (first time: set upstream)
git push -u origin main
```

If the GitHub repo already has content (e.g. a README created on GitHub), pull first:

```powershell
git pull origin main --rebase
# then push
git push -u origin main
```

Use a **personal access token (PAT)** as password when Git asks for credentials, or set up SSH and use the SSH remote URL: `git@github.com:jaison-samuel-d/teams-genie.git`.

---

## 2. Push (sync) to Databricks workspace

After [installing the Databricks CLI](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/) and logging in (`databricks configure --token`), sync this folder to a workspace path:

```powershell
cd D:\teams-genie-bot

# Sync current folder to your user folder in the workspace
# Replace <your-email> with your Databricks user email
databricks sync . /Workspace/Users/<your-email>/teams-genie-bot
```

Example if your login is `jaison.samuel@company.com`:

```powershell
databricks sync . /Workspace/Users/jaison.samuel@company.com/teams-genie-bot
```

- This uploads `app.py`, `app.yaml`, `requirements.txt`, and other files (not `.env` or `.venv` — add them to `.databricksignore` if you want to exclude more).
- Then in **Databricks** → **Compute** → **Apps** → your app → **Deploy** → choose **Workspace folder** → select `/Workspace/Users/<your-email>/teams-genie-bot` → **Deploy**.

### Optional: exclude extra files from sync

Create `.databricksignore` in the project root (same format as `.gitignore`) so `databricks sync` skips them, e.g.:

```
.venv/
.env
__pycache__/
*.pyc
.git/
```

Then run `databricks sync` as above.
