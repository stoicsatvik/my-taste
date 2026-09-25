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
