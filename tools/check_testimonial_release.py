#!/usr/bin/env python3
"""Run the public static-manifest testimonial release assertion."""

from __future__ import annotations

import sys

from build_static import StaticBuildError, build_manifest
from testimonial_gate import load_testimonial_release


def main() -> int:
    try:
        drafts, released = load_testimonial_release()
        manifest = build_manifest()
    except (OSError, RuntimeError, StaticBuildError, UnicodeError) as exc:
        print(f"testimonial release check failed: {exc}", file=sys.stderr)
        return 1
    ratings = sum(1 for item in released.values() if item["show_rating"])
    print(
        "testimonial release check passed — "
        f"{len(drafts)} drafts preserved; {len(released)} quotes and {ratings} ratings released; "
        f"{len(manifest)} public files checked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
