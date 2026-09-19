#!/usr/bin/env python3
"""
Generate Quarto API reference pages using custom `api` fenced blocks that our
reference filter expands into module documentation.

Usage:
  PYTHONPATH=src uv run python scripts/gen_quarto_api.py

One page is generated per public package: the top-level component packages under
``docs/reference/``, the solver subpackages under ``docs/reference/solvers/`` and the utility
subpackages under ``docs/reference/utils/``. Each page's title is the package path with the
``inspect_toolkit.`` prefix trimmed (e.g. ``utils.coding``); the api block keeps the fully-qualified
package. The reference landing page (``docs/reference/index.qmd``) is maintained by hand.
"""
from __future__ import annotations

import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "docs" / "reference"

# Top-level component pages under docs/reference/, as (filename stem, api package). The page title
# is the stem; the api package usually matches ``inspect_toolkit.<stem>``, except ``datasets`` whose
# public API lives in the ``datasets.sources`` subpackage (``datasets`` itself is a namespace).
TOP_LEVEL = [
    ("metrics", "inspect_toolkit.metrics"),
    ("scorers", "inspect_toolkit.scorers"),
    ("solvers", "inspect_toolkit.solvers"),
    ("tools", "inspect_toolkit.tools"),
    ("datasets", "inspect_toolkit.datasets.sources"),
    ("fixtures", "inspect_toolkit.fixtures"),
]

# Solver subpackages (the child export/import/diff solvers), one page each under
# docs/reference/solvers/.
SOLVERS = [
    "exports",
    "imports",
    "diffs",
]

# Utility subpackages, one page each under docs/reference/utils/.
UTILS = [
    "coding",
    "collections",
    "databases",
    "eval",
    "evals",
    "filesystem",
    "format",
    "math",
    "parse",
    "sandbox",
]

TEMPLATE = """---
title: {title}
---

```api
package: {package}
source: src
members: true
inherited: false
```
"""


def write_page(path: pathlib.Path, title: str, package: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.format(title=title, package=package), encoding="utf-8")


def main() -> None:
    for name, package in TOP_LEVEL:
        write_page(REFERENCE_DIR / f"{name}.qmd", name, package)

    for name in SOLVERS:
        package = f"inspect_toolkit.solvers.{name}"
        write_page(REFERENCE_DIR / "solvers" / f"{name}.qmd", f"solvers.{name}", package)

    for name in UTILS:
        package = f"inspect_toolkit.utils.{name}"
        write_page(REFERENCE_DIR / "utils" / f"{name}.qmd", f"utils.{name}", package)


if __name__ == "__main__":
    main()
