"""Retired Lemon Squeezy setup helper.

Lemon Squeezy was abandoned for AI NOWA on 2026-05-18.  Keep this module as a
safe tombstone so old runbooks fail closed instead of creating stale checkout
URLs or reviving the wrong product.
"""


def main() -> None:
    raise SystemExit(
        "Lemon Squeezy is retired. Use Polar/intent-flow tooling and "
        "company/kpi_observations.md for current revenue state."
    )


if __name__ == "__main__":
    main()
