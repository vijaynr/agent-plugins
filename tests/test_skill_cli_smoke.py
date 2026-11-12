from __future__ import annotations

import ast
import shutil
import sys
from pathlib import Path

import pytest


PYTHON_HELP_SCRIPT_NAMES = [
    "plugins/okf/skills/okf-toolkit/scripts/okf_cli.py",
    "plugins/blackduck/skills/blackduck/scripts/blackduck_token.py",
    "plugins/gitlab/skills/gitlab/scripts/gitlab_token.py",
    "plugins/octane/skills/alm-octane/scripts/octane_token.py",
    "plugins/octane/skills/alm-octane/scripts/octane_url.py",
]

UV_HELP_SCRIPT_NAMES = [
    "plugins/blackduck/skills/blackduck/scripts/blackduck_vulnerabilities.py",
    "plugins/gitlab/skills/gitlab/scripts/gitlab_cli.py",
    "plugins/octane/skills/alm-octane/scripts/octane_client.py",
]

OCTANE_GENERIC_COMMANDS = (
    "get-entity-types", "get-entity-field-metadata", "get-filter-metadata",
    "get-entities", "get-entity", "create-entity", "update-entity",
    "get-favorite", "list-favorite-items",
)

COMPATIBILITY_TARGETS = {
    "blackduck": (3, 10),
    "gitlab": (3, 10),
    "octane": (3, 10),
}

TOKEN_HELP_CONTRACT = {
    "okf_cli.py": ("init", "ingest", "validate", "export"),
    "blackduck_token.py": ("--profile", "--no-activate", "profiles", "use-profile", "delete-profile", "defaults", "save", "get", "delete", "setup", "--show", "--skip-test", "--write-secret-to-env"),
    "gitlab_token.py": ("--profile", "--no-activate", "profiles", "use-profile", "delete-profile", "defaults", "save", "get", "delete", "setup", "--show", "--skip-test", "--write-secret-to-env"),
    "octane_token.py": ("--profile", "--no-activate", "profiles", "use-profile", "delete-profile", "defaults", "save", "get", "delete", "setup", "--show", "--skip-test", "--write-secret-to-env"),
    "octane_url.py": ("--profile", "get-favorite", "list-favorite-items", "--page-size", "--max-items"),
}

THIRD_PARTY_IMPORTS = {
    "defusedxml",
    "dotenv",
    "keyring",
    "openpyxl",
    "PIL",
    "requests",
}


def script_paths(repo_root: Path, names: list[str]) -> list[Path]:
    return [repo_root / name for name in names]


def assert_pep723_dependencies(path: Path, relpath) -> None:
    text = path.read_text(encoding="utf-8")
    assert "# /// script" in text and "dependencies" in text, (
        f"{relpath(path)} lacks PEP 723 dependency metadata"
    )


@pytest.mark.parametrize(
    "script_name",
    PYTHON_HELP_SCRIPT_NAMES + UV_HELP_SCRIPT_NAMES,
    ids=PYTHON_HELP_SCRIPT_NAMES + UV_HELP_SCRIPT_NAMES,
)
def test_skill_cli_script_compiles(repo_root: Path, script_name: str):
    path = repo_root / script_name

    compile(path.read_text(encoding="utf-8"), str(path), "exec")


@pytest.mark.parametrize("script_name", PYTHON_HELP_SCRIPT_NAMES, ids=PYTHON_HELP_SCRIPT_NAMES)
def test_dependency_free_skill_cli_scripts_show_help(repo_root: Path, run_command, script_name: str):
    path = repo_root / script_name
    result = run_command([sys.executable, str(path), "--help"], check=False)

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "usage:" in output.lower()
    for retained_option in TOKEN_HELP_CONTRACT[path.name]:
        assert retained_option in output, f"{script_name} help omitted {retained_option}"


@pytest.mark.parametrize("script_name", UV_HELP_SCRIPT_NAMES, ids=UV_HELP_SCRIPT_NAMES)
def test_dependency_backed_skill_cli_scripts_show_help_or_declare_pep723_metadata(
    repo_root: Path,
    run_command,
    relpath,
    script_name: str,
):
    path = repo_root / script_name
    uv = shutil.which("uv")

    if uv:
        result = run_command([uv, "run", f"scripts/{path.name}", "--help"], cwd=path.parents[1], check=False)
        output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        assert "usage:" in output.lower()
        assert "--profile" in output, f"{script_name} help is not profile-aware"
        if path.name == "octane_client.py":
            for command in OCTANE_GENERIC_COMMANDS:
                assert command in output, f"Octane help omitted {command}"
    else:
        assert_pep723_dependencies(path, relpath)


def test_skill_scripts_parse_with_their_declared_minimum_python_grammar(repo_root: Path):
    errors: list[str] = []
    for plugin, feature_version in COMPATIBILITY_TARGETS.items():
        for path in sorted((repo_root / "plugins" / plugin).glob("skills/*/scripts/*.py")):
            try:
                ast.parse(
                    path.read_text(encoding="utf-8"),
                    filename=str(path),
                    feature_version=feature_version,
                )
            except SyntaxError as exc:
                errors.append(f"{path.relative_to(repo_root)} is not Python {feature_version[0]}.{feature_version[1]} syntax: {exc}")

    assert not errors, "\n".join(errors)


def test_scripts_with_third_party_imports_declare_pep723_metadata(repo_root: Path, relpath):
    errors: list[str] = []
    for path in sorted(repo_root.glob("plugins/*/skills/*/scripts/*.py")):
        text = path.read_text(encoding="utf-8")
        imports_dependency = any(
            f"import {module}" in text or f"from {module}" in text
            for module in THIRD_PARTY_IMPORTS
        )
        if imports_dependency and "# /// script" not in text:
            errors.append(f"{relpath(path)} imports a third-party package but lacks PEP 723 metadata")

    assert not errors, "\n".join(errors)
