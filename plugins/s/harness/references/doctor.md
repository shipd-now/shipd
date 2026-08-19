# /s:doctor reference — the GitHub-side remedies

Read this before proposing any remedy that changes state on GitHub. The three
checks below (`protection`, `automerge`, `copilot-secret`) are the only ones
whose remedies leave the local machine.

## Take the repository and branch from the finding

The preflight names both in its own detail — for example ``the default branch
`main` of acme/widget is not protected``. Never resolve `<nwo>` or `<default>`
yourself, and never run a remedy against a repository the detail did not name.

## Tell the two `protection` warnings apart

Read the detail text before choosing; getting this backwards replaces an
existing protection ruleset.

**"is not protected"** — the branch has no protection at all. Offer the minimal
protection that requires the gate and changes nothing else:

```bash
gh api -X PUT repos/<nwo>/branches/<default>/protection \
  --input - <<'JSON'
{"required_status_checks": {"strict": false,
                            "contexts": ["semantic-review"]},
 "enforce_admins": false,
 "required_pull_request_reviews": null,
 "restrictions": null}
JSON
```

**"does not require the `semantic-review` status context"** — the branch is
protected and already requires checks. Append, never replace:

```bash
gh api -X POST \
  repos/<nwo>/branches/<default>/protection/required_status_checks/contexts \
  -f "contexts[]=semantic-review"
```

**"requires no status checks at all"** — report-only. The append call 404s
(there is nothing to append to) and the whole-protection PUT would clobber the
branch's existing reviews, restrictions, and admin enforcement. Relay the
manual hint: an admin enables required status checks on that branch and adds
`semantic-review` to them.

## `automerge`

```bash
gh api -X PATCH repos/<nwo> -F allow_auto_merge=true
```

## `copilot-secret` — a hand-off, never a command you run

The token has to be minted by a human. Report, as prose rather than a choice,
the minimal recipe: a **fine-grained** personal access token owned by the
account whose Copilot subscription pays for the reviews, with **repository
access: none** and exactly one account permission — **"Copilot Requests" → Read
and write** — on a bounded expiry. Then hand over the storage step for the user
to run themselves:

```
gh secret set COPILOT_GITHUB_TOKEN --repo <nwo>
```

Do not run it, do not read the token, and never suggest a broader-scope token.

## Missing admin permission

Where a `protection`, `automerge`, or `copilot-secret` detail says the token
lacks admin permission, the finding is report-only: the call would be denied.
Name what an admin has to change and move on.
