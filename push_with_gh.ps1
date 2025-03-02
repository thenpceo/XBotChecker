# Push to GitHub using GitHub CLI
# First, authenticate with GitHub
Write-Host "Authenticating with GitHub..." -ForegroundColor Green
gh auth login

# Create a repository on GitHub
Write-Host "Creating repository on GitHub..." -ForegroundColor Green
gh repo create thenpceo/XBotChecker --public --source=. --remote=origin --push 