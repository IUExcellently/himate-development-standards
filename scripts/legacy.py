"""显式迁移 V2 本机登记与经回执验证的旧入口。"""
import base64
from pathlib import Path

from integrations import PLATFORMS, entry, legacy_targets
from local_state import NAME, digest, encode, inside, read, read_json

MARKER = b"<!-- BEGIN HIMATE DEVELOPMENT STANDARDS -->"
END = b"<!-- END HIMATE DEVELOPMENT STANDARDS -->"


def merge_registration(local, folder, plan, incoming=None):
    manifest = read_json(folder / "manifest.json")
    if manifest is None or manifest.get("schema_version") != 1:
        raise ValueError("迁移源必须是原有 V2 本机规范目录")
    project = manifest["project"]
    if not isinstance(project["roots"], list) or not all(
        isinstance(root, str) and Path(root).is_absolute() for root in project["roots"]
    ):
        raise ValueError("V2 登记格式无效")
    current = read(local.registry)
    registry = local.registrations() if incoming is None else incoming
    registry["roots"] = list(dict.fromkeys(
        registry["roots"] + [str(Path(root).resolve()) for root in project["roots"]]
    ))
    legacy = {key: value for key, value in manifest.items()
              if key not in {"schema_version", "version", "root", "project", "base", "backend", "tags"}}
    legacy["project"] = {k: v for k, v in project.items() if k not in {"name", "roots", "signatures"}}
    previous = registry.setdefault("legacy", [])
    if not isinstance(previous, list):
        raise ValueError("已有自定义 legacy 字段。请先审查迁移配置")
    if legacy not in previous:
        previous.append(legacy)
    plan.add(local.registry, current, encode(registry))


def remove_legacy(local, folder, plan, selected):
    state = folder / ".install-state"
    if state.is_symlink():
        raise ValueError("旧回执目录属于链接")
    target = local.state / "legacy-backup.json"
    previous = read_json(target, {})
    backups = dict(previous)
    legacy_paths = legacy_targets(local)
    for platform in PLATFORMS:
        receipt = read_json(state / f"{platform}.json", {"installed": False, "files": {}})
        if not receipt["installed"]:
            continue
        if backups.get(platform) == receipt:
            # 已提交的迁移可能随后被正常卸载，旧源及回执保留用于审计。
            continue
        if platform in backups:
            raise ValueError(f"旧回执与已完成迁移不一致：{platform}")
        if platform not in selected:
            raise ValueError(f"仍有活动 V2 入口，需一并迁移或先按 V2 流程卸载：{platform}")
        expected = {
            "codex": ((entry(local, "codex"), "SKILL.md"),
                      (legacy_paths["codex"], "AGENTS.fragment.md")),
            "claude": ((entry(local, "claude"), "SKILL.md"),
                       (legacy_paths["claude"], "CLAUDE.fragment.md")),
            "kiro": ((legacy_paths["kiro"], f"{NAME}.md"),),
            "qoder": ((entry(local, "qoder"), "SKILL.md"),),
        }[platform]
        if set(receipt["files"]) != {str(path) for path, _ in expected}:
            raise ValueError(f"旧回执落点不受支持：{platform}")
        for path, filename in expected:
            record = receipt["files"][str(path)]
            inside(path, local.home)
            if filename == "SKILL.md" and path.parent.is_dir() and set(path.parent.iterdir()) != {path}:
                raise ValueError(f"旧 Skill 目录含未知文件：{path.parent}")
            existing = read(path)
            adapter = read(folder / "integrations" / platform / filename)
            if adapter is None:
                raise ValueError(f"旧适配模板缺失：{platform}/{filename}")
            original = record["original"]
            restored = None if original is None else base64.b64decode(original, validate=True)
            computed = adapter
            if filename.endswith(".fragment.md") and (adapter.count(MARKER), adapter.count(END)) != (1, 1):
                raise ValueError("旧全局片段边界不明确")
            if restored is not None:
                if not filename.endswith(".fragment.md") or MARKER in restored or END in restored:
                    raise ValueError("旧入口原始内容归属不明确")
                sep = b"\r\n" if b"\r\n" in restored else b"\n"
                computed = restored + sep * 2 + adapter.replace(b"\n", sep)
            if existing != computed or digest(existing) != record["installed_sha256"]:
                raise ValueError(f"旧入口发生变化，保留原样：{path}")
            plan.add(path, existing, restored)
        backups[platform] = receipt
    for platform, path in legacy_paths.items():
        if platform not in selected:
            continue
        inside(path, local.home)
        data = read(path)
        if path in plan.changes or data is None:
            continue
        if platform == "kiro" or MARKER in data or END in data:
            raise ValueError(f"检测到归属未确认的 V2 入口，先检查旧回执：{path}")
    if backups != previous:
        plan.add(target, read(target), encode(backups))
