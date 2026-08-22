from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

_SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    instructions: str
    path: Path


def load_skill(path: Path) -> Skill:
    """Load the subset of the Agent Skills format needed by this exercise."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} 缺少 YAML frontmatter 起始分隔符")

    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError(f"{path} 缺少 YAML frontmatter 结束分隔符") from exc

    metadata: dict[str, str] = {}
    for line in lines[1:closing_index]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, value = stripped.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("'\"")

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    instructions = "\n".join(lines[closing_index + 1 :]).strip()

    if not _SKILL_NAME.fullmatch(name):
        raise ValueError(f"Skill name {name!r} 不符合 Agent Skills 命名规范")
    if path.parent.name != name:
        raise ValueError(f"Skill name {name!r} 必须与目录名 {path.parent.name!r} 一致")
    if not description:
        raise ValueError("Skill description 不能为空")
    if not instructions:
        raise ValueError("Skill instructions 不能为空")

    return Skill(
        name=name,
        description=description,
        instructions=instructions,
        path=path,
    )


def default_skill_path() -> Path:
    configured = os.getenv("AGENT_SKILL_PATH")
    if configured:
        return Path(configured).expanduser().resolve()

    relative = Path("skills") / "workshop-planner" / "SKILL.md"
    candidates = (
        Path.cwd() / relative,
        Path(__file__).resolve().parents[2] / relative,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"找不到 workshop-planner Skill；已检查: {searched}")
