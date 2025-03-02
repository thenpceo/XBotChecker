Write-Host "Deploying to GitHub..." -ForegroundColor Green

Write-Host "Checking Git status..." -ForegroundColor Yellow
git status

Write-Host "Setting up remote repository..." -ForegroundColor Yellow
git remote remove origin
git remote add origin https://github.com/thenpceo/XBotChecker.git

Write-Host "Creating main branch..." -ForegroundColor Yellow
git branch -m main

Write-Host "Adding all files..." -ForegroundColor Yellow
git add .

Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "Initial commit for XBotChecker"

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main

Write-Host "Deployment complete!" -ForegroundColor Green
Read-Host -Prompt "Press Enter to exit" 