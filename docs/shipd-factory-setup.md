<!-- doc-type: how-to -->

# Run your own shipd-factory host

> **Beta, invite only:** the factory code is private, and access is by invitation.

This page sets up your own factory host and points the `/shipd-factory` skill
at it. The [concept page](shipd-factory.md) explains the factory. The factory's
scripts default the host and bind address to the maintainer's host, so every
command here sets them. Placeholders are `<host>`, `<user>` and so on.

## 1. What the host needs

The tested setup, not a hard minimum:

- Debian 13 on x86_64 (amd64).
- 4 vCPU, 12 GB RAM and 64 GB disk, which runs two job workers.
- A `debian` user with passwordless sudo, reached over ssh from your machine.
- Outbound internet to GitHub, the Go and Kubernetes download sites and the Claude API.

No GPU: jobs run in gVisor sandboxes. The tested host has `/dev/kvm`; nobody
has tried one without it. The install puts docker, Go, kubectl, kind and ko on
the host. It builds one kind cluster running Agent Substrate (`ate-system`) and
ax (`ax-system`), with a gVisor worker pool.

For reference, see Google's [ax](https://github.com/google/ax), whose
`docs/installation.md` covers a manual install, and
[Agent Substrate](https://github.com/agent-substrate/substrate). The factory
pins both to exact commits in `server/versions.env`. Use the factory's scripts,
not the upstream quick start.

## 2. Install the cluster

Run these from the factory checkout on your machine. Export your host once.
`<user>` is `debian`, because the bootstrap and the orchestrator unit assume
that user and `/home/debian`.

```sh
export AX_HOST=<host> AX_USER=<user>
```

Bootstrap the host. The script runs on the host, installs the tools and adds
`debian` to the docker group.

```sh
ssh <user>@<host> bash -s < server/provision.sh
```

Copy `server/` to `~/shipd-factory` and build the cluster from the pins.
`install.sh` ends `install: ok`. It refuses an existing kind cluster unless you
pass `--recreate`.

```sh
server/deploy.sh
```

Build the runner image, then prove the image and the cluster.

```sh
server/deploy.sh --image
ssh <user>@<host> ~/shipd-factory/server/image-smoke.sh
ssh <user>@<host> ~/shipd-factory/server/smoke.sh
```

## 3. Orchestrator

The orchestrator listens on port 8080 at `ORCH_BIND`. The unit sets none and
the install checks health at the maintainer's address, so edit your checkout.

1. Under `[Service]` in `server/orchestrator/shipd-factory-orchestrator.service`,
   add `Environment=ORCH_BIND=<bind-address>:8080`.
2. In `server/orchestrator/install.sh`, set
   `URL="http://<bind-address>:8080/health"`.

Then install and restart the unit with `server/deploy.sh --orchestrator`. It
ends `orchestrator: ok`. The unit `shipd-factory-orchestrator` runs as the host
user from `~/shipd-factory`. Read its logs with
`journalctl -u shipd-factory-orchestrator`.

## 4. Your GitHub App and reviewer

Each operator creates their own App and reviewer, and shares nothing.

1. Open Settings, Developer settings, GitHub Apps, then New GitHub App.
2. Choose any name and turn the webhook off.
3. Set repository permissions: Contents read and write, Pull requests read and
   write, and Metadata read.
4. Note the App id and generate a private key.
5. Create a separate GitHub user for reviews, sign it in with `gh auth login`,
   then switch back with `gh auth switch -u <your-login>`.
6. Install the App on each repo, and invite the reviewer there with push access.

Store three files in `~/.config/shipd-factory/` on the host, each mode 0600.
Write them over ssh stdin with `umask 077`, never as a command argument. First
check that `gh auth token -u <reviewer-login>` prints a token. Without a reviewer
sign-in it prints nothing, and the last line writes an empty `reviewer.token`.

```sh
ssh <user>@<host> 'umask 077; mkdir -p ~/.config/shipd-factory; cat > ~/.config/shipd-factory/github-app.pem' < <downloaded-key>.pem
printf 'GITHUB_APP_ID=<id>\nREVIEWER_LOGIN=<reviewer-login>\n' | ssh <user>@<host> 'umask 077; cat > ~/.config/shipd-factory/credentials.env'
gh auth token -u <reviewer-login> | ssh <user>@<host> 'umask 077; cat > ~/.config/shipd-factory/reviewer.token'
```

Check them, adding `<owner/repo>` to check one install.
```sh
ssh <user>@<host> python3 ~/shipd-factory/server/credentials/ghcreds.py check [<owner/repo>]
```

It must print `ok: app <your-app-slug>` and `ok: reviewer <reviewer-login>`. With a
repo it also prints `ok: installed on <owner/repo>`. The factory reads the bot
name from the App, so any App name works.

## 5. Claude token

A job fails at `credentials` without a long-lived token from
`claude setup-token`. Store it on the host.

```sh
<token-command> | ssh <user>@<host> 'umask 077; cat > ~/.config/shipd-factory/claude-oauth.token'
ssh <user>@<host> python3 ~/shipd-factory/server/egress/egress.py setup
```

Replace `<token-command>` with whatever prints the token, such as `pbpaste`.
The setup stores it for the cluster and applies the egress policy, so jobs reach
only an allowlist of hosts. It ends `ok: secret claude-oauth`.

## 6. Network

The API has no authentication beyond the network. Never expose it publicly;
use a private network or an ssh tunnel.

```sh
ssh -N -L 8080:<bind-address>:8080 <user>@<host>
```

## 7. Point the skill

Install the skill. It prints `shipd-factory: installed` and its path under
`~/.claude/skills/shipd-factory`. Set the URL to `http://<bind-address>:8080`
on a private network, or `http://localhost:8080` for a tunnel. Check health,
which prints `ok: true` and exits 0 when healthy.

```sh
skill/install.sh
export SHIPD_FACTORY_URL=http://<bind-address>:8080
python3 ~/.claude/skills/shipd-factory/shipd_factory.py health
```

Then run `/shipd-factory onboard <owner/repo>`, as in
[Set up a repo](shipd-factory.md#set-up-a-repo).
