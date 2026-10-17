#!/usr/bin/env python3
"""team_merge_test.py: prove on the unkannybanny test repo that GitHub itself
enforces the shipd merge rules for a team of three identities.

Verbs:
  preflight [--only user|repo]  print `ok|missing <name> - <fix>`; exit 3 on a miss
  apply                         apply the `shipd merge rules` ruleset and read it back
  run --out DIR                 one throwaway pull request proving rules (a) to (e)
  report --evidence FILE        render the evidence file as a retro record

The driver is confined to ALLOWED_REPO. The reviewer identity comes only from
the environment (TEAM_TEST_REVIEWER_GH_TOKEN or TEAM_TEST_REVIEWER_GH_CONFIG_DIR),
reaches only the reviewer subprocess, and is redacted from every output line.
Stdlib only; see docs/team-merge-test.md.
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_REPO = "mikkel-bergmann/unkannybanny"
TOKEN_VAR = "TEAM_TEST_REVIEWER_GH_TOKEN"
CONFIG_VAR = "TEAM_TEST_REVIEWER_GH_CONFIG_DIR"
GATE_FILE = ".github/workflows/copilot-review-gate.yml"
COPILOT_SECRET = "COPILOT_GITHUB_TOKEN"
RULESET_NAME = "shipd merge rules"
SHIPD = Path(__file__).resolve().parent.parent / "plugins" / "s" / "bin" / "shipd"
GH_TIMEOUT = 120
BOT = "github-actions[bot]"

EXIT_FAIL, EXIT_USAGE, EXIT_MISSING = 1, 2, 3

_TOKEN_SHAPES = re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]+")


class Gh:
    """The one subprocess seam. ``who`` is ``author`` (the ambient gh login)
    or ``reviewer`` (the environment-supplied second identity)."""

    def __init__(self, environ=None):
        self.environ = dict(os.environ if environ is None else environ)

    def reviewer_configured(self):
        return bool(self.environ.get(TOKEN_VAR) or self.environ.get(CONFIG_VAR))

    def secrets(self):
        return [v for v in (self.environ.get(TOKEN_VAR),) if v]

    def _env(self, who):
        env = dict(self.environ)
        if who != "reviewer":
            env.pop(TOKEN_VAR, None)
            env.pop(CONFIG_VAR, None)
            return env
        if env.get(TOKEN_VAR):
            env["GH_TOKEN"] = env[TOKEN_VAR]
            env.pop("GH_CONFIG_DIR", None)
        elif env.get(CONFIG_VAR):
            env["GH_CONFIG_DIR"] = env[CONFIG_VAR]
            env.pop("GH_TOKEN", None)
            env.pop("GITHUB_TOKEN", None)
        return env

    def exec(self, argv, who="author", stdin=None, cwd=None):
        """``(code, stdout, stderr)`` for ``argv``, bounded and redacted."""
        try:
            proc = subprocess.run(argv, input=stdin, cwd=cwd, env=self._env(who),
                                  capture_output=True, text=True,
                                  timeout=GH_TIMEOUT)
        except subprocess.TimeoutExpired:
            return (1, "", "timed out after %ds" % GH_TIMEOUT)
        except OSError as exc:
            return (1, "", str(exc))
        secrets = self.secrets()
        return (proc.returncode, redact(proc.stdout, secrets),
                redact(proc.stderr, secrets))

    def run(self, args, who="author", stdin=None, cwd=None):
        return self.exec(["gh"] + list(args), who=who, stdin=stdin, cwd=cwd)


def redact(text, secrets):
    """``text`` with every secret value and token-shaped string replaced."""
    text = text or ""
    for secret in secrets or []:
        if secret:
            text = text.replace(secret, "[redacted]")
    return _TOKEN_SHAPES.sub("[redacted]", text)


def classify_probe(out):
    """``blocked`` for an HTTP 405 on the merge call, ``merged`` for a 2xx,
    otherwise ``other``; read from the status line ``gh api -i`` prints."""
    match = (re.match(r"\s*HTTP/\S+\s+(\d{3})", out or "")
             or re.search(r"\(HTTP (\d{3})\)", out or ""))
    if not match:
        return "other"
    code = int(match.group(1))
    if code == 405:
        return "blocked"
    if 200 <= code < 300:
        return "merged"
    return "other"


def approvals_on_head(reviews, head, author):
    """Sorted logins other than ``author`` whose latest approving-or-
    dismissing review on ``head`` is APPROVED. A later COMMENTED review does
    not change an approval; DISMISSED removes it."""
    latest = {}
    for rev in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        login = ((rev.get("user") or {}).get("login")) or ""
        if (rev.get("commit_id") != head or not login
                or rev.get("state") not in ("APPROVED", "DISMISSED",
                                            "CHANGES_REQUESTED")):
            continue
        latest[login] = rev["state"]
    return sorted(l for l, s in latest.items()
                  if s == "APPROVED" and l.lower() != (author or "").lower())


def _login(gh, who):
    code, out, _err = gh.run(["api", "user", "--jq", ".login"], who=who)
    return out.strip() if code == 0 else ""


def _json(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def check_prereqs(gh, repo, only=None):
    """Preflight results as ``(status, name, detail)`` rows; ``status`` is
    ``ok`` or ``missing`` and ``detail`` is the fix for a miss."""
    rows = []

    def add(ok, name, fix):
        rows.append(("ok" if ok else "missing", name, "satisfied" if ok else fix))

    if only in (None, "user"):
        env_ok = gh.reviewer_configured()
        add(env_ok, "reviewer-env",
            "export %s or %s in your own shell" % (TOKEN_VAR, CONFIG_VAR))
        author = _login(gh, "author")
        reviewer = _login(gh, "reviewer") if env_ok else ""
        add(bool(reviewer), "reviewer-auth",
            "the reviewer credential must make `gh api user` succeed")
        add(bool(reviewer and author and reviewer.lower() != author.lower()),
            "reviewer-login",
            "the reviewer must be a different account from the author")
        perm = ""
        if reviewer:
            code, out, _e = gh.run(["api", "repos/%s/collaborators/%s/permission"
                                    % (repo, reviewer), "--jq", ".permission"])
            perm = out.strip() if code == 0 else ""
        add(perm in ("write", "admin"), "reviewer-collaborator",
            "add the reviewer as a write collaborator on %s and accept" % repo)
        code, out, _e = gh.run(["api", "repos/%s/actions/permissions/workflow" % repo])
        data = _json(out) if code == 0 else None
        add(bool(data and data.get("can_approve_pull_request_reviews") is True),
            "actions-approve",
            "consent to Actions approving pull requests (/s:gate optional row)")
    if only in (None, "repo"):
        code, out, _e = gh.run(["api", "repos/%s/actions/secrets" % repo,
                                "--jq", ".secrets[].name"])
        add(code == 0 and COPILOT_SECRET in out.split(), "copilot-secret",
            "set the %s Actions secret" % COPILOT_SECRET)
        code, out, _e = gh.run(["api", "-H", "Accept: application/vnd.github.raw",
                                "repos/%s/contents/%s?ref=main" % (repo, GATE_FILE)])
        add(code == 0 and "PR_AUTHOR" in out, "gate-workflow",
            "merge the prep PR: `shipd copilot add` in the repo")
        code, out, _e = gh.run(["api", "-H", "Accept: application/vnd.github.raw",
                                "repos/%s/contents/.shipd-config.json?ref=main" % repo])
        data = _json(out) if code == 0 else None
        add(isinstance(data, dict) and "merge" in data, "merge-block",
            "merge the prep PR: add an explicit `merge` block to .shipd-config.json")
    return rows


def preflight(gh, repo, only, out):
    rows = check_prereqs(gh, repo, only)
    for status, name, detail in rows:
        out("%s %s - %s" % (status, name, detail))
    return EXIT_MISSING if any(r[0] == "missing" for r in rows) else 0


def parse_stream(text):
    """The JSON values in ``text``: one per line (`--jq '.[]'` output), or a
    single document."""
    whole = _json(text)
    if isinstance(whole, list):
        return whole
    if isinstance(whole, dict):
        return [whole]
    values = []
    for line in (text or "").splitlines():
        value = _json(line) if line.strip() else None
        if isinstance(value, dict):
            values.append(value)
    return values


def check_ruleset(detail):
    """``(claim, observed, ok)`` rows for the live `shipd merge rules`
    ruleset, read straight from GitHub's response."""
    rules = {r.get("type"): (r.get("parameters") or {})
             for r in detail.get("rules") or [] if isinstance(r, dict)}
    pr = rules.get("pull_request") or {}
    sc = rules.get("required_status_checks") or {}
    checks = sorted(c.get("context") for c in sc.get("required_status_checks") or []
                    if isinstance(c, dict))
    bypass = len(detail.get("bypass_actors") or [])
    approvals = pr.get("required_approving_review_count")
    return [
        ("ruleset enforcement is active", detail.get("enforcement"),
         detail.get("enforcement") == "active"),
        ("two approving reviews required", approvals, approvals == 2),
        ("approvals dismissed on push", pr.get("dismiss_stale_reviews_on_push"),
         pr.get("dismiss_stale_reviews_on_push") is True),
        ("approval of the last push required",
         pr.get("require_last_push_approval"),
         pr.get("require_last_push_approval") is True),
        ("review threads must be resolved",
         pr.get("required_review_thread_resolution"),
         pr.get("required_review_thread_resolution") is True),
        ("required checks are ci and semantic-review", checks,
         checks == ["ci", "semantic-review"]),
        ("no bypass actors", bypass, bypass == 0),
    ]


