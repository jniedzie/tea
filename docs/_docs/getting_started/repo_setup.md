---
title: Repositories setup
permalink: /docs/repo_setup/
---


We highly recommend that you keep your analysis code in a git repository, while (optionally) downloading updates in the TEA framework from our repository. In order to do that:

1. Create your analysis repository on github (go to your profile -> repositories -> new, pick a suitable name and create). Don't add any README, licence or gitignore.
2. Create an empty directory for your analysis:
```bash
mkdir tea_ttH_analysis
cd tea_ttH_analysis
```
4. Clone TEA repository:
```bash
git clone https://github.com/jniedzie/tea.git .
```
5. Setup git remotes:
```bash
git remote set-url origin git@github.com:your_username/your_repo.git
git remote add upstream git@github.com:jniedzie/tea.git
git push origin main
```

Now you can regularly push to your repository:
```bash
git add path_to_file
git commit -m "Commit message"
git push origin main
```

while from time to time you can also pull changes from TEA repository:
```bash
git pull --rebase upstream main
```

Keep in mind that if you modify parts for the framework itself, you will have to resolve conflicts when updating TEA.
You can (and should!) modify README.md though - it will be ignored when pulling changes from upstream.