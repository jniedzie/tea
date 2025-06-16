---
title: Installation
permalink: /docs/repo_setup/
---

#### Initial setup
We highly recommend that you keep your analysis code in a git repository, while (optionally) downloading updates in the `tea` framework from our repository. As a rule of thumb, you should not modify `tea` code, only your apps, configs and classes.

Then, to set up `tea` together with your analysis code:

1. Create your analysis repository on github (go to your profile > repositories > new, pick a suitable name and create). You can choose to add README, licence or gitignore. When the repo is ready, save the URL it gave you (or click on "Code" button to find it), something like: 
```
git@github.com:your_username/tea_analysis.git
```
2. Create an empty directory for your analysis:
```bash
mkdir tea_analysis
cd tea_analysis
```
3. Get `tea` install script:
```bash
curl -O https://raw.githubusercontent.com/jniedzie/tea/main/install.sh
```
4. Run `tea` install script, providing URL to your repo as an argument, e.g.:
```bash
chmod 700 install.sh
./install.sh git@github.com:your_username/tea_analysis.git
```

After following these steps, you should see a directory structure in your project including the `tea` directory. Your code was pushed to your repo, so you can also see it online (although you won't see empty directories there - this is expected).

#### Updating your analysis

Now you can regularly push to your repository:
```bash
git add path_to_file
git commit -m "Commit message"
git push origin main
```

#### Updating tea

From time to time you can also pull changes from `tea` repository. Before you do that, **make sure all your changes are commited and pushed to your repository!!** Then, run the script which will update `tea`:

```bash
./tea/update.sh
```

#### Contributing to `tea`

You can also contribute to the `tea` framework itself! `tea` directory is a git sub-module - you can go there (`cd tea`) and setup your own branch, commit to it and eventually create Pull Requests to include your changes in the main branch.