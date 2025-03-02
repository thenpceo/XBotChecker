@echo off
echo Deploying to GitHub...

echo Checking Git status...
git status

echo Setting up remote repository...
git remote remove origin
git remote add origin https://github.com/thenpceo/XBotChecker.git

echo Creating main branch...
git branch -m main

echo Adding all files...
git add .

echo Committing changes...
git commit -m "Initial commit for XBotChecker"

echo Pushing to GitHub...
git push -u origin main

echo Deployment complete!
pause 