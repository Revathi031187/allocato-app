# Run this in PowerShell from D:\teams-genie-bot
# Usage: .\setup_git_and_push.ps1

Set-Location $PSScriptRoot

if (Test-Path .git) {
    Write-Host "Git repo already exists."
} else {
    Write-Host "Initializing git repository..."
    git init
    git branch -M main
    git remote add origin https://github.com/jaison-samuel-d/teams-genie.git
    Write-Host "Done. Remote origin set to https://github.com/jaison-samuel-d/teams-genie.git"
}

Write-Host "Staging files..."
git add app.py app.yaml requirements.txt README.md DEPLOY_DATABRICKS_APPS.md PUSH_INSTRUCTIONS.md .gitignore .databricksignore
git status

Write-Host "Committing..."
git commit -m "Teams Genie bot: app, Databricks Apps, deploy and push docs"

Write-Host "Ready to push. Run: git push -u origin main"
Write-Host "If the GitHub repo already has content, run first: git pull origin main --rebase"
