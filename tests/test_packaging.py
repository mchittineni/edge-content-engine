"""
Packaging tests.

The container smoke test caught two real defects: a wheel built without any
source, and agent subdirectories that were not importable packages. Both were
invisible to an editable install, which is what local development uses.
These tests fail on the cheap side of that feedback loop.
"""

import pathlib
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENT_DIRS = sorted(
    d for d in (REPO_ROOT / "agents").iterdir() if d.is_dir() and (d / "agent.py").exists()
)


@pytest.mark.parametrize("agent_dir", AGENT_DIRS, ids=lambda d: d.name)
def test_agent_subpackage_has_init(agent_dir: pathlib.Path) -> None:
    """
    Without __init__.py these are namespace dirs, which setuptools excludes
    (namespaces = false). The wheel then ships agents/ with no agents in it.
    """
    assert (agent_dir / "__init__.py").exists(), (
        f"agents/{agent_dir.name}/__init__.py is missing; it will be omitted from the wheel"
    )


def test_every_agent_dir_is_discoverable() -> None:
    assert len(AGENT_DIRS) >= 12, "expected the full agent roster"


def test_declared_python_matches_ruff_target() -> None:
    """A ruff target below requires-python would allow syntax the project cannot run."""
    cfg = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())

    requires = cfg["project"]["requires-python"].lstrip(">=").strip()
    major, minor = (int(part) for part in requires.split(".")[:2])

    ruff_target = cfg["tool"]["ruff"]["target-version"]  # e.g. "py313"
    digits = ruff_target.removeprefix("py")
    ruff_version = (int(digits[0]), int(digits[1:]))

    assert ruff_version == (major, minor), (
        f"requires-python {requires} and ruff target-version {ruff_target} disagree"
    )

    mypy_version = cfg["tool"]["mypy"]["python_version"]
    assert mypy_version == f"{major}.{minor}", (
        f"requires-python {requires} and mypy python_version {mypy_version} disagree"
    )
