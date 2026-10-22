#!/usr/bin/env python3
"""room_claim — one review per pull request head, claimed through a GitHub ref.

Reviewer runners of one agent can run on several machines and compete for the
same head. Before a ``reviewer`` or ``ci`` turn a runner creates
``refs/shipd/claims/pr-<N>/<agent>/<sha>/<gen>`` through the GitHub API;
GitHub creates a ref only once, so exactly one runner wins each generation.
The winner moves its claim ref to a new claim commit every minute (the
heartbeat); GitHub stamps each commit with its own clock, so ages are always
the response ``Date`` header minus the commit's ``committer.date``, never a
local clock. A custom ref has no compare-and-swap on update, so only the
create decides a winner and a takeover always creates the next generation.

Every GitHub call goes through the ``gh(args, input=None) -> (rc, out, err)``
seam the room scripts use. Standard library only.
"""

import calendar
import email.utils
import json
import os
import socket
import sys
import threading
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import room  # noqa: E402

CLAIM_ENV = "SHIPD_ROOM_CLAIM"
BEAT_SECONDS = 60
LEASE_SECONDS = 600
FENCE_SECONDS = 300
MESSAGE_PREFIX = "shipd-claim "
LIVE_STATES = ("claimed", "beat")

_HOLDER = []


def claim_prefix(number, agent, sha):
    """The ref path (without ``refs/``) of every generation of one claim."""
    return "shipd/claims/pr-%d/%s/%s" % (number, agent.replace("/", "_"), sha)


def holder_id():
    """``<hostname>:<pid>:<8 hex>``, computed once per runner process."""
    if not _HOLDER:
        _HOLDER.append("%s:%d:%s" % (socket.gethostname(), os.getpid(),
                                     uuid.uuid4().hex[:8]))
    return _HOLDER[0]


def _commit_message(holder, state, agent, sha):
    return MESSAGE_PREFIX + json.dumps(
        {"holder": holder, "state": state, "agent": agent, "sha": sha},
        separators=(",", ":"), sort_keys=True)


def _parse_message(message):
    """The claim dict in a claim commit message; ``{}`` for anything else."""
    if not isinstance(message, str) or \
            not message.startswith(MESSAGE_PREFIX):
        return {}
    try:
        data = json.loads(message[len(MESSAGE_PREFIX):])
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _parse_date(text):
    """Epoch seconds of a GitHub ISO-8601 ``...Z`` timestamp."""
    return float(calendar.timegm(time.strptime(text, "%Y-%m-%dT%H:%M:%SZ")))


class Claim:
    """One won claim: the generation ref a runner holds."""

    FIELDS = ("repo", "number", "agent", "sha", "gen", "holder", "tree",
              "tip", "last_beat")

    def __init__(self, repo, number, agent, sha, gen, holder, tree="",
                 tip="", last_beat=0.0):
        self.repo = repo
        self.number = number
        self.agent = agent
        self.sha = sha
        self.gen = gen
        self.holder = holder
        self.tree = tree
        self.tip = tip
        self.last_beat = last_beat

    @property
    def prefix(self):
        return claim_prefix(self.number, self.agent, self.sha)

    @property
    def ref(self):
        return "refs/%s/%d" % (self.prefix, self.gen)

    def to_env(self):
        return json.dumps({k: getattr(self, k) for k in self.FIELDS},
                          sort_keys=True)

    @classmethod
    def from_env(cls, text):
        try:
            data = json.loads(text)
            return cls(**{k: data[k] for k in cls.FIELDS})
        except (ValueError, KeyError, TypeError):
            raise room.RoomError("%s is not a valid claim" % CLAIM_ENV)


# ---------------------------------------------------------------------------
# GitHub calls
# ---------------------------------------------------------------------------

def _fail(what, err, rc):
    return room.RoomError("%s failed: %s" % (what, (err or "").strip()
                                             or "exit %d" % rc))


def _json(gh, args, what, input=None):
    rc, out, err = gh(list(args), input=input)
    if rc != 0:
        raise _fail(what, err, rc)
    try:
        return json.loads(out or "null")
    except ValueError as exc:
        raise room.RoomError("%s returned invalid JSON: %s" % (what, exc))


def server_now(gh, repo):
    """GitHub's current time (epoch seconds), from the ``Date`` header of
    one ``gh api -i`` call."""
    rc, out, err = gh(["api", "-i", "repos/%s" % repo])
    if rc != 0:
        raise _fail("reading GitHub's clock", err, rc)
    for line in (out or "").splitlines():
        if not line.strip():
            break
        name, _sep, value = line.partition(":")
        if name.strip().lower() == "date":
            try:
                return email.utils.parsedate_to_datetime(
                    value.strip()).timestamp()
            except (TypeError, ValueError):
                break
    raise room.RoomError("GitHub's response carried no readable Date header")


