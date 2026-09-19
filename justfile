# Display all recipes
[default]
_list:
    @ {{just_executable()}} --list --justfile {{justfile()}} --unsorted

# Run tests
[group: 'Testing']
test *args:
    uv run pytest {{args}}

# Lint and type-check code
[group: 'Linting & Formatting']
lint:
    uv run ruff check
    uv run pyright

# Format code
[group: 'Linting & Formatting']
format:
    uv run ruff format .

# Preview the documentation locally (builds the API reference first)
[group: 'Documentation']
docs:
    just docs-build-api
    uv run --group doc quarto preview docs --port 4200

# Build the API reference pages
[group: 'Documentation']
docs-build-api:
    PYTHONPATH=src uv run python scripts/gen_quarto_api.py

# Build the full documentation, including the API reference pages
[group: 'Documentation']
docs-build:
    just docs-build-api
    uv run --group doc quarto render docs

# View the documentation locally
[group: 'Documentation']
view-docs:
    uv run --group doc quarto preview docs --port 4200
