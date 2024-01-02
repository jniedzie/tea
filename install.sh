# !/bin/bash

# create necessary directories
mkdir -p apps bin build configs libs tea

# initialize git repository
git init

# add tea as a submodule
git submodule add git@github.com:jniedzie/tea.git tea
git commit -m "Add tea as a submodule"

# copy CMakelists.txt from tea
cp tea/user_files/CMakeLists.txt .

# setup remote
git remote add origin $1
git add .
git commit -m "Initial commit"