def _generations(gh, repo, prefix):
    """``[(gen, ref, tip_sha)]`` under ``prefix`` ascending by generation."""
    data = _json(gh, ["api", "repos/%s/git/matching-refs/%s/" % (repo, prefix)],
                 "listing claim refs")
    found = []
    for item in data if isinstance(data, list) else []:
        ref = item.get("ref") if isinstance(item, dict) else None
        obj = item.get("object") if isinstance(item, dict) else None
        sha = obj.get("sha") if isinstance(obj, dict) else None
        tail = ref.rsplit("/", 1)[-1] if isinstance(ref, str) else ""
        if tail.isdigit() and isinstance(sha, str):
            found.append((int(tail), ref, sha))
    return sorted(found)


def _read_commit(gh, repo, sha):
    """``(info, tree, committed_at)`` of a claim commit."""
    data = _json(gh, ["api", "repos/%s/git/commits/%s" % (repo, sha)],
                 "reading claim commit %s" % sha[:7])
    data = data if isinstance(data, dict) else {}
    tree = (data.get("tree") or {}).get("sha", "")
    try:
        when = _parse_date((data.get("committer") or {}).get("date"))
    except (TypeError, ValueError):
        raise room.RoomError("claim commit %s has no readable date"
                             % sha[:7])
    return _parse_message(data.get("message")), tree, when


def _create_commit(gh, repo, message, tree, parents):
    data = _json(gh, ["api", "-X", "POST", "repos/%s/git/commits" % repo,
                      "--input", "-"], "creating a claim commit",
                 input=json.dumps({"message": message, "tree": tree,
                                   "parents": list(parents)}))
    try:
        return data["sha"], _parse_date(data["committer"]["date"])
    except (KeyError, TypeError, ValueError):
        raise room.RoomError("creating a claim commit returned no sha/date")


def _is_exists(rc, out, err):
    text = ((err or "") + (out or "")).lower()
    return rc != 0 and ("422" in text or "already exists" in text)


def _verdict(gh, repo, number, agent, sha, holder):
    """The ``acquire`` outcome from the newest generation under the claim
    prefix: ``(kind, info, newest_gen)`` where kind is ``none``, ``done``,
    ``open`` (released or stale) or ``held``."""
    gens = _generations(gh, repo, claim_prefix(number, agent, sha))
    if not gens:
        return "none", {}, 0
    gen, _ref, tip = gens[-1]
    info, _tree, when = _read_commit(gh, repo, tip)
    who = {"holder": info.get("holder", "unknown"), "gen": gen}
    state = info.get("state")
    if state == "done":
        return "done", who, gen
    if state == "released":
        return "open", who, gen
    if server_now(gh, repo) - when > LEASE_SECONDS:
        return "open", who, gen
    return "held", who, gen


def acquire(gh, repo, number, agent, sha, holder):
    """Try to claim ``sha``: ``("won", Claim)``, ``("held", info)`` or
    ``("done", info)``; ``info`` names the holder and generation."""
    kind, info, newest = _verdict(gh, repo, number, agent, sha, holder)
    if kind in ("done", "held"):
        return kind, info
    gen = newest + 1
    tree = _read_commit_tree(gh, repo, sha)
    commit, when = _create_commit(
        gh, repo, _commit_message(holder, "claimed", agent, sha), tree, [])
    ref = "refs/%s/%d" % (claim_prefix(number, agent, sha), gen)
    rc, out, err = gh(["api", "-X", "POST", "repos/%s/git/refs" % repo,
                       "--input", "-"],
                      input=json.dumps({"ref": ref, "sha": commit}))
    if rc == 0:
        return "won", Claim(repo, number, agent, sha, gen, holder, tree,
                            commit, when)
    if not _is_exists(rc, out, err):
        raise _fail("creating claim ref %s" % ref, err, rc)
    kind, info, _newest = _verdict(gh, repo, number, agent, sha, holder)
    return ("done" if kind == "done" else "held"), info


def _read_commit_tree(gh, repo, sha):
    data = _json(gh, ["api", "repos/%s/git/commits/%s" % (repo, sha)],
                 "reading head commit %s" % sha[:7])
    tree = ((data or {}).get("tree") or {}).get("sha") \
        if isinstance(data, dict) else None
    if not tree:
        raise room.RoomError("head commit %s has no readable tree"
                             % sha[:7])
    return tree


def beat(gh, claim, state="beat"):
    """Move the claim ref to a new claim commit in ``state``."""
    commit, when = _create_commit(
        gh, claim.repo,
        _commit_message(claim.holder, state, claim.agent, claim.sha),
        claim.tree, [claim.tip] if claim.tip else [])
    rc, _out, err = gh(["api", "-X", "PATCH", "repos/%s/git/%s" % (
        claim.repo, claim.ref), "--input", "-"],
        input=json.dumps({"sha": commit, "force": True}))
    if rc != 0:
        raise _fail("moving claim ref %s" % claim.ref, err, rc)
    claim.tip, claim.last_beat = commit, when


def tip_state(gh, claim):
    """``(info, committed_at)`` of the claim ref's current tip commit."""
    for gen, _ref, tip in _generations(gh, claim.repo, claim.prefix):
        if gen == claim.gen:
            info, _tree, when = _read_commit(gh, claim.repo, tip)
            return info, when
    raise room.RoomError("claim ref %s is gone" % claim.ref)


