---
title: Installation
permalink: /docs/repo_setup/
---

## Initial setup

1. Create an empty directory for your analysis:
```bash
mkdir tea_analysis
cd tea_analysis
```
2. Get `tea` install script and set permissions:
```bash
curl -O https://raw.githubusercontent.com/jniedzie/tea/main/install.sh
chmod 700 install.sh
```

3. Optionally (highly recommended): create your analysis repository on github (go to your profile > repositories > new, pick a suitable name and create). You can choose to add README, licence or gitignore. When the repo is ready, save the URL it gave you (or click on "Code" button to find it), something like: 
```
git@github.com:your_username/tea_analysis.git
```

4. Run `tea` install script, providing URL to your repo as an argument (optional, but recommended), e.g.:
```bash
./install.sh git@github.com:your_username/tea_analysis.git
```

After following these steps, you should see a directory structure in your project including the `tea` directory. If you specified the git repo URL, your code was pushed to your repo, so you can also see it online (although you won't see empty directories there - this is expected).

From here you can go to [build & run]({{site.baseurl}}/docs/build/)

---

## Updating your analysis

Now you can regularly push to your repository:
```bash
git add path_to_file
git commit -m "Commit message"
git push origin main
```

---

## Updating tea

From time to time you can also pull changes from `tea` repository. Before you do that, **make sure all your changes are commited and pushed to your repository!!** Then, run the script which will update `tea`:

```bash
./tea/update.sh
```
---

## Contributing to `tea`

You can also contribute to the `tea` framework itself! `tea` directory is a git sub-module - you can go there (`cd tea`) and setup your own branch, commit to it and eventually create Pull Requests to include your changes in the main branch.