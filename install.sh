# !/bin/bash

SETUP_REMOTE=true
if [ $# -eq 0 ]; then
    echo "No remote repository provided. Git setup will be skipped."
    SETUP_REMOTE=false
fi

# create necessary directories
echo "Creating necessary directories"
mkdir -p apps bin build configs utils libs/user_extensions/include

# initialize git repository
echo "Initializing git repository"
git init

echo "Adding tea as a submodule"
git submodule add git@github.com:jniedzie/tea.git tea
git submodule update --init --recursive
git commit -m "Add tea as a submodule"

# copy and removing files
echo "Copying CMakelists.txt from tea"
cp tea/templates/CMakeLists.template.txt CMakeLists.txt
cp tea/templates/gitignore.template .gitignore
cp tea/templates/UserExtensionsHelpers.template.hpp libs/user_extensions/include/UserExtensionsHelpers.hpp
rm install.sh

if [ "$SETUP_REMOTE" = true ]; then
    echo "Setting up remote"
    git remote add origin $1
    git add .
    git commit -m "Initial commit"

    # take what's in the repo already (like gitignore, README, etc.) and push all other files
    git pull --rebase origin main
    git push -u origin main
fi