def apply_rules(gh, repo, root, out):
    code, o, err = gh.exec([str(SHIPD), "gate", "rules", "apply", "--repo", repo,
                            "--root", root], cwd=root)
    out("gate rules apply: exit %d %s" % (code, (o or err).strip().splitlines()[-1:]))
    if code != 0:
        return EXIT_FAIL
    code, o, err = gh.run(["api", "repos/%s/rulesets" % repo])
    items = parse_stream(o) if code == 0 else []
    item = next((i for i in items if i.get("name") == RULESET_NAME), None)
    if item is None:
        out("FAIL ruleset exists: no ruleset named `%s` on %s" % (RULESET_NAME, repo))
        return EXIT_FAIL
    code, o, err = gh.run(["api", "repos/%s/rulesets/%s" % (repo, item["id"])])
    detail = _json(o) if code == 0 else None
    if not isinstance(detail, dict):
        out("FAIL ruleset readable: %s" % err.strip())
        return EXIT_FAIL
    failed = False
    for claim, observed, ok in check_ruleset(detail):
        out("%s %s: %s" % ("ok" if ok else "FAIL", claim, observed))
        failed = failed or not ok
    return EXIT_FAIL if failed else 0


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class StepFailed(Exception):
    """An assertion did not hold; the run stops and the PR stays open."""


