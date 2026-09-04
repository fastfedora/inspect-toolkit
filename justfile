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
