@echo off
git remote remove origin
git remote add origin https://github.com/thenpceo/XBotChecker.git
git push -u origin vercel-backup-deploy:main 