THREADS_QUERY = ("query($owner:String!,$name:String!,$number:Int!){repository("
                 "owner:$owner,name:$name){pullRequest(number:$number){"
                 "reviewThreads(first:100){nodes{isResolved}}}}}")
DOCTOR_CHECKS = ("protection", "merge-rules", "actions-approve")


def checks_green(rollup, names=("ci", "semantic-review")):
    state = {}
    for item in rollup or []:
        name = item.get("name") or item.get("context")
        state[name] = (item.get("conclusion") or item.get("state") or "")
    return all(state.get(n) == "SUCCESS" for n in names)


class Proof:
    """One throwaway pull request and the evidence of what GitHub did to it."""

    def __init__(self, gh, repo, root, out_dir, say, sleep, attempts=120,
                 interval=15):
        self.gh, self.repo, self.root = gh, repo, root
        self.say, self.sleep = say, sleep
        self.attempts, self.interval = attempts, interval
        self.path = os.path.join(out_dir, "evidence.json")
        os.makedirs(out_dir, exist_ok=True)
        self.data = {"repo": repo, "pr_url": None, "pr_number": None,
                     "branch": None, "result": "running", "started": now(),
                     "finished": None, "records": []}
        self.author = ""

    # -- bookkeeping ---------------------------------------------------
    def save(self):
        text = redact(json.dumps(self.data, indent=2, sort_keys=True),
                      self.gh.secrets())
        with open(self.path, "w") as handle:
            handle.write(text + "\n")

    def check(self, rid, claim, observed, ok):
        secrets = self.gh.secrets()
        record = {"id": rid, "claim": claim,
                  "observed": redact(str(observed), secrets),
                  "ok": bool(ok), "at": now()}
        self.data["records"].append(record)
        self.save()
        self.say("%s %s: %s" % ("ok" if ok else "FAIL", rid, record["observed"]))
        if not ok:
            raise StepFailed(rid)

    # -- GitHub reads and writes ----------------------------------------
    def gh_ok(self, args, who="author", what=""):
        code, out, err = self.gh.run(args, who=who, cwd=self.root)
        if code != 0:
            raise StepFailed("%s failed: %s" % (what or " ".join(args[:3]),
                                                redact(err.strip(), self.gh.secrets())))
        return out

    def view(self):
        out = self.gh_ok(["pr", "view", str(self.number), "-R", self.repo, "--json",
                          "headRefOid,state,mergeStateStatus,autoMergeRequest,"
                          "statusCheckRollup,author"], what="pr view")
        return _json(out) or {}

    def reviews(self):
        out = self.gh_ok(["api", "repos/%s/pulls/%d/reviews" % (self.repo, self.number),
                          "--paginate", "--jq", ".[]"], what="list reviews")
        return parse_stream(out)

    def probe(self):
        code, out, err = self.gh.run(
            ["api", "-i", "-X", "PUT",
             "repos/%s/pulls/%d/merge" % (self.repo, self.number),
             "-f", "merge_method=squash"], cwd=self.root)
        text = out if out.lstrip().startswith("HTTP/") else (err or out)
        line = text.strip().splitlines()[0] if text.strip() else "(no response)"
        return classify_probe(text), line

    def approve(self, who, sha):
        self.gh_ok(["api", "-X", "POST",
                    "repos/%s/pulls/%d/reviews" % (self.repo, self.number),
                    "-f", "event=APPROVE", "-f", "commit_id=" + sha],
                   who=who, what="approve as " + who)

    def poll(self, fn, attempts=None):
        for _ in range(attempts or self.attempts):
            value = fn()
            if value:
                return value
            self.sleep(self.interval)
        return None

    def ready(self):
        """The head's sha once ci and semantic-review are green and the bot
        has approved it, else ``None``."""
        info = self.view()
        head = info.get("headRefOid")
        if checks_green(info.get("statusCheckRollup")) and BOT in approvals_on_head(
                self.reviews(), head, self.author):
            return head
        return None

    # -- steps ---------------------------------------------------------
    def open_pr(self):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        branch = "team-merge-test/" + stamp
        self.data["branch"] = branch
        self.author = _login(self.gh, "author")
        run = lambda *a: self.gh_ok(list(a), what=" ".join(a[:2]))
        for argv in (["fetch", "origin", "main"],
                     ["checkout", "-b", branch, "origin/main"]):
            code, _o, err = self.gh.exec(["git"] + argv, cwd=self.root)
            if code != 0:
                raise StepFailed("git %s failed: %s" % (argv[0], err.strip()))
        rel = self.rel = os.path.join("team-merge-test", stamp + ".md")
        os.makedirs(os.path.join(self.root, "team-merge-test"), exist_ok=True)
        with open(os.path.join(self.root, rel), "w") as handle:
            handle.write("Throwaway file for the shipd merge-rules proof (%s).\n" % stamp)
        for argv in (["add", rel], ["commit", "-m", "team-merge-test " + stamp],
                     ["push", "-u", "origin", branch]):
            code, _o, err = self.gh.exec(["git"] + argv, cwd=self.root)
            if code != 0:
                raise StepFailed("git %s failed: %s" % (argv[0], err.strip()))
        url = run("pr", "create", "-R", self.repo, "--base", "main", "--head", branch,
                  "--title", "team-merge-test " + stamp, "--body",
                  "Throwaway pull request for the merge-rules proof. Do not merge by hand.").strip().splitlines()[-1]
        self.data["pr_url"] = url
        self.number = int(url.rstrip("/").rsplit("/", 1)[-1])
        self.data["pr_number"] = self.number
        self.save()
        self.say("opened " + url)

    def step_one_approval_blocks(self):
        head = self.poll(self.ready)
        self.check("a-gate-ready", "ci and semantic-review are green and the bot approved the head",
                   "head=%s" % head, bool(head))
        self.head = head
        cls, line = self.probe()
        info = self.view()
        approvals = approvals_on_head(self.reviews(), head, self.author)
        self.check("a-one-approval-blocks",
                   "one approval (the bot) cannot merge: PUT merge is refused and the state is BLOCKED",
                   "PUT merge -> %s; mergeStateStatus=%s; approvals=%s"
                   % (line, info.get("mergeStateStatus"), approvals),
                   cls == "blocked" and info.get("mergeStateStatus") == "BLOCKED"
                   and approvals == [BOT])

    def step_author_refused(self):
        code, out, err = self.gh.run(["pr", "review", str(self.number), "-R", self.repo,
                                      "--approve"], cwd=self.root)
        text = (err or out).strip()
        self.check("c-author-approval-refused",
                   "the author's own approval is refused by GitHub",
                   "exit %d: %s" % (code, text),
                   code != 0 and "own pull request" in text.lower())
        code, out, err = self.gh.exec([str(SHIPD), "room", "whoami", str(self.number),
                                       "--repo", self.repo], cwd=self.root)
        self.check("c-whoami-author-exit-1", "`shipd room whoami` as the author exits 1",
                   "exit %d: %s" % (code, (err or out).strip()), code == 1)

    def step_reviewer_approves(self):
        code, out, err = self.gh.exec([str(SHIPD), "room", "whoami", str(self.number),
                                       "--repo", self.repo], who="reviewer", cwd=self.root)
        info = _json(out) or {}
        self.check("c-whoami-reviewer-may-approve",
                   "`shipd room whoami` as the reviewer exits 0 with may_approve true",
                   "exit %d: login=%s may_approve=%s" % (code, info.get("login"),
                                                         info.get("may_approve")),
                   code == 0 and info.get("may_approve") is True)
        self.reviewer = info.get("login")
        self.approve("reviewer", self.head)

        def two():
            approvals = approvals_on_head(self.reviews(), self.head, self.author)
            return approvals if len(approvals) >= 2 else None
        approvals = self.poll(two, attempts=20) or []
        info = self.view()
        self.check("a-two-approvals-clean",
                   "two non-author approvals on the head make the state CLEAN with no merge",
                   "approvals=%s; mergeStateStatus=%s; state=%s"
                   % (approvals, info.get("mergeStateStatus"), info.get("state")),
                   len(approvals) >= 2 and info.get("state") == "OPEN"
                   and info.get("mergeStateStatus") == "CLEAN")
        mine = [r for r in self.reviews() if (r.get("user") or {}).get("login") == self.reviewer
                and r.get("commit_id") == self.head]
        self.review_id = mine[-1]["id"] if mine else None

    def step_push_dismisses(self):
        old = self.head
        # A real content change: GitHub keeps approvals across an empty commit.
        os.makedirs(os.path.dirname(os.path.join(self.root, self.rel)), exist_ok=True)
        with open(os.path.join(self.root, self.rel), "a") as handle:
            handle.write("A second commit that changes the diff.\n")
        for argv in (["add", self.rel],
                     ["commit", "-m", "team-merge-test: change after approvals"],
                     ["push", "origin", self.data["branch"]]):
            code, _o, err = self.gh.exec(["git"] + argv, cwd=self.root)
            if code != 0:
                raise StepFailed("git %s failed: %s" % (argv[0], err.strip()))

        def dismissed():
            states = {r.get("id"): r.get("state") for r in self.reviews()}
            return states.get(self.review_id) == "DISMISSED"
        ok = bool(self.poll(dismissed, attempts=20))
        info = self.view()
        self.head = info.get("headRefOid")
        self.check("b-push-dismisses",
                   "a push dismisses the reviewer's approval",
                   "review %s by %s reads %s; head %s -> %s" % (
                       self.review_id, self.reviewer,
                       "DISMISSED" if ok else "not DISMISSED", old, self.head),
                   ok and self.head != old)
        cls, line = self.probe()
        self.check("b-probe-after-push",
                   "the merge call is refused after the push while checks run",
                   "PUT merge -> %s" % line, cls == "blocked")
        head = self.poll(self.ready)
        cls, line = self.probe()
        approvals = approvals_on_head(self.reviews(), self.head, self.author)
        self.check("b-only-bot-reapproves",
                   "with checks green only the bot re-approved; merge is still refused",
                   "head=%s approvals=%s; PUT merge -> %s" % (head, approvals, line),
                   bool(head) and approvals == [BOT] and cls == "blocked")

    def step_auto_merge(self):
        owner, name = self.repo.split("/")
        out = self.gh_ok(["api", "graphql", "-f", "query=" + THREADS_QUERY, "-f",
                          "owner=" + owner, "-f", "name=" + name, "-F",
                          "number=%d" % self.number], what="graphql threads")
        nodes = ((((_json(out) or {}).get("data") or {}).get("repository") or {})
                 .get("pullRequest") or {}).get("reviewThreads", {}).get("nodes") or []
        unresolved = len([n for n in nodes if not n.get("isResolved")])
        self.check("d-threads-resolved", "no unresolved review threads on the head",
                   "head=%s unresolved_threads=%d" % (self.head, unresolved),
                   unresolved == 0)
        self.gh_ok(["pr", "merge", str(self.number), "-R", self.repo, "--auto", "--squash"],
                   what="arm auto-merge")
        info = self.view()
        approvals = approvals_on_head(self.reviews(), self.head, self.author)
        self.check("d-auto-merge-armed-open",
                   "auto-merge is armed last and the pull request stays OPEN on one approval",
                   "state=%s autoMergeRequest=%s approvals=%s" % (
                       info.get("state"), "set" if info.get("autoMergeRequest") else "none",
                       approvals),
                   info.get("state") == "OPEN" and bool(info.get("autoMergeRequest"))
                   and approvals == [BOT])
        self.approve("reviewer", self.head)
        merged = self.poll(lambda: self.view().get("state") == "MERGED", attempts=60)
        self.check("d-merged", "the pull request reaches MERGED with no manual merge call",
                   "state=%s" % ("MERGED" if merged else self.view().get("state")),
                   bool(merged))
        approvals = approvals_on_head(self.reviews(), self.head, self.author)
        self.check("d-two-nonauthor-approvals",
                   "two APPROVED reviews on the merged head come from non-author logins",
                   "head=%s approvals=%s author=%s" % (self.head, approvals, self.author),
                   len(approvals) >= 2)

    def step_doctor(self):
        for argv in (["checkout", "main"], ["pull", "--ff-only", "origin", "main"]):
            code, _o, err = self.gh.exec(["git"] + argv, cwd=self.root)
            if code != 0:
                raise StepFailed("git %s failed: %s" % (argv[0], err.strip()))
        code, out, err = self.gh.exec([str(SHIPD), "doctor"], cwd=self.root)
        lines = [l for l in out.splitlines() if l.split(" ", 1)[0] in ("ok", "warn", "fail")]
        bad = [l for l in lines if l.split(" ", 1)[0] != "ok"
               and l.split(" ")[1] in DOCTOR_CHECKS]
        seen = {l.split(" ")[1] for l in lines if l.split(" ", 1)[0] == "ok"}
        self.check("e-doctor-no-drift",
                   "`shipd doctor` reports ok for protection, merge-rules, and actions-approve",
                   "; ".join(l for l in lines if l.split(" ")[1] in DOCTOR_CHECKS)
                   or "no lines", not bad and set(DOCTOR_CHECKS) <= seen)
        code, out, err = self.gh.exec([str(SHIPD), "gate", "rules", "--repo", self.repo,
                                       "--root", self.root], cwd=self.root)
        self.check("e-rules-no-differs", "bare `shipd gate rules` shows no `differs` line",
                   "exit %d; %d differs line(s)" % (code, out.count("differs")),
                   code == 0 and "differs" not in out)

    def resume(self):
        """Continue a run that stopped at ``b-push-dismisses`` after an empty
        commit: GitHub kept the approvals, so that failed record becomes the
        observed fact and the dismissal proof is retried with a real change.
        The relabel needs proof: the compare API must show no changed file
        between the record's old and new head, else the run refuses."""
        with open(self.path) as handle:
            self.data = json.load(handle)
        last = (self.data.get("records") or [{}])[-1]
        if last.get("id") != "b-push-dismisses" or last.get("ok"):
            raise StepFailed("nothing to resume: the evidence does not end at b-push-dismisses")
        moved = re.search(r"head (\w+) -> (\w+)", last.get("observed") or "")
        if not moved:
            raise StepFailed("cannot prove the push was empty: no old and new head in the record")
        code, out, err = self.gh.exec(
            ["gh", "api", "repos/%s/compare/%s...%s" % (self.repo, moved.group(1), moved.group(2)),
             "--jq", ".files|length"])
        if code != 0 or out.strip() != "0":
            raise StepFailed("the push %s -> %s changed files (or could not be checked); "
                             "only an empty push may be relabelled"
                             % (moved.group(1), moved.group(2)))
        last.update(id="b-empty-push-keeps-approvals", ok=True,
                    claim="an empty push leaves the approvals standing (observed on GitHub; "
                          "the dismissal proof pushes a real change)")
        self.data.update(result="running", finished=None)
        self.number = self.data["pr_number"]
        branch = self.data["branch"]
        self.rel = branch + ".md"
        self.author = _login(self.gh, "author")
        self.reviewer = _login(self.gh, "reviewer")
        code, _o, err = self.gh.exec(["git", "checkout", branch], cwd=self.root)
        if code != 0:
            raise StepFailed("git checkout failed: %s" % err.strip())
        self.head = self.view().get("headRefOid")
        mine = [r for r in self.reviews() if (r.get("user") or {}).get("login") == self.reviewer
                and r.get("commit_id") == self.head and r.get("state") == "APPROVED"]
        if not mine:
            raise StepFailed("no APPROVED review by %s on %s" % (self.reviewer, self.head))
        self.review_id = mine[-1]["id"]
        self.save()

    def run(self, resume=False):
        steps = (self.open_pr, self.step_one_approval_blocks, self.step_author_refused,
                 self.step_reviewer_approves, self.step_push_dismisses,
                 self.step_auto_merge, self.step_doctor)
        if resume:
            steps = (self.resume, self.step_push_dismisses, self.step_auto_merge,
                     self.step_doctor)
        try:
            for step in steps:
                step()
            self.data["result"] = "pass"
        except StepFailed as exc:
            if not self.data["records"] or self.data["records"][-1]["ok"]:
                self.data["records"].append({"id": "run-error", "claim": "the run proceeds",
                                             "observed": redact(str(exc), self.gh.secrets()),
                                             "ok": False, "at": now()})
            self.data["result"] = "fail"
            self.say("stopped: %s (the pull request stays open)" % exc)
        self.data["finished"] = now()
        self.save()
        return 0 if self.data["result"] == "pass" else EXIT_FAIL


