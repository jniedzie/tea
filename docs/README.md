# tea documentation

The documentation is a Jekyll site. The source lives in `docs/` on the
`gh-pages` branch and is published by GitHub Pages from that branch's `/docs`
directory.

## Preview locally

Docker avoids macOS's protected system Ruby and does not require installing
Ruby gems on the host. Install [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/)
if the `docker` command is not available:

```bash
brew install --cask docker
```

Before the first use, start Docker Desktop yourself and wait until it says
that Docker is running. Docker Desktop may require a first-run license,
login, or macOS permission confirmation that a shell script cannot complete.
After that, `run.sh` attempts to start it automatically when it is installed
but stopped, and waits for the Docker daemon to become ready. Increase the
wait time if needed with `TEA_DOCKER_START_TIMEOUT=180`.

```bash
cd docs
./run.sh
```

The script prints the preview URL and opens it in the default browser on
macOS:
<http://localhost:4000/tea/docs/home/>. Keep the terminal open while using
the preview; press `Ctrl-C` there to stop the server. Set
`TEA_OPEN_BROWSER=0` to prevent automatic browser opening.

The image uses the current host architecture. Set `DOCKER_PLATFORM` when a
different platform is required, for example
`DOCKER_PLATFORM=linux/amd64 ./run.sh`.

There is intentionally no native Ruby setup documented here. The repository
uses an older GitHub Pages/Jekyll dependency set, while macOS ships a
protected Ruby 2.6 and current package managers may provide Ruby 4.x. Both
lead to avoidable Bundler failures. Docker keeps the required Ruby and gems
isolated and makes the preview procedure consistent across shells and Macs.
The older `./run.sh --docker` form is still accepted, but the argument is no
longer needed.

## Publishing

GitHub Pages must be configured in the `jniedzie/tea` repository settings as:

- **Source:** Deploy from a branch
- **Branch:** `gh-pages`
- **Folder:** `/docs`

After a commit is pushed to `gh-pages`, GitHub Pages builds and publishes the
contents of `docs/` automatically. The public site is
<https://jniedzie.github.io/tea/docs/home/>.

Keep `baseurl: "/tea/"` in `_config.yml` for the published site. The local
command above supplies the same value explicitly, so links and assets behave
the same way in a preview.
