"""预演、原子文件提交和可恢复的多文件操作。"""
import base64
from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

from integrations import PLATFORMS, entry, legacy_targets
from local_state import MAX_FILE, NAME, digest, encode, inside, parent_handle, read, regular_fd, write_file
from release import allowed

JOURNAL_LIMIT = 16 * 1024 * 1024


@dataclass(frozen=True)
class Change:
    path: Path
    before: bytes | None
    after: bytes | None
    mode: int | None = None


def guard(local, path, migration=False):
    inside(path, local.home)
    fixed = {local.registry, local.receipt, local.state / "legacy-backup.json"}
    fixed.update(entry(local, p) for p in PLATFORMS)
    if path in fixed or migration and path in legacy_targets(local).values():
        return
    releases = local.state / "releases"
    if releases in path.parents:
        version, folder, *parts = path.relative_to(releases).parts
        if re.fullmatch(r"[0-9a-f]{40}", version) and folder == NAME:
            name = PurePosixPath(*parts).as_posix()
            if name == "bundle.json" or allowed(name):
                return
    raise ValueError(f"不是受管理的落点：{path}")


class Plan:
    def __init__(self, local, migration=False):
        self.local = local
        self.migration = migration
        self.changes = {}
        self.conflicts = []
        self.journal_cleared = False

    def add(self, path, before, after):
        guard(self.local, path, self.migration)
        if after is not None and len(after) > MAX_FILE:
            raise ValueError(f"写入内容超过后续读取的大小限制：{path}")
        old = self.changes.get(path)
        if old is not None:
            if old.after != before:
                raise ValueError(f"多项操作的预期状态冲突：{path}")
            before = old.before
        if before != after:
            mode = stat.S_IMODE(path.stat().st_mode) if before is not None else None
            self.changes[path] = Change(path, before, after, mode)
        else:
            self.changes.pop(path, None)

    def summary(self, applied=False):
        return {
            "applied": applied or self.journal_cleared,
            "changes": [{
                "path": str(c.path),
                "action": "create" if c.before is None else "delete" if c.after is None else "modify",
                "before_sha256": digest(c.before), "after_sha256": digest(c.after),
            } for c in self.changes.values()],
            "conflicts": self.conflicts,
            "backup": "写入前在私有状态目录保存恢复日志" if self.changes else None,
            "rollback": "recover 可处理未完成事务，rollback 可切换保留的发行版本" if self.changes else None,
            "requires_apply": bool(self.changes) and not applied,
        }


def packed(value):
    return None if value is None else base64.b64encode(value).decode("ascii")


def unpacked(value):
    return None if value is None else base64.b64decode(value, validate=True)


def save_journal(plan):
    local = plan.local
    rows = [{"path": str(c.path.relative_to(local.home)), "mode": c.mode,
             "before": packed(c.before), "after": packed(c.after)}
            for c in plan.changes.values()]
    payload = encode({"schema": 1, "migration": plan.migration, "changes": rows})
    if len(payload) > JOURNAL_LIMIT:
        raise ValueError("恢复日志超过大小限制")
    inside(local.journal, local.home)
    write_file(local.journal, None, payload, home=local.home)
    return payload


def journal_changes(local):
    inside(local.journal, local.home)
    raw = read(local.journal, limit=JOURNAL_LIMIT)
    if raw is None:
        return None, []
    journal = json.loads(raw)
    if journal["schema"] != 1 or type(journal["migration"]) is not bool:
        raise ValueError("恢复日志格式无效")
    changes = []
    seen = set()
    for row in journal["changes"]:
        path = local.home / Path(row["path"])
        guard(local, path, journal["migration"])
        if path in seen:
            raise ValueError("恢复日志包含重复路径")
        seen.add(path)
        changes.append(Change(path, unpacked(row["before"]), unpacked(row["after"]), row["mode"]))
    return raw, changes


def is_legacy_document(local, path):
    locations = legacy_targets(local)
    return path in (locations["codex"], locations["claude"])


def replace_change(local, change, migration, reverse=False):
    guard(local, change.path, migration)
    before, after = (change.after, change.before) if reverse else (change.before, change.after)
    if migration and is_legacy_document(local, change.path) and before is not None and after is not None:
        # 保留 V2 的原有用户指令、inode 和 ACL。只处理已验证的尾部。
        if not before.startswith(after) and not after.startswith(before):
            raise ValueError("全局指令变更不属于尾部追加段")
        with parent_handle(change.path, local.home) as parent:
            fd = regular_fd(change.path, os.O_RDWR, parent=parent)
            with os.fdopen(fd, "r+b") as stream:
                if stream.read(len(before) + 1) != before:
                    raise ValueError(f"全局指令已变化：{change.path}")
                offset = min(len(before), len(after))
                stream.seek(offset)
                stream.write(after[offset:])
                stream.truncate()
                stream.flush()
                os.fsync(stream.fileno())
        return
    # 进程中断可留下暂存文件。把它隔离于 Skill 入口和不可变发行目录之外。
    write_file(change.path, before, after, change.mode, home=local.home,
               stage_dir=local.state / "staging")


def clear_journal(local, expected):
    with parent_handle(local.journal, local.home) as parent:
        if read(local.journal, limit=JOURNAL_LIMIT, parent=parent) != expected:
            raise ValueError("恢复日志发生变化")
        leaf = local.journal if parent is None else local.journal.name
        os.unlink(leaf, dir_fd=parent)


def recover(local, apply):
    raw, changes = journal_changes(local)
    plan = Plan(local)
    if raw is None:
        return plan
    migration = json.loads(raw)["migration"]
    plan.migration = migration
    pending = []
    for change in reversed(changes):
        current = read(change.path)
        if current == change.before:
            continue
        if current != change.after:
            partial = (migration and is_legacy_document(local, change.path)
                       and current is not None and change.before is not None and change.after is not None
                       and change.before.startswith(current) and current.startswith(change.after))
            if not partial:
                plan.conflicts.append(f"恢复时遇到外部变更：{change.path}")
                continue
            change = Change(change.path, change.before, current, change.mode)
        plan.add(change.path, current, change.before)
        pending.append(change)
    if apply and not plan.conflicts:
        for change in pending:
            replace_change(local, change, migration, reverse=True)
        clear_journal(local, raw)
        plan.journal_cleared = True
    return plan


def apply_plan(plan):
    if plan.conflicts or not plan.changes:
        return
    raw = save_journal(plan)
    try:
        for change in plan.changes.values():
            replace_change(plan.local, change, plan.migration)
    except Exception:
        recover(plan.local, True)
        raise
    clear_journal(plan.local, raw)