def fence(gh, claim):
    """Raise ``RoomError`` unless ``claim`` is still the newest generation,
    held by its holder, with a heartbeat under ``FENCE_SECONDS`` old; then
    beat."""
    gens = _generations(gh, claim.repo, claim.prefix)
    if any(gen > claim.gen for gen, _r, _t in gens):
        raise room.RoomError("a newer claim generation exists")
    tip = next((t for gen, _r, t in gens if gen == claim.gen), None)
    if tip is None:
        raise room.RoomError("claim ref %s is gone" % claim.ref)
    info, _tree, when = _read_commit(gh, claim.repo, tip)
    if info.get("holder") != claim.holder or \
            info.get("state") not in LIVE_STATES:
        raise room.RoomError("the claim is held by %s in state %s" % (
            info.get("holder"), info.get("state")))
    if server_now(gh, claim.repo) - when >= FENCE_SECONDS:
        raise room.RoomError("the claim's last heartbeat is over %d seconds "
                             "old" % FENCE_SECONDS)
    beat(gh, claim)


class Heartbeat:
    """A daemon thread that beats ``claim`` every ``interval`` seconds until
    ``stop()``. A failed beat warns and the thread keeps trying; a claim
    already marked ``done`` or ``released`` is left alone."""

    def __init__(self, gh, claim, interval=BEAT_SECONDS):
        self.gh = gh
        self.claim = claim
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def _loop(self):
        while not self._stop.wait(self.interval):
            try:
                info, _when = tip_state(self.gh, self.claim)
                if info.get("state") not in LIVE_STATES:
                    return
                beat(self.gh, self.claim)
            except room.RoomError as exc:
                sys.stderr.write("warning: claim heartbeat failed: %s\n"
                                 % exc)

    def stop(self):
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join()


def can_claim(gh, repo):
    """Whether the acting account has push permission on ``repo``."""
    data = _json(gh, ["api", "repos/%s" % repo], "reading %s" % repo)
    perms = data.get("permissions") if isinstance(data, dict) else None
    return bool(isinstance(perms, dict) and perms.get("push") is True)


def require_push(gh, repo, login):
    """Refuse a reviewer or ci runner whose account cannot create refs."""
    if not can_claim(gh, repo):
        raise room.RoomError(
            "@%s cannot create review claims on %s (it needs push "
            "permission); a reviewer runner needs them to guarantee one "
            "review" % (login, repo))


def delete_pr_claims(gh, repo, number):
    """Delete every claim ref of pull request ``number``; returns the count.
    Errors raise ``RoomError``."""
    data = _json(gh, ["api", "repos/%s/git/matching-refs/shipd/claims/pr-%d/"
                      % (repo, number)], "listing claim refs")
    count = 0
    for item in data if isinstance(data, list) else []:
        ref = item.get("ref") if isinstance(item, dict) else None
        if not isinstance(ref, str) or not ref.startswith("refs/"):
            continue
        rc, _out, err = gh(["api", "-X", "DELETE",
                            "repos/%s/git/%s" % (repo, ref)])
        if rc != 0:
            raise _fail("deleting claim ref %s" % ref, err, rc)
        count += 1
    return count


def set_status(gh, repo, sha, agent, state, description):
    """Set the ``room-review/<agent>`` commit status on ``sha``."""
    rc, _out, err = gh(["api", "-X", "POST", "repos/%s/statuses/%s" % (
        repo, sha), "--input", "-"], input=json.dumps({
            "state": state, "context": "room-review/%s" % agent,
            "description": description}))
    if rc != 0:
        raise _fail("setting the room-review status", err, rc)


def claimed_turn(gh, repo, number, agent, head, run):
    """Run ``run()`` only when this runner wins the claim on ``head``.
    Returns ``("ran", result)``, ``("held", None)`` or ``("done", None)``."""
    if not head:
        sys.stderr.write("room run: #%d head is unreadable; skipping\n"
                         % number)
        return "held", None
    outcome, got = acquire(gh, repo, number, agent, head, holder_id())
    if outcome == "held":
        sys.stderr.write("room run: #%d head %s is claimed by %s; skipping\n"
                         % (number, head[:7], got.get("holder")))
        return "held", None
    if outcome == "done":
        sys.stderr.write("room run: #%d head %s was already reviewed by %s\n"
                         % (number, head[:7], got.get("holder")))
        return "done", None
    claim = got
    beater = None
    try:
        os.environ[CLAIM_ENV] = claim.to_env()
        set_status(gh, repo, head, agent, "pending",
                   "claimed for %s" % head[:7])
        beater = Heartbeat(gh, claim).start()
        result = run()
    finally:
        if beater is not None:
            beater.stop()
        os.environ.pop(CLAIM_ENV, None)
        _release(gh, claim)
    return "ran", result


def _release(gh, claim):
    """Mark an unfinished claim ``released``; never raises."""
    try:
        info, _when = tip_state(gh, claim)
        if info.get("state") != "done":
            beat(gh, claim, "released")
            set_status(gh, claim.repo, claim.sha, claim.agent, "pending",
                       "released; waiting for a runner")
    except room.RoomError as exc:
        sys.stderr.write("warning: could not release the claim: %s\n" % exc)
