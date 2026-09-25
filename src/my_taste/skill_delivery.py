from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mcp_types as types
from mcp.server.extension import Extension, MethodBinding
from mcp.shared.exceptions import MCPError

_SKILL_NAME = "my-taste"
_SERVER_NAMESPACE = "my-taste"
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)


class SkillsListParams(types.RequestParams):
    cursor: str | None = None


class SkillsGetParams(types.RequestParams):
    uri: str


@dataclass(frozen=True)
class SkillResource:
    relative_path: str
    uri: str
    text: str
    digest: str


def _skill_root() -> Path:
    packaged = Path(__file__).resolve().parent / "skill_bundle"
    if (packaged / "SKILL.md").is_file():
        return packaged

    source_tree = Path(__file__).resolve().parents[2] / "skills" / _SKILL_NAME
    if (source_tree / "SKILL.md").is_file():
        return source_tree

    raise RuntimeError("Bundled My Taste skill files are missing.")


def _parse_frontmatter(text: str) -> dict[str, Any]:
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise RuntimeError("SKILL.md is missing YAML front matter.")

    frontmatter: dict[str, Any] = {}
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise RuntimeError(f"Unsupported SKILL.md front matter line: {raw_line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]
        frontmatter[key] = value

    if frontmatter.get("name") != _SKILL_NAME:
        raise RuntimeError(
            f"SKILL.md name must be {_SKILL_NAME!r}, got {frontmatter.get('name')!r}."
        )
    if not frontmatter.get("description"):
        raise RuntimeError("SKILL.md front matter must include a description.")
    return frontmatter


def _digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _uri(relative_path: str) -> str:
    return f"skill://{_SERVER_NAMESPACE}/{_SKILL_NAME}/{relative_path}"


def load_skill_resources() -> tuple[dict[str, Any], tuple[SkillResource, ...]]:
    root = _skill_root()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        raise RuntimeError("My Taste skill contains no files.")

    resources: list[SkillResource] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        if relative.startswith("../") or "/../" in relative:
            raise RuntimeError(f"Unsafe skill resource path: {relative}")
        text = path.read_text(encoding="utf-8")
        resources.append(
            SkillResource(
                relative_path=relative,
                uri=_uri(relative),
                text=text,
                digest=_digest(text),
            )
        )

    by_path = {resource.relative_path: resource for resource in resources}
    manifest = by_path.get("SKILL.md")
    if manifest is None:
        raise RuntimeError("My Taste skill is missing SKILL.md.")

    frontmatter = _parse_frontmatter(manifest.text)
    return frontmatter, tuple(resources)


class SkillsExtension(Extension):
    identifier = "io.modelcontextprotocol/skills"

    def __init__(self) -> None:
        self.frontmatter, self.resources_manifest = load_skill_resources()
        self.catalog_uri = _uri("SKILL.md")
        self.resource_text = {
            resource.uri: resource.text for resource in self.resources_manifest
        }
        self.entry = {
            "uri": self.catalog_uri,
            "frontmatter": self.frontmatter,
            "resources": [
                {"uri": resource.uri, "digest": resource.digest}
                for resource in self.resources_manifest
            ],
        }

    def settings(self) -> dict[str, Any]:
        return {}

    def methods(self) -> tuple[MethodBinding, ...]:
        return (
            MethodBinding(
                method="skills/list",
                params_type=SkillsListParams,
                handler=self._list_skills,
            ),
            MethodBinding(
                method="skills/get",
                params_type=SkillsGetParams,
                handler=self._get_skill,
            ),
        )

    async def _list_skills(
        self,
        _ctx: Any,
        _params: SkillsListParams,
    ) -> dict[str, object]:
        return {"skills": [self.entry]}

    async def _get_skill(
        self,
        _ctx: Any,
        params: SkillsGetParams,
    ) -> dict[str, object]:
        if params.uri != self.catalog_uri:
            raise MCPError(
                code=types.INVALID_PARAMS,
                message=f"Unknown skill URI: {params.uri}",
            )
        return {"skill": self.entry}


def register_skill_resources(server: Any, extension: SkillsExtension) -> None:
    for resource in extension.resources_manifest:
        def reader(text: str = resource.text) -> str:
            return text

        reader.__name__ = "read_skill_" + re.sub(
            r"[^A-Za-z0-9_]+",
            "_",
            resource.relative_path,
        )
        server.resource(
            resource.uri,
            name=f"My Taste: {resource.relative_path}",
            mime_type="text/markdown",
        )(reader)
