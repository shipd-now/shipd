#!/usr/bin/env python3
"""report — a tiny CLI that prints a fixed table of rows to stdout."""

ROWS = [
    ("alice", 30, "engineering"),
    ("bob", 41, "sales"),
    ("carol", 25, "design"),
]


def main():
    print("name    age  team")
    for name, age, team in ROWS:
        print("%-6s  %3d  %s" % (name, age, team))


if __name__ == "__main__":
    main()
