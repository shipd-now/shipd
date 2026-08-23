#!/usr/bin/env python3
"""review_gate.py — publish an /s:review verdict to a GitHub pull request.

This is the mechanical half of the semantic-review gate: it consumes the
`/s:review --json` object and shapes GitHub payloads, but makes **no** findings
and assigns **no** severities of its own — the skill supplies the judgement.
Stdlib only. Every network call goes through an injectable `gh` command runner
so the logic is unit-testable without a network or a real repo.

Subcommands:
  post <pr> --from <json|->   upsert a summary comment, post anchored inline
       [--disposition <scope>] comments, and set a `semantic-review` commit
       [--model <tier>]        status on the PR's head SHA; the disposition
                              scope selects the status mapping and both
                              options are recorded in the summary
  reply <pr> <comment-id>     post a reply onto the finding thread rooted at
       --body <text>          the given review comment (REST in_reply_to)
  autoreply <pr>              post the canonical policy reply onto every
       --disposition <scope>  gate-authored, unreplied finding thread the
       [--body <text>]        scope covers, so `resolve` has its evidence
  resolve <pr> [--check]      resolve gate-authored threads carrying
                              disposition evidence (a reply, or a later
                              commit); --check counts unresolved gate threads
                              without mutating
  protect [--remove]          add (or remove) `semantic-review` in the default
                              branch's required status check contexts and the
                              conversation-resolution requirement, creating the
                              protection when the branch has none

The `gh` runner has signature ``gh(args, input=None) -> (rc, stdout, stderr)``
where ``args`` is everything after the ``gh`` executable.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys

PROG = "review_gate"
CONTEXT = "semantic-review"
# The event every review this poster submits carries. `COMMENT` deliberately,
# never `REQUEST_CHANGES`: the required `semantic-review` commit status set
# below is the merge-blocking signal, and a review decision would add a second
# block that a human must dismiss by hand even after the fix has landed. The
# review POST is the carrier for inline comments, not a gate of its own.
REVIEW_EVENT = "COMMENT"
MARKER = "<!-- shipd-semantic-review -->"
# The pre-rename marker. Every *read* still recognizes it — a PR whose summary
# predates the rename is edited in place, never duplicated — while every write
# emits MARKER only, so the old form retires as PRs are re-posted.
LEGACY_MARKER = "<!-- am-semantic-review -->"
# The ☕ brand line that opens the summary comment's visible body — the hidden
# MARKER above stays line 1 and unbranded, so upsert matching is untouched.
BRAND_LINE = "**☕ shipd** semantic review"

# Severity -> summary-table dot. These, the ✅/❌ verdict marker, and the ☕ of
# BRAND_LINE are the only emoji this script emits, mirroring the skill's three
# sanctioned sites.
_SEV_DOT = {"high": "\U0001F534", "medium": "\U0001F7E0", "low": "\U0001F7E1"}
_SEV_LABEL = {"high": "high", "medium": "med", "low": "low"}

# Disposition scopes — the review-stage option an invoker passes through. It
# selects the commit-status mapping only: the findings JSON and the rendered
# verdict stay severity-honest in every scope.
DISPOSITIONS = ("all", "high-only", "none")

# The scopes `autoreply` acts under, and the canonical reply each posts. `all`
# is absent by design: it means per-finding judgement, which is the skill's job.
AUTOREPLY_DISPOSITIONS = ("high-only", "none")
_AUTOREPLY_BODY = {
    "high-only": ("Auto-dispositioned by review policy (disposition: "
                  "high-only): below the acting threshold; not implemented."),
    "none": ("Auto-dispositioned by review policy (disposition: none): "
             "findings are recorded, not dispositioned individually."),
}

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

# GraphQL: list a PR's review threads (root-comment author, comment count,
# creation time, and body) plus the PR's commit dates and the authenticated
# viewer login, so `resolve` can pick gate-authored threads and judge
# disposition evidence, and `autoreply` can read each root's severity.
# Pagination beyond 100 threads/comments is out of scope (the same known cap as
# the poster's comment listing).
_THREADS_QUERY = """
query($owner:String!, $name:String!, $number:Int!) {
  viewer { login }
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      commits(last:100) { nodes { commit { committedDate } } }
      reviewThreads(first:100) {
        nodes {
          id
          isResolved
          comments(first:100) {
            nodes { databaseId author { login } createdAt body }
          }
        }
      }
    }
  }
}
"""

_RESOLVE_MUTATION = """
mutation($threadId:ID!) {
  resolveReviewThread(input:{threadId:$threadId}) { thread { isResolved } }
}
"""


class ReviewGateError(Exception):
    """A hard, run-blocking failure (a `gh` call the flow depends on failed)."""


def _noop(*_args, **_kwargs):
    pass


def _fail(msg):
    raise ReviewGateError(msg)


# --- default (production) gh seam ------------------------------------------

def _default_gh(args, input=None):
    proc = subprocess.run(
        ["gh"] + list(args), input=input, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


# --- diff anchoring ---------------------------------------------------------

def commentable_lines(patch):
    """RIGHT-side commentable line numbers of a unified-diff ``patch``.

    A line is commentable on the PR's RIGHT (new-file) side when it is present
    there — i.e. context (` `) and added (`+`) lines. Removed (`-`) lines have
    no new-file number and are skipped. Returns a set of new-file line numbers.
    """
    lines = set()
    new_line = None
    for row in (patch or "").splitlines():
        m = _HUNK_RE.match(row)
        if m:
            new_line = int(m.group(1))
            continue
        if new_line is None:
            continue
        if row.startswith("+"):
            lines.add(new_line)
            new_line += 1
        elif row.startswith("-"):
            continue  # left side only
        elif row.startswith("\\"):
            continue  # "\ No newline at end of file"
        else:  # context line
            lines.add(new_line)
            new_line += 1
    return lines


def _parse_location(location):
    """Split a ``path:LINE`` finding location into ``(path, line)`` or
    ``(None, None)`` when it is not an anchorable single-line reference."""
    if not location or ":" not in location:
        return None, None
    path, _, tail = location.rpartition(":")
    try:
        return path, int(tail)
    except ValueError:
        return None, None


def _split_findings(findings, commentable):
    """Partition ``findings`` into ``(anchored, unanchored)`` against the
    per-path ``commentable`` line sets. ``anchored`` items are
    ``(finding, path, line)`` tuples; ``unanchored`` is the raw findings."""
    anchored, unanchored = [], []
    for f in findings:
        path, line = _parse_location(f.get("location", ""))
        if path is not None and line in commentable.get(path, set()):
            anchored.append((f, path, line))
        else:
            unanchored.append(f)
    return anchored, unanchored


# --- rendering --------------------------------------------------------------

def status_state(verdict, findings=None, disposition="all"):
    """The `semantic-review` commit-status state under the acting ``disposition``
    scope — the one place merge policy acts on a review.

    ``all`` (the default): `success` iff the verdict is a clean pass.
    ``high-only``: `success` iff no finding carries severity `high` — the
    mediums and lows are auto-dispositioned, never implemented, so a red status
    over them would never clear. ``none``: always `success`; the honesty lives
    in the posted findings, not in a status nobody may act on.
    """
    if disposition == "none":
        return "success"
    if disposition == "high-only":
        highs = any((f.get("severity") == "high") for f in (findings or []))
        return "failure" if highs else "success"
    return "success" if verdict == "pass" else "failure"


def _verdict_header(verdict):
    if verdict == "pass":
        return "## Findings: ✅ Ship it"
    return "## Findings: ❌ Fix required"


def _detail_cell(f):
    loc = f.get("location") or ""
    what = (f.get("what") or "").replace("|", "\\|")
    return ("%s — %s" % (loc, what)).strip(" —")


def render_summary(review, unanchored, disposition="all", model=None):
    """Render the marker-tagged summary comment body: the ☕ brand line, the
    verdict header, effort, the policy provenance lines, the
    ``# | rating | details`` findings table, and an "Additional findings"
    section carrying the ``unanchored`` findings in full (they get no inline
    comment).

    The brand line opens the visible body — the hidden ``MARKER`` stays line 1
    and byte-identical, so upsert matching is unmoved.

    Provenance: a non-``all`` ``disposition`` adds a ``Disposition: <scope>``
    line so a green status over visible findings is explained on the PR, and a
    given ``model`` adds a ``Model: <tier>`` line recorded verbatim — symbolic
    tiers are never resolved here."""
    verdict = review.get("verdict")
    findings = review.get("findings") or []
    out = [MARKER, "", BRAND_LINE, "", _verdict_header(verdict), "",
           "Effort: %s/5" % review.get("effort", "?")]
    if disposition and disposition != "all":
        out.append("Disposition: %s" % disposition)
    if model:
        out.append("Model: %s" % model)
    out.append("")
    if findings:
        out.append("| # | rating | details |")
        out.append("| --- | --- | --- |")
        for i, f in enumerate(findings, 1):
            sev = f.get("severity", "low")
            rating = "%s %s" % (_SEV_DOT.get(sev, ""), _SEV_LABEL.get(sev, sev))
            out.append("| %d | %s | %s |" % (i, rating.strip(), _detail_cell(f)))
    else:
        out.append("No findings.")
    if unanchored:
        out += ["", "### Additional findings",
                "", "_Findings not anchored to a line in the PR diff:_", ""]
        for f in unanchored:
            sev = f.get("severity", "low")
            loc = f.get("location") or "(no location)"
            out.append("- **%s** [%s] — %s" % (loc, sev, f.get("what") or ""))
            why, fix = f.get("why"), f.get("fix")
            if why:
                out.append("  - Why: %s" % why)
            if fix:
                out.append("  - Fix: %s" % fix)
    return "\n".join(out) + "\n"


def has_gate_marker(body):
    """True when ``body`` carries this gate's hidden marker in either its
    current or its pre-rename form — the single read-side identification every
    marker lookup goes through, so no path recognizes one form and not the
    other."""
    text = body or ""
    return MARKER in text or LEGACY_MARKER in text


def _sev_marker(severity):
    """The marker an inline finding comment opens with. The renderer below and
    ``parse_severity`` both go through this one format, so the pair cannot
    drift — the tests cover the render → parse round trip."""
    return "**%s — " % severity


# The parser side of `_sev_marker`, derived from it via a sentinel so the
# literal format lives in exactly one place.
_SEV_MARKER_RE = re.compile(
    "^" + re.escape(_sev_marker("\x00")).replace(
        "\x00", "(%s)" % "|".join(_SEV_DOT)))


def parse_severity(body):
    """The severity of a gate-authored inline finding comment, read back from
    the marker ``_inline_body`` rendered, or ``None`` when ``body`` does not
    open with one (a human's comment, or a body this gate did not write)."""
    match = _SEV_MARKER_RE.match((body or "").lstrip())
    return match.group(1) if match else None


def _line_number(value):
    """True when ``value`` is a usable line number — an int, and not the bool
    that ``isinstance(True, int)`` would otherwise let through."""
    return isinstance(value, int) and not isinstance(value, bool)


def _suggestion(f, commentable=None):
    """The ``(start_line, end_line, lines)`` of a finding's committable
    suggestion, or ``None`` when it declares none or declares one this poster
    will not commit.

    The reviewer supplies the judgement in an optional ``suggestion`` object —
    ``{"confident": true, "start_line": n, "end_line": m, "lines": [...]}`` —
    and this is the whitelist it must pass. Anything else degrades to prose
    rather than failing: a wrong shape costs a suggestion, never a review.

    * ``confident`` must be exactly ``True``: the reviewer's own declaration
      that the fix is right, which is what a one-click apply rests on.
    * A ``start_column``/``end_column`` key declares an edit *inside* a line,
      which a whole-line suggestion cannot express.
    * ``start_line``/``end_line`` must be ints with ``start_line <= end_line``:
      one contiguous range is the only shape GitHub commits, so a missing or
      inverted bound is a discontiguous fix by another name.
    * ``lines`` must be a non-empty list of strings — the whole replacement
      lines. Its length need not match the range: a fix may add or remove
      lines.
    * Given a ``commentable`` set, every line in the range must be in it; a
      comment spanning a line the diff does not carry is rejected outright,
      which would cost the whole review POST. ``None`` skips that check.
    """
    sug = f.get("suggestion")
    if not isinstance(sug, dict) or sug.get("confident") is not True:
        return None
    if "start_column" in sug or "end_column" in sug:
        return None
    start, end = sug.get("start_line"), sug.get("end_line")
    if not (_line_number(start) and _line_number(end)) or start > end:
        return None
    lines = sug.get("lines")
    if not isinstance(lines, list) or not lines:
        return None
    if not all(isinstance(line, str) for line in lines):
        return None
    if commentable is not None and not all(
            n in commentable for n in range(start, end + 1)):
        return None
    return start, end, lines


def _inline_body(f, suggestion=None):
    """The text body of one anchored inline comment — the finding's what / why
    / fix as prose, followed by a committable ``suggestion`` fenced block when
    ``suggestion`` is the ``(start, end, lines)`` triple ``_suggestion``
    accepted for this finding. The prose and the leading severity marker are
    the same either way, so ``parse_severity`` reads a suggestion-carrying body
    exactly as it reads any other.

    No emoji."""
    sev = f.get("severity", "low")
    parts = [_sev_marker(sev) + "%s**" % (f.get("what") or "")]
    if f.get("why"):
        parts.append("")
        parts.append(f["why"])
    if f.get("fix"):
        parts.append("")
        parts.append("Fix: %s" % f["fix"])
    if suggestion:
        parts += ["", "```suggestion"] + list(suggestion[2]) + ["```"]
    return "\n".join(parts)


def _status_description(review, disposition="all"):
    findings = review.get("findings") or []
    verdict = review.get("verdict") or "unknown"
    suffix = ("" if not disposition or disposition == "all"
              else " (disposition %s)" % disposition)
    if not findings:
        return ("%s: no findings%s" % (verdict, suffix))[:140]
    counts = {"high": 0, "medium": 0, "low": 0}
    for f in findings:
        counts[f.get("severity", "low")] = counts.get(f.get("severity", "low"), 0) + 1
    parts = ["%d %s" % (counts[s], s) for s in ("high", "medium", "low")
             if counts.get(s)]
    return ("%s: %s%s" % (verdict, ", ".join(parts), suffix))[:140]


# --- gh interactions --------------------------------------------------------

def _resolve_pr(gh, pr):
    rc, out, err = gh(["pr", "view", str(pr),
                       "--json", "number,headRefOid,url"])
    if rc != 0:
        _fail("gh pr view %s failed: %s" % (pr, err.strip()))
    d = json.loads(out)
    return d["number"], d["headRefOid"], d.get("url")


def _resolve_repo(gh):
    rc, out, err = gh(["repo", "view", "--json", "nameWithOwner"])
    if rc != 0:
        _fail("gh repo view failed: %s" % err.strip())
    return json.loads(out)["nameWithOwner"]


def _default_branch(gh):
    rc, out, err = gh(["repo", "view", "--json", "defaultBranchRef"])
    if rc != 0:
        _fail("resolving default branch failed: %s" % err.strip())
    return json.loads(out)["defaultBranchRef"]["name"]


def _pr_files(gh, repo, number):
    rc, out, err = gh(["api",
                       "repos/%s/pulls/%d/files?per_page=100" % (repo, number)])
    if rc != 0:
        _fail("fetching PR files failed: %s" % err.strip())
    return json.loads(out or "[]")


def _upsert_summary(gh, repo, number, body):
    """Create the marker summary comment or edit the existing one in place — a
    comment carrying either the current or the legacy marker is *the* summary,
    so a pre-rename PR is edited rather than given a second one. Returns the
    comment's html_url."""
    rc, out, err = gh(["api",
                       "repos/%s/issues/%d/comments?per_page=100" % (repo, number)])
    comments = json.loads(out or "[]") if rc == 0 else []
    existing = next((c for c in comments if has_gate_marker(c.get("body"))), None)
    payload = json.dumps({"body": body})
    if existing:
        rc, out, err = gh(
            ["api", "repos/%s/issues/comments/%d" % (repo, existing["id"]),
             "-X", "PATCH", "--input", "-"], input=payload)
    else:
        rc, out, err = gh(
            ["api", "repos/%s/issues/%d/comments" % (repo, number),
             "-X", "POST", "--input", "-"], input=payload)
    if rc != 0:
        _fail("posting summary comment failed: %s" % err.strip())
    return json.loads(out or "{}").get("html_url")


def _set_status(gh, repo, sha, state, description, target_url):
    payload = json.dumps({"state": state, "context": CONTEXT,
                          "description": description,
                          "target_url": target_url or ""})
    rc, _out, err = gh(["api", "repos/%s/statuses/%s" % (repo, sha),
                        "-X", "POST", "--input", "-"], input=payload)
    if rc != 0:
        _fail("setting commit status failed: %s" % err.strip())


def _review_comment(f, path, line, commentable=None):
    """One inline comment payload for an anchored finding. A finding carrying
    a committable suggestion anchors on the range that suggestion replaces —
    GitHub applies a suggestion to the lines its comment spans — and a
    multi-line range takes the ``start_line``/``line`` pair; every other
    finding keeps its location-line anchor unchanged."""
    suggestion = _suggestion(f, commentable)
    comment = {"path": path, "side": "RIGHT",
               "body": _inline_body(f, suggestion)}
    if suggestion is None:
        comment["line"] = line
        return comment
    start, end, _lines = suggestion
    if start != end:
        comment["start_line"] = start
        comment["start_side"] = "RIGHT"
    comment["line"] = end
    return comment


def _post_review(gh, repo, number, sha, anchored, commentable=None):
    """Post one COMMENT review with the ``anchored`` inline comments, each
    carrying its finding's committable suggestion where ``commentable`` — the
    per-path RIGHT-side line sets ``post`` already computed — admits one.
    Returns True on success, False on rejection (e.g. a 422 from an
    un-anchorable line)."""
    comments = [
        _review_comment(f, p, ln,
                        None if commentable is None
                        else commentable.get(p, set()))
        for f, p, ln in anchored]
    body = ("Semantic review — see the summary comment for the full report."
            if comments else
            "Semantic review posted — see the summary comment.")
    payload = json.dumps({"commit_id": sha, "event": REVIEW_EVENT,
                          "body": body, "comments": comments})
    rc, _out, _err = gh(["api", "repos/%s/pulls/%d/reviews" % (repo, number),
                         "-X", "POST", "--input", "-"], input=payload)
    return rc == 0


def post(pr, review, gh, out=_noop, disposition="all", model=None):
    """Publish ``review`` (a parsed /s:review --json object) to pull request
    ``pr`` through the ``gh`` seam. ``disposition`` is the acting review-stage
    scope (see ``status_state``) and ``model`` the tier the reviewing session
    ran on, both recorded as provenance in the summary. Returns a small result
    dict."""
    number, sha, pr_url = _resolve_pr(gh, pr)
    repo = _resolve_repo(gh)
    files = _pr_files(gh, repo, number)
    commentable = {f.get("filename"): commentable_lines(f.get("patch") or "")
                   for f in files}
    findings = review.get("findings") or []
    anchored, unanchored = _split_findings(findings, commentable)

    comment_url = _upsert_summary(
        gh, repo, number,
        render_summary(review, unanchored, disposition, model))
    state = status_state(review.get("verdict"), findings, disposition)
    _set_status(gh, repo, sha, state,
                _status_description(review, disposition), comment_url)
    out("summary comment: %s" % (comment_url or "(created)"))

    if anchored:
        # ``commentable`` travels with the anchored findings: `_split_findings`
        # above stays the one decision on inline-vs-fold — an unanchorable
        # finding is already folded here, suggestion or not — and the same
        # sets it consulted then decide whether a suggestion's range is
        # committable, rather than a second anchoring pass over the diff.
        if not _post_review(gh, repo, number, sha, anchored, commentable):
            # The inline review was rejected: fold every finding into the
            # summary so nothing is lost, then retry the review with no inline.
            out("inline review rejected; folding findings into the summary")
            _upsert_summary(
                gh, repo, number,
                render_summary(review, findings, disposition, model))
            _post_review(gh, repo, number, sha, [])

    out("semantic-review status: %s" % state)
    return {"state": state, "summary_url": comment_url,
            "anchored": len(anchored), "unanchored": len(unanchored),
            "disposition": disposition}


def _enabled(value):
    """Normalize a protection field to a bool — GET returns ``{"enabled": ...}``
    for the toggle fields, while PUT expects a bare boolean."""
    if isinstance(value, dict):
        return bool(value.get("enabled"))
    return bool(value)


def _pr_reviews_put(value):
    """Translate a GET-shaped ``required_pull_request_reviews`` object into the
    subset the PUT accepts, or ``None`` when the field is unset."""
    if not value:
        return None
    body = {
        "dismiss_stale_reviews": bool(value.get("dismiss_stale_reviews")),
        "require_code_owner_reviews": bool(
            value.get("require_code_owner_reviews")),
        "required_approving_review_count": value.get(
            "required_approving_review_count", 0),
    }
    if "require_last_push_approval" in value:
        body["require_last_push_approval"] = bool(
            value.get("require_last_push_approval"))
    return body


def _restrictions_put(value):
    """Translate GET-shaped ``restrictions`` (users/teams/apps objects) into the
    PUT's login/slug lists, or ``None`` when unrestricted."""
    if not value:
        return None
    return {
        "users": [u.get("login") for u in value.get("users", [])],
        "teams": [t.get("slug") for t in value.get("teams", [])],
        "apps": [a.get("slug") for a in value.get("apps", [])],
    }


# Optional toggle fields that PUT accepts as bare booleans; carried through from
# the current protection when present so the write preserves them.
_PROTECTION_TOGGLES = (
    "required_linear_history", "allow_force_pushes", "allow_deletions",
    "block_creations", "required_signatures", "lock_branch",
    "allow_fork_syncing",
)


def _not_protected(err):
    """True when a protection read failed because the branch simply has no
    protection yet — the ``Branch not protected (HTTP 404)`` gh reports. Any
    other failure (a denial, a missing repository, a transport error) is a real
    read failure and must not be mistaken for "unprotected"."""
    text = (err or "").lower()
    return "branch not protected" in text and "http 404" in text


def _protection_put_body(current, contexts, conversation, strict_default=True):
    """Build the full-protection PUT body from the ``current`` GET object,
    setting the required-check ``contexts`` and the ``conversation`` resolution
    flag while preserving every other protection field (translated to the PUT's
    flatter shape). The four keys PUT requires are always present (nullable).
    ``strict_default`` is the ``strict`` used when ``current`` names none — the
    creation case, where false keeps auto-merged PRs off the update-branch
    treadmill."""
    rsc = current.get("required_status_checks") or {}
    body = {
        "required_status_checks": {
            "strict": bool(rsc.get("strict", strict_default)),
            "contexts": list(contexts),
        },
        "enforce_admins": _enabled(current.get("enforce_admins")),
        "required_pull_request_reviews": _pr_reviews_put(
            current.get("required_pull_request_reviews")),
        "restrictions": _restrictions_put(current.get("restrictions")),
        "required_conversation_resolution": conversation,
    }
    for field in _PROTECTION_TOGGLES:
        if field in current:
            body[field] = _enabled(current.get(field))
    return body


def protect(gh, remove=False, out=_noop):
    """Add (or with ``remove``, remove) the ``semantic-review`` required check
    **and** the ``required_conversation_resolution`` requirement on the default
    branch, preserving every other protection field. The pair is set together
    via the full-protection GET + PUT (conversation resolution has no
    sub-resource endpoint). An unprotected branch — whose read 404s — gains the
    minimal protection instead of failing: `semantic-review` required with
    ``strict`` false and conversation resolution on. A no-op when already in the
    desired state — exits zero and writes nothing. Returns
    ``{"changed": bool, "contexts": [...], "conversation_resolution": bool}``."""
    repo = _resolve_repo(gh)
    branch = _default_branch(gh)
    endpoint = "repos/%s/branches/%s/protection" % (repo, branch)
    rc, body, err = gh(["api", endpoint])
    if rc != 0:
        if not _not_protected(err):
            _fail("reading branch protection failed: %s" % err.strip())
        # No protection at all: create it from an empty current object rather
        # than failing, so a fresh repository can be gated in one call.
        current = {}
    else:
        current = json.loads(body or "{}")
    rsc = current.get("required_status_checks") or {}
    contexts = list(rsc.get("contexts") or [])
    present = CONTEXT in contexts
    conv_now = _enabled(current.get("required_conversation_resolution"))
    want_conv = not remove
    conv_label = "required" if want_conv else "not required"

    contexts_ok = (not present) if remove else present
    if contexts_ok and conv_now == want_conv:
        out("%s already %s on %s: contexts %s; conversation resolution %s"
            % (CONTEXT, "absent" if remove else "required", branch,
               ", ".join(contexts), conv_label))
        return {"changed": False, "contexts": contexts,
                "conversation_resolution": conv_now}

    if remove:
        contexts = [c for c in contexts if c != CONTEXT]
    elif not present:
        contexts = contexts + [CONTEXT]

    body_obj = _protection_put_body(current, contexts, want_conv,
                                    strict_default=bool(current))
    rc, _out, err = gh(["api", endpoint, "-X", "PUT", "--input", "-"],
                       input=json.dumps(body_obj))
    if rc != 0:
        _fail("updating branch protection failed: %s" % err.strip())
    out("%s branch protection on %s: contexts %s; conversation resolution %s"
        % ("relaxed" if remove else "updated", branch,
           ", ".join(contexts), conv_label))
    return {"changed": True, "contexts": contexts,
            "conversation_resolution": want_conv}


# --- finding-thread disposition (reply + resolve) ---------------------------

def _as_utc(stamp):
    """Parse an ISO-8601 stamp into an aware datetime, or ``None`` when empty
    or unparsable. GraphQL mixes formats: ``DateTime`` fields (a thread's
    ``createdAt``) are UTC ``Z`` strings while ``GitTimestamp`` fields
    (``committedDate``) keep the commit's local UTC offset, so evidence
    comparisons must go through parsed datetimes, never the raw strings."""
    if not stamp:
        return None
    try:
        return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _comment_id_int(comment_id):
    """Coerce ``comment_id`` to an int, failing with the CLI's one-line
    diagnostic rather than a traceback on non-numeric input."""
    try:
        return int(comment_id)
    except (TypeError, ValueError):
        _fail("invalid comment id %r" % (comment_id,))


def _post_reply(gh, repo, number, comment_id, body):
    """Create a threaded reply under review comment ``comment_id`` via the REST
    ``in_reply_to`` create. Returns the new comment's html_url; a rejected
    create (unknown comment id) raises."""
    payload = json.dumps({"body": body, "in_reply_to": _comment_id_int(comment_id)})
    rc, body_out, err = gh(
        ["api", "repos/%s/pulls/%d/comments" % (repo, number),
         "-X", "POST", "--input", "-"], input=payload)
    if rc != 0:
        _fail("posting reply to comment %s failed: %s"
              % (comment_id, err.strip()))
    return json.loads(body_out or "{}").get("html_url")


def reply(pr, comment_id, body, gh, out=_noop):
    """Post ``body`` as a reply onto the finding thread rooted at review comment
    ``comment_id`` on pull request ``pr``, through the ``gh`` seam. Uses the REST
    ``in_reply_to`` create so the reply threads under the gate's comment. Returns
    ``{"url": <html_url>}``; a rejected create (unknown comment id) raises."""
    number, _sha, _url = _resolve_pr(gh, pr)
    repo = _resolve_repo(gh)
    url = _post_reply(gh, repo, number, comment_id, body)
    out("reply posted: %s" % (url or "(created)"))
    return {"url": url}


def _graphql(gh, query, **variables):
    """Run a GraphQL ``query`` through the ``gh`` seam with typed ``variables``
    (ints as ``-F``, strings as ``-f``); return the parsed ``data`` object."""
    args = ["api", "graphql", "-f", "query=%s" % query]
    for key, value in variables.items():
        flag = "-F" if isinstance(value, int) else "-f"
        args += [flag, "%s=%s" % (key, value)]
    rc, out_s, err = gh(args)
    if rc != 0:
        _fail("GraphQL query failed: %s" % err.strip())
    return json.loads(out_s or "{}").get("data") or {}


def _list_review_threads(gh, repo, number):
    """Return ``(viewer_login, commit_dates, threads)`` for pull request
    ``number``. Each thread is ``{"id", "isResolved", "comments"}`` where
    ``comments`` is the ordered list of
    ``{"databaseId", "author", "createdAt", "body"}`` (author being the
    login)."""
    owner, _, name = repo.partition("/")
    data = _graphql(gh, _THREADS_QUERY, owner=owner, name=name, number=int(number))
    viewer = (data.get("viewer") or {}).get("login")
    pull = ((data.get("repository") or {}).get("pullRequest") or {})
    commit_dates = [
        (n.get("commit") or {}).get("committedDate")
        for n in ((pull.get("commits") or {}).get("nodes") or [])]
    commit_dates = [d for d in commit_dates if d]
    threads = []
    for node in ((pull.get("reviewThreads") or {}).get("nodes") or []):
        comments = [
            {"databaseId": c.get("databaseId"),
             "author": (c.get("author") or {}).get("login"),
             "createdAt": c.get("createdAt"),
             "body": c.get("body") or ""}
            for c in ((node.get("comments") or {}).get("nodes") or [])]
        threads.append({"id": node.get("id"),
                        "isResolved": bool(node.get("isResolved")),
                        "comments": comments})
    return viewer, commit_dates, threads


def _resolve_thread(gh, thread_id):
    _graphql(gh, _RESOLVE_MUTATION, threadId=thread_id)


def resolve(pr, gh, check=False, out=_noop):
    """Resolve gate-authored review threads on ``pr`` that carry disposition
    evidence — a reply on the thread, or a commit landed after the thread was
    created. Gate-authored means the root comment's author is the authenticated
    viewer (the account the gate posts as); human-authored threads are never
    touched. Undispositioned gate threads are listed, left unresolved, and make
    the verb non-zero. ``check`` mutates nothing and only counts unresolved
    gate threads. Prints ``unresolved=<n>`` and returns a result dict."""
    number, _sha, _url = _resolve_pr(gh, pr)
    repo = _resolve_repo(gh)
    viewer, commit_dates, threads = _list_review_threads(gh, repo, number)

    gate_threads = [t for t in threads
                    if t["comments"] and t["comments"][0]["author"] == viewer]
    unresolved = [t for t in gate_threads if not t["isResolved"]]

    if check:
        n = len(unresolved)
        out("unresolved=%d" % n)
        return {"unresolved": n, "check": True,
                "resolved": [], "undispositioned": []}

    commit_stamps = [c for c in map(_as_utc, commit_dates)
                     if c is not None]
    resolved, undispositioned = [], []
    for t in unresolved:
        root = t["comments"][0]
        has_reply = len(t["comments"]) >= 2
        created = _as_utc(root["createdAt"])
        later_commit = created is not None and any(
            c > created for c in commit_stamps)
        if has_reply or later_commit:
            _resolve_thread(gh, t["id"])
            resolved.append(t["id"])
            out("resolved %s" % t["id"])
        else:
            undispositioned.append(t["id"])
            out("undispositioned (no reply, no later commit): %s" % t["id"])
    out("unresolved=%d" % len(undispositioned))
    return {"unresolved": len(undispositioned), "check": False,
            "resolved": resolved, "undispositioned": undispositioned}


def autoreply(pr, gh, disposition, body=None, out=_noop):
    """Post the canonical policy reply onto the gate-authored finding threads a
    cheapened review never dispositions individually, so ``resolve`` finds its
    evidence without per-finding judgement.

    A thread is eligible when it is unresolved, rooted at a comment authored by
    the authenticated viewer (the account the gate posts as — human threads are
    never touched), and carries no reply yet, which makes re-runs idempotent.
    Under ``high-only`` only ``medium``/``low`` roots are replied to: ``high``
    findings are the ones the flow still acts on, and a root whose severity
    cannot be parsed is left for judgement and reported. Under ``none``
    severity is not consulted and every eligible thread is replied to.

    Returns ``{"replied": n, "threads": [...], "unparsed": [...]}``."""
    if disposition not in AUTOREPLY_DISPOSITIONS:
        _fail("autoreply needs disposition %s, got %r"
              % (" or ".join(AUTOREPLY_DISPOSITIONS), disposition))
    number, _sha, _url = _resolve_pr(gh, pr)
    repo = _resolve_repo(gh)
    viewer, _commit_dates, threads = _list_review_threads(gh, repo, number)
    text = body or _AUTOREPLY_BODY[disposition]

    replied, unparsed = [], []
    for t in threads:
        comments = t["comments"]
        if t["isResolved"] or not comments:
            continue
        root = comments[0]
        if root["author"] != viewer:
            continue                      # human-authored: never touched
        if len(comments) > 1:
            continue                      # already dispositioned
        if disposition == "high-only":
            severity = parse_severity(root.get("body"))
            if severity is None:
                unparsed.append(t["id"])
                out("unparsed severity, left for judgment: %s" % t["id"])
                continue
            if severity == "high":
                continue
        _post_reply(gh, repo, number, root["databaseId"], text)
        replied.append(t["id"])
        out("replied %s" % t["id"])
    out("replied=%d" % len(replied))
    return {"replied": len(replied), "threads": replied, "unparsed": unparsed}


# --- CLI --------------------------------------------------------------------

def _load_review(src):
    if src == "-":
        return json.loads(sys.stdin.read())
    with open(src, encoding="utf-8") as fh:
        return json.load(fh)


def _cmd_post(args, gh):
    review = _load_review(args.from_)
    result = post(args.pr, review, gh, out=lambda m: print(m, file=sys.stderr),
                  disposition=args.disposition, model=args.model)
    print(json.dumps(result))
    return 0


def _cmd_reply(args, gh):
    result = reply(args.pr, args.comment_id, args.body, gh,
                   out=lambda m: print(m, file=sys.stderr))
    print(json.dumps(result))
    return 0


def _cmd_autoreply(args, gh):
    # ``replied=<n>`` goes to stdout so a driving flow can read the count.
    autoreply(args.pr, gh, args.disposition, body=args.body, out=print)
    return 0


def _cmd_resolve(args, gh):
    # The human/greppable lines (including ``unresolved=<n>``) go to stdout so
    # callers — the skill flow and the autopilot grade — can read the count.
    result = resolve(args.pr, gh, check=args.check, out=print)
    return 0 if result["unresolved"] == 0 else 1


def _cmd_protect(args, gh):
    result = protect(gh, remove=args.remove,
                     out=lambda m: print(m, file=sys.stderr))
    print(json.dumps(result))
    return 0


def main(argv=None, gh=None):
    gh = gh or _default_gh
    parser = argparse.ArgumentParser(prog=PROG, description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("post", help="publish a review verdict to a PR")
    p.add_argument("pr", help="PR number, URL, or branch")
    p.add_argument("--from", dest="from_", required=True,
                   help="path to the /s:review --json object, or - for stdin")
    p.add_argument("--disposition", choices=DISPOSITIONS, default="all",
                   help="review-stage disposition scope selecting the commit "
                        "status mapping (default: all)")
    p.add_argument("--model", default=None,
                   help="the model tier the reviewing session ran on, recorded "
                        "verbatim in the summary comment")
    p.set_defaults(func=_cmd_post)

    rp = sub.add_parser("reply", help="reply onto a finding thread")
    rp.add_argument("pr", help="PR number, URL, or branch")
    rp.add_argument("comment_id", help="the review comment id rooting the thread")
    rp.add_argument("--body", required=True, help="the reply text")
    rp.set_defaults(func=_cmd_reply)

    ar = sub.add_parser(
        "autoreply", help="post the canonical policy reply onto the gate "
                          "threads a disposition scope does not judge")
    ar.add_argument("pr", help="PR number, URL, or branch")
    ar.add_argument("--disposition", choices=AUTOREPLY_DISPOSITIONS,
                    required=True,
                    help="the acting disposition scope (high-only replies to "
                         "medium/low roots; none replies to every gate thread)")
    ar.add_argument("--body", default=None,
                    help="override the canonical policy reply text")
    ar.set_defaults(func=_cmd_autoreply)

    rs = sub.add_parser(
        "resolve", help="resolve gate-authored threads carrying disposition "
                        "evidence")
    rs.add_argument("pr", help="PR number, URL, or branch")
    rs.add_argument("--check", action="store_true",
                    help="count unresolved gate threads without mutating")
    rs.set_defaults(func=_cmd_resolve)

    pr = sub.add_parser(
        "protect", help="require (or --remove) semantic-review on the "
                        "default branch")
    pr.add_argument("--remove", action="store_true",
                    help="remove the context instead of adding it")
    pr.set_defaults(func=_cmd_protect)

    args = parser.parse_args(argv)
    try:
        return args.func(args, gh)
    except ReviewGateError as exc:
        sys.stderr.write("%s: %s\n" % (PROG, exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
