"""Hygiene tests for the mkdocs documentation site config."""

from pathlib import Path

import pytest

try:
    import yaml
    _HAVE_YAML = True
except ImportError:
    _HAVE_YAML = False


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_mkdocs_yml_exists():
    assert (REPO_ROOT / "mkdocs.yml").exists()


@pytest.mark.skipif(not _HAVE_YAML, reason="pyyaml not installed")
def test_mkdocs_yml_is_valid_yaml():
    with open(REPO_ROOT / "mkdocs.yml") as fh:
        config = yaml.safe_load(fh)
    assert config["site_name"] == "FusionFlow"
    assert config["theme"]["name"] == "material"
    assert "nav" in config


@pytest.mark.skipif(not _HAVE_YAML, reason="pyyaml not installed")
def test_mkdocs_nav_references_existing_files():
    """Every file referenced in the nav must exist under docs/."""
    with open(REPO_ROOT / "mkdocs.yml") as fh:
        config = yaml.safe_load(fh)
    docs_dir = REPO_ROOT / "docs"

    def _collect_files(nav_entry):
        files = []
        if isinstance(nav_entry, str):
            files.append(nav_entry)
        elif isinstance(nav_entry, dict):
            for value in nav_entry.values():
                files.extend(_collect_files(value))
        elif isinstance(nav_entry, list):
            for item in nav_entry:
                files.extend(_collect_files(item))
        return files

    for rel_path in _collect_files(config["nav"]):
        assert (docs_dir / rel_path).exists(), f"nav references missing doc: {rel_path}"


def test_docs_index_exists():
    assert (REPO_ROOT / "docs" / "index.md").exists()


def test_docs_index_has_install_instructions():
    text = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    assert "pip install fusionflow" in text
