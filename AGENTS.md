# Agents Custom Instructions

## Project Guidelines

This project uses modern Python development practices with specific tooling requirements.

## Python Development

- **Always use `uv`** for Python package management and script execution
- Use `uv run` for executing Python scripts instead of direct python calls
- Use `uv add` for adding dependencies instead of pip install
- Use `uv sync` for installing dependencies from pyproject.toml

## Code Quality

- Always run `uv ruff check` after editing any Python files
- Fix any ruff issues before proceeding
- Use ruff for both linting and formatting (replaces black + flake8)
- DO NOT add `noqa` comments to fix linter errors - fix the underlying issue instead

## Git Workflow

- **Always run `pre-commit run -a`** before committing changes
- Ensure all pre-commit hooks pass before suggesting commits
- Fix any pre-commit failures before proceeding
- YOU MUST NEVER use `--no-verify` with git commit

## Script Headers

For Python scripts, use this shebang and dependency format:

```python
#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "package1",
#   "package2"
# ]
# ///
```

## Test suite

- Run the full test suite with `uv run pytest`
- Use pytest library for writing unit and integration tests
- Use free functions for tests instead of classes
- Run individual tests with `uv run pytest -k test_function_name`
- When iterating on a test, use `uv run pytest --last-failed` to run only the last failed test

## Code Style

- Code architecture must follow SOLID principles
- Prefer modern Python features (3.13+)
- Use type hints for function parameters and return values
- Use pathlib.Path instead of os.path for file operations
- Use f-strings for string formatting
- Keep functions focused and well-documented

## Commands to Remember

Before committing:

```bash
uv run ruff check --fix
pre-commit run -a
```

Running scripts:

```bash
uv run script_name.py
```

Adding dependencies:

```bash
uv add package_name
```

## Script Entrypoints

- When adding or modifying script entrypoints in `[project.scripts]` (pyproject.toml), update the "Available CLI
  scripts" section in README.md accordingly

## Error Handling

- Always check for file existence before operations
- Use specific exception types rather than bare except clauses
- Provide helpful error messages that guide users toward resolution
