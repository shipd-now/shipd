# Call-site tracing

The skill reads this file when a changed signature, constant, guard, or helper needs chasing from the diff out to the call sites that reach it — the detail behind the downstream-impact and call-site-value steps, whose check names stay inline in `SKILL.md`.

## Downstream impact

Run `context <symbol>` for any changed function, type, or message signature, then weigh each match:

- **Untouched callers.** Callers that appear in `context` but **not** in the diff are your highest-value findings: code the user changed a contract for but did not update.
- **Every match is a candidate.** Treat each as a candidate to verify, never as "safe." The lookup is best-effort grep, not a complete call graph. Unmatched files are *not* proven unaffected — say so rather than implying coverage you do not have.
- **`--lang` misses extensionless scripts.** It filters by extension, so retry without it before concluding there are no references.
- **Changed constants are contract changes.** A changed limit, bound, timeout, retry count, buffer size, or threshold is not a stylistic tweak — it changes what callers can rely on. Chase every consumer of the changed constant through `context <symbol>` exactly as you would a changed signature.
- **Uneven sibling sites.** When the diff touches two or more parallel implementations of the same thing (sibling handlers, mirrored engines, duplicated validation), compare them against each other, not only against the base. Name any hardening, guard, or edge-case handling applied to one and not the other.

## Call-site values — reachability and comment accuracy

Do not judge a new branch, guard, or helper in isolation — follow the actual argument each call site passes in:

- **Unreachable guard / dead branch.** A defensive branch the real call can never hit. Flag it as dead code, and never describe it in the walkthrough as if it executes.
- **Comment / intent vs. actual behaviour.** A comment that promises behaviour the code does not produce, given how it is actually called, is wrong even though the line it sits on exists.

Both are usually low severity alone, but they compound. Whenever you quote a mechanism in the walkthrough, confirm the path that reaches it actually runs with the values the call sites supply.
