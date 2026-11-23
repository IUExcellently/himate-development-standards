"""四端都使用原生用户 Skill，入口与规范正文分开。"""
import json
import os
from pathlib import Path
import shutil
import re
import sys

from local_state import NAME

PLATFORMS = {
    "codex": (".agents", ("codex",)),
    "claude": (".claude", ("claude",)),
    "kiro": (".kiro", ("kiro-cli", "kiro")),
    "qoder": (".qoder", ("qodercli",)),
}


def config_root(local, platform):
    relative, _ = PLATFORMS[platform]
    if platform == "claude" and local.home == Path.home().resolve():
        configured = os.environ.get("CLAUDE_CONFIG_DIR")
        if configured:
            return Path(configured).expanduser()
    return local.home / relative


def entry(local, platform):
    return config_root(local, platform) / "skills" / NAME / "SKILL.md"


def detected(local):
    return {platform: config_root(local, platform).is_dir()
            or any(shutil.which(executable) for executable in executables)
            for platform, (_, executables) in PLATFORMS.items()}


def legacy_targets(local):
    codex = local.home / ".codex"
    if local.home == Path.home().resolve() and os.environ.get("CODEX_HOME"):
        codex = Path(os.environ["CODEX_HOME"]).expanduser()
    return {
        "codex": codex / "AGENTS.md",
        "claude": config_root(local, "claude") / "CLAUDE.md",
        "kiro": local.home / ".kiro" / "steering" / f"{NAME}.md",
    }


def wrapper(bundle, template):
    # 本地路径是数据参数，入口要求客户端按参数边界调用。
    paths = {"BODY": str(bundle / "SKILL.md"),
             "DETECT": str(bundle / "scripts" / "detect_project.py")}
    if any(any(ord(ch) < 32 or ch == "`" for ch in p) for p in paths.values()):
        raise ValueError("发行路径包含不适合写入 Skill 导航的字符")
    return re.sub(r"@@(BODY|DETECT)@@", lambda m: json.dumps(paths[m[1]], ensure_ascii=False),
                  template.decode("utf-8")).encode("utf-8")


def environment(local):
    return {"python": list(sys.version_info[:3]), "git": shutil.which("git") is not None,
            "platforms": detected(local)}
