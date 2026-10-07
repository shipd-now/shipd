# New-code checks

The skill reads this file when reviewing whether a new function, class, guard, or helper meets its own stated purpose.

For every new code introduced by the diff, judge it against its documented contract — do not wave it through because it is new rather than modified. Five checks below, with worked examples of real findings and reflexes.

## Wrong quantity measured

A limit, cap, or check that measures the wrong thing (bytes where the guarantee is about lines, wall time where it is about CPU time) looks correct and is not.

- **Real finding.** A new function enforces a line limit by counting bytes: `if (bytes > limit)` when the docstring promises "line count ≤ limit" — the check measures the wrong dimension.
- **Reflex, not worth reporting.** A new function counts bytes as intended and the docstring correctly describes the byte limit.

Rates on the existing high/medium/low rubric — no floor.

## Escape hatch lapsing the guarantee

A flag, default, or fallback branch that quietly steps around the very invariant the code exists to enforce.

- **Real finding.** A new validation function returns `true` on error by default when the flag `skip_validation` is set, silently bypassing the check its caller relies on.
- **Reflex, not worth reporting.** A new validation function correctly implements the check and error paths follow documented expectations.

Rates on the existing high/medium/low rubric — no floor.

## Termination on hostile input

Does the routine terminate — and cheaply — on empty, oversized, malformed, or adversarial input, not only the input the happy-path test exercises?

- **Real finding.** A new parser reads a user-supplied message byte-by-byte in a loop without a length limit or timeout, allowing an attacker to send an infinitely long message and block the thread.
- **Reflex, not worth reporting.** A new parser bounds its loop with `len(input)` or a reasonable timeout, protecting against both empty and oversized input.

Rates on the existing high/medium/low rubric — no floor.

## Boundary agreement

Off-by-one and inclusive/exclusive edges: does the code's actual boundary match the one its doc comment or name claims?

- **Real finding.** A new slice or loop is documented as `[start, end)` (exclusive end) but the code implements `[start, end]` (inclusive), causing off-by-one errors in every caller.
- **Reflex, not worth reporting.** A new slice correctly implements the documented inclusive or exclusive boundary, and the code matches the comment.

Rates on the existing high/medium/low rubric — no floor.

## Doc comment versus code

Where the new code carries a doc comment or docstring, confirm it describes what the code actually does, not what it was meant to do.

- **Real finding.** A new function's docstring promises "returns the user's email address" but the code actually returns their username, and the caller relies on the documented contract.
- **Reflex, not worth reporting.** The docstring accurately describes the function's actual behavior, including edge cases and error conditions.

Rates on the existing high/medium/low rubric — no floor.
