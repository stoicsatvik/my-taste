from __future__ import annotations

import hashlib

from my_taste.skill_delivery import SkillsExtension, load_skill_resources


def test_skill_bundle_has_complete_manifest():
    frontmatter, resources = load_skill_resources()

    assert frontmatter["name"] == "my-taste"
    assert frontmatter["description"]
    paths = {resource.relative_path for resource in resources}
    assert paths == {
        "SKILL.md",
        "references/style-fingerprints.md",
        "references/tool-contract.md",
    }


def test_skill_resource_digests_match_utf8_content():
    _, resources = load_skill_resources()

    for resource in resources:
        expected = "sha256:" + hashlib.sha256(resource.text.encode("utf-8")).hexdigest()
        assert resource.digest == expected


def test_skill_extension_advertises_complete_catalog_entry():
    extension = SkillsExtension()

    assert extension.identifier == "io.modelcontextprotocol/skills"
    assert extension.catalog_uri == "skill://my-taste/my-taste/SKILL.md"
    assert extension.entry["frontmatter"]["name"] == "my-taste"
    assert len(extension.entry["resources"]) == 3
    assert set(extension.resource_text) == {
        row["uri"] for row in extension.entry["resources"]
    }


def test_actual_mcp_server_registers_skill_extension_and_resources():
    from my_taste.mcp_server import mcp, skill_extension

    assert skill_extension.identifier == "io.modelcontextprotocol/skills"
    assert mcp._lowlevel_server.get_request_handler("skills/list") is not None
    assert mcp._lowlevel_server.get_request_handler("skills/get") is not None
