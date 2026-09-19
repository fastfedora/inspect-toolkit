import json
import os
import sys
import yaml
from pathlib import Path


# only execute if a reference doc is in the inputs
input_files = os.getenv("QUARTO_PROJECT_INPUT_FILES", "")
if "reference/index.qmd" not in input_files:
    exit(0)

# Add src and filter directories to path so we can import the package and shared modules
project_root = Path(__file__).resolve().parents[3]
src_dir = project_root / "src"
filter_dir = str(Path(__file__).resolve().parent)
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if filter_dir not in sys.path:
    sys.path.insert(0, filter_dir)

from documented_symbols import documented_functions_and_classes  # noqa: E402

# The public-API reference pages: (section label / api package, page doc path).
reference_pages = [
    ("inspect_toolkit.metrics", "reference/metrics.qmd"),
    ("inspect_toolkit.scorers", "reference/scorers.qmd"),
    ("inspect_toolkit.solvers", "reference/solvers.qmd"),
    ("inspect_toolkit.solvers.exports", "reference/solvers/exports.qmd"),
    ("inspect_toolkit.solvers.imports", "reference/solvers/imports.qmd"),
    ("inspect_toolkit.solvers.diffs", "reference/solvers/diffs.qmd"),
    ("inspect_toolkit.tools", "reference/tools.qmd"),
    ("inspect_toolkit.datasets.sources", "reference/datasets.qmd"),
    ("inspect_toolkit.fixtures", "reference/fixtures.qmd"),
    ("inspect_toolkit.utils.coding", "reference/utils/coding.qmd"),
    ("inspect_toolkit.utils.collections", "reference/utils/collections.qmd"),
    ("inspect_toolkit.utils.databases", "reference/utils/databases.qmd"),
    ("inspect_toolkit.utils.eval", "reference/utils/eval.qmd"),
    ("inspect_toolkit.utils.evals", "reference/utils/evals.qmd"),
    ("inspect_toolkit.utils.filesystem", "reference/utils/filesystem.qmd"),
    ("inspect_toolkit.utils.format", "reference/utils/format.qmd"),
    ("inspect_toolkit.utils.math", "reference/utils/math.qmd"),
    ("inspect_toolkit.utils.parse", "reference/utils/parse.qmd"),
    ("inspect_toolkit.utils.sandbox", "reference/utils/sandbox.qmd"),
]


def build_sidebar() -> None:
    """Build the sidebar for the reference documentation."""
    sidebar = yaml.safe_load(
      """
website:
  sidebar:
    - title: Reference
      style: docked
      collapse-level: 1
      contents:
        - reference/index.qmd
      """
    )
    api_contents, index_json = _generate_api_sidebar_contents()
    sidebar["website"]["sidebar"][0]["contents"].extend(api_contents)

    docs_dir = project_root / "docs"
    index_file = docs_dir / "reference/refs.json"
    with open(index_file, "w") as f:
        json.dump(index_json, f, indent=2)

    sidebar_yaml = yaml.dump(sidebar, sort_keys=False).strip()
    sidebar_file = docs_dir / "reference/_sidebar.yml"
    if sidebar_file.exists():
        previous_sidebar_yaml = sidebar_file.read_text().strip()
    else:
        previous_sidebar_yaml = ""

    if sidebar_yaml != previous_sidebar_yaml:
        sidebar_file.write_text(sidebar_yaml + "\n", encoding="utf-8")


def _generate_api_sidebar_contents() -> tuple[list[dict], dict[str, str]]:
    """Build one docked sidebar section per public-API page by introspecting the package."""
    contents: list[dict] = []
    index: dict[str, str] = {}
    docs_dir = project_root / "docs"

    for module_name, doc in reference_pages:
        if not (docs_dir / doc).exists():
            continue

        refs = _function_and_class_sidebar_refs(module_name, doc)
        for ref in refs:
            index[ref["text"]] = ref["href"].removeprefix("reference/")

        contents.append(dict(section=_section_label(doc), href=doc, contents=refs))

    return contents, index


def _section_label(doc: str) -> str:
    """Display label for a reference page, e.g. 'reference/utils/coding.qmd' -> 'utils.coding'."""
    return doc.removeprefix("reference/").removesuffix(".qmd").replace("/", ".")


def _function_and_class_sidebar_refs(module_name: str, doc: str) -> list[dict[str, str]]:
    """Sidebar links for every public symbol documented on this API page."""
    try:
        pairs = documented_functions_and_classes(module_name)
    except Exception as error:
        print(
            f"Warning: Could not list documented API symbols for {module_name}: {error}",
            file=sys.stderr,
        )
        return []
    return [dict(text=name, href=f"{doc}#{anchor}") for name, anchor in pairs]


build_sidebar()
