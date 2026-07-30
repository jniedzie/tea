# tea documentation

The documentation is a Jekyll site. The source lives in `docs/` on the `gh-pages` branch and is published by GitHub Pages from that branch's `/docs` directory.

## Preview locally

1. Install Docker
The easiest way to run it locally is with Docker. 

**macOS**
Install [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/). If the `docker` command is not available in the terminal, install it with brew:

```bash
brew install --cask docker
```

Before the first use, start Docker Desktop yourself and wait until it says that Docker is running. Docker Desktop may require a first-run license, login, or macOS permission confirmation that a shell script cannot complete.

2. Run locally

Once docker is installed and running, you can start the website:

```bash
cd docs
./run.sh
```

The script prints the preview URL and opens it in the default browser <http://localhost:4000/tea/docs/home/>. 

Keep the terminal open while using the preview; press `Ctrl-C` there to stop the server.

The image uses the current host architecture. Set `DOCKER_PLATFORM` when a different platform is required, for example `DOCKER_PLATFORM=linux/amd64 ./run.sh`.

## Publishing

GitHub Pages must be configured in the `jniedzie/tea` repository settings as:

- **Source:** Deploy from a branch
- **Branch:** `gh-pages`
- **Folder:** `/docs`

After a commit is pushed to `gh-pages`, GitHub Pages builds and publishes the contents of `docs/` automatically. The public site is <https://jniedzie.github.io/tea/docs/home/>.

Keep `baseurl: "/tea/"` in `_config.yml` for the published site. The local command above supplies the same value explicitly, so links and assets behave the same way in a preview.
