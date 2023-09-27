---
title: Repositories setup
permalink: /docs/repo_setup/
---

#### Initial setup
We highly recommend that you keep your analysis code in a git repository, while (optionally) downloading updates in the `tea` framework from our repository. As a rule of thumb, you should not modify `tea` code, only your apps, configs and classes.

To set up `tea` together with your analysis code:

1. Create an empty directory for your analysis:
```bash
mkdir tea_ttH_analysis
cd tea_ttH_analysis
```
2. Clone `tea` repository:
```bash
git clone https://github.com/jniedzie/tea.git .
```

3. Create your analysis repository on github (go to your profile -> repositories -> new, pick a suitable name and create). Don't add any README, licence or gitignore.

4. Setup git remotes:
```bash
git remote set-url origin git@github.com:your_username/your_repo.git
git remote add upstream git@github.com:jniedzie/tea.git
git push origin main
```

5. Prepare .gitignore file for your repo:
```bash
cp .gitignore_user .gitignore
```

#### Updating your analysis

Now you can regularly push to your repository:
```bash
git add path_to_file
git commit -m "Commit message"
git push origin main
```

#### Updating tea

From time to time you can also pull changes from `tea` repository. Before you do that, **make sure all your changes are commited and pushed to your repository!!** Then, run the script which will update `tea` and push its new version to your repository:

```bash
./update_tea.sh
```