def run_proof(gh, repo, root, out_dir, say, sleep, resume=False):
    return Proof(gh, repo, root, out_dir, say, sleep).run(resume=resume)


def _cell(text, limit=400):
    text = " ".join(str(text).split())
    if len(text) > limit:
        text = text[:limit - 3] + "..."
    return text.replace("|", "\\|")


def render_report(evidence):
    """The retro evidence record, as Markdown, from an evidence dict."""
    lines = ["# Team merge test evidence", "",
             "Run of `tools/team_merge_test.py` against %s." % evidence.get("repo"), "",
             "- Result: **%s**" % evidence.get("result"),
             "- Pull request: %s" % evidence.get("pr_url"),
             "- Started: %s" % evidence.get("started"),
             "- Finished: %s" % evidence.get("finished"), "",
             "## Server facts", "",
             "| Id | Claim | Observed | Ok | At |", "|---|---|---|---|---|"]
    for rec in evidence.get("records") or []:
        lines.append("| %s | %s | %s | %s | %s |" % (
            _cell(rec.get("id")), _cell(rec.get("claim")), _cell(rec.get("observed")),
            "yes" if rec.get("ok") else "no", _cell(rec.get("at"))))
    return "\n".join(lines) + "\n"


def report(opts, out):
    if not opts.evidence:
        sys.stderr.write("Error: report needs --evidence FILE\n")
        return EXIT_USAGE
    with open(opts.evidence) as handle:
        text = render_report(json.load(handle))
    if opts.output:
        with open(opts.output, "w") as handle:
            handle.write(text)
        out("wrote " + opts.output)
    else:
        out(text.rstrip("\n"))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="team_merge_test.py",
                                     description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="verb", required=True)
    for verb in ("preflight", "apply", "run", "report"):
        p = sub.add_parser(verb)
        p.add_argument("--repo", default=ALLOWED_REPO)
        p.add_argument("--root", default=os.getcwd(),
                       help="the unkannybanny clone (default: cwd)")
        if verb == "preflight":
            p.add_argument("--only", choices=["user", "repo"])
        if verb == "run":
            p.add_argument("--resume", action="store_true",
                           help="continue a run that stopped at b-push-dismisses")
            p.add_argument("--out",
                           help="directory the evidence.json is written into")
        if verb == "report":
            p.add_argument("--evidence")
            p.add_argument("--output", help="file to write (default: stdout)")
    return parser


def main(argv, gh=None, out=print, sleep=time.sleep):
    opts = build_parser().parse_args(argv)
    if opts.repo != ALLOWED_REPO:
        sys.stderr.write("Error: the driver is confined to %s, not %s\n"
                         % (ALLOWED_REPO, opts.repo))
        return EXIT_USAGE
    gh = gh or Gh()
    root = os.path.abspath(opts.root)
    if opts.verb == "preflight":
        return preflight(gh, opts.repo, opts.only, out)
    if opts.verb == "apply":
        return apply_rules(gh, opts.repo, root, out)
    if opts.verb == "run":
        if not opts.out:
            sys.stderr.write("Error: run needs --out DIR\n")
            return EXIT_USAGE
        say = lambda line: out(redact(line, gh.secrets()))
        return run_proof(gh, opts.repo, root, os.path.abspath(opts.out), say, sleep, resume=opts.resume)
    return report(opts, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
