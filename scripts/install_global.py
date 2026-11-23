"""安装独立入口，维护备份和回执，拒绝覆盖未知变更。"""
import argparse
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

from detect_project import MANIFEST, ROOT

NAME = "himate-development-standards"
PLATFORMS = ("codex", "claude", "kiro", "qoder")
STATE = ROOT / ".install-state"
HOME = Path.home().resolve()


def digest(data):
    return None if data is None else hashlib.sha256(data).hexdigest()


def entries(platform):
    prefix = ROOT / "integrations" / platform
    if platform == "codex":
        codex = Path(os.environ.get("CODEX_HOME", str(HOME / ".codex"))).expanduser()
        if not codex.is_absolute() or HOME not in codex.parents:
            raise ValueError("CODEX_HOME 必须位于当前用户目录内")
        if (codex / "AGENTS.override.md").exists():
            raise ValueError("已存在 Codex AGENTS.override.md，需核对有效入口")
        return [(HOME / ".agents" / "skills" / NAME / "SKILL.md", prefix / "SKILL.md", False),
                (codex / "AGENTS.md", prefix / "AGENTS.fragment.md", True)]
    if platform == "claude":
        claude = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(HOME / ".claude"))).expanduser()
        if not claude.is_absolute() or HOME not in claude.parents:
            raise ValueError("CLAUDE_CONFIG_DIR 必须位于当前用户目录内")
        return [(claude / "skills" / NAME / "SKILL.md", prefix / "SKILL.md", False),
                (claude / "CLAUDE.md", prefix / "CLAUDE.fragment.md", True)]
    if platform == "kiro":
        return [(HOME / ".kiro" / "steering" / f"{NAME}.md", prefix / f"{NAME}.md", False)]
    return [(HOME / ".qoder" / "skills" / NAME / "SKILL.md", prefix / "SKILL.md", False)]


def safe_path(path, boundary):
    if not path.is_absolute() or boundary not in path.parents or path.resolve() != path:
        raise ValueError(f"路径跳转或越界：{path}")
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(f"拒绝通过链接写入：{item}")
        if item == boundary:
            break
    for raw in MANIFEST["project"]["roots"]:
        repo = Path(raw)
        if path == repo or repo in path.parents or path in repo.parents:
            raise ValueError(f"路径与受保护仓库重叠：{path}")


def current(path):
    if not path.exists():
        return None, None
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError(f"需要单链接普通文件：{path}")
    return path.read_bytes(), stat.S_IMODE(info.st_mode)


def atomic(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        stage = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.chmod(stage, mode)
            os.replace(stage, path)
        finally:
            stage.unlink(missing_ok=True)


def replace_content(path, payload, previous, mode):
    if previous is None or ROOT in path.parents:
        atomic(path, payload, mode)
        return
    # 现有用户指令保留原 inode、ACL 与扩展属性；安装仅追加，撤销仅截断。
    with path.open("r+b") as stream:
        if stream.read() != previous:
            raise ValueError(f"用户入口在写入前已变化：{path}")
        try:
            common = os.path.commonprefix((previous, payload))
            stream.seek(len(common))
            stream.write(payload[len(common):])
            stream.truncate()
            stream.flush()
            os.fsync(stream.fileno())
        except OSError:
            stream.seek(0)
            stream.write(previous)
            stream.truncate()
            stream.flush()
            os.fsync(stream.fileno())
            raise


def load_receipt(platform):
    path = STATE / f"{platform}.json"
    safe_path(path, ROOT)
    data, _ = current(path)
    return json.loads(data) if data is not None else {"files": {}, "installed": False}


def build_plan(platform, uninstall):
    receipt = load_receipt(platform)
    plan = []
    next_files = {}
    known = {str(dest) for dest, _, _ in entries(platform)}
    if set(receipt["files"]) - known:
        raise ValueError(f"{platform} 的配置目录发生变化，先恢复安装时的配置目录")
    for dest, source, append in entries(platform):
        safe_path(dest, HOME)
        safe_path(source, ROOT)
        old, old_mode = current(dest)
        record = receipt["files"].get(str(dest))
        if record and digest(old) != record["installed_sha256"]:
            raise ValueError(f"入口安装后已变化，已保留：{dest}")
        if uninstall and not record:
            continue
        if record and record["original"] is not None:
            original = base64.b64decode(record["original"], validate=True)
        else:
            original = old if not record else None
        original_mode = record["original_mode"] if record else old_mode
        if uninstall:
            payload, mode = original, original_mode
        else:
            adapter = source.read_bytes()
            if append:
                if original and b"BEGIN HIMATE DEVELOPMENT STANDARDS" in original:
                    raise ValueError(f"已有未知 HiMate 配置段：{dest}")
                if original is None:
                    payload = adapter
                else:
                    # 保留原文件字节，并让片段沿用其换行风格。
                    newline = b"\r\n" if b"\r\n" in original else b"\n"
                    payload = original + newline * 2 + adapter.replace(b"\n", newline)
            else:
                if original is not None:
                    raise ValueError(f"已存在同名入口：{dest}")
                payload = adapter
            mode = original_mode if original_mode is not None else 0o600
            next_files[str(dest)] = {
                "original": None if original is None else base64.b64encode(original).decode("ascii"),
                "original_mode": original_mode, "installed_sha256": digest(payload),
            }
        if (old, old_mode) != (payload, mode):
            plan.append((dest, old, old_mode, payload, mode))
    updated = {"files": next_files, "installed": not uninstall}
    receipt_path = STATE / f"{platform}.json"
    if receipt != updated and (next_files or receipt["files"]):
        previous, previous_mode = current(receipt_path)
        data = (json.dumps(updated, ensure_ascii=False, indent=2) + "\n").encode()
        # 原始字节单独备份，回执即使在卸载后也可核对。
        if uninstall:
            backup = STATE / f"{platform}.last-install.json"
            safe_path(backup, ROOT)
            backup_old, backup_mode = current(backup)
            plan.append((backup, backup_old, backup_mode, previous, 0o600))
        if not uninstall and not receipt["installed"]:
            backup = STATE / f"{platform}.pre-install.json"
            safe_path(backup, ROOT)
            backup_old, backup_mode = current(backup)
            snapshot = {name: {k: info[k] for k in ("original", "original_mode")}
                        for name, info in next_files.items()}
            backup_data = (json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n").encode()
            plan.insert(0, (backup, backup_old, backup_mode, backup_data, 0o600))
        plan.append((receipt_path, previous, previous_mode, data, 0o600))
    return plan


@contextmanager
def install_lock():
    lock = STATE / "lock"
    safe_path(lock, ROOT)
    STATE.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "rb") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def apply(plan):
    done = []
    try:
        for dest, old, old_mode, payload, mode in plan:
            safe_path(dest, ROOT if ROOT in dest.parents else HOME)
            if current(dest) != (old, old_mode):
                raise ValueError(f"写入前内容已变化：{dest}")
            if payload is None:
                dest.unlink()
            else:
                replace_content(dest, payload, old, mode)
            done.append((dest, old, old_mode, payload, mode))
    except (OSError, ValueError):
        for dest, old, old_mode, payload, mode in reversed(done):
            if current(dest) != (payload, mode):
                continue
            if old is None:
                dest.unlink()
            else:
                replace_content(dest, old, payload, old_mode)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", action="append", choices=PLATFORMS)
    parser.add_argument("--uninstall", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    platforms = args.platform or PLATFORMS

    def make_plan():
        return [row for platform in dict.fromkeys(platforms)
                for row in build_plan(platform, args.uninstall)]

    try:
        if args.apply:
            with install_lock():
                plan = make_plan()
                apply(plan)
        else:
            plan = make_plan()
        print(json.dumps({"applied": args.apply, "uninstall": args.uninstall,
                          "paths": [str(row[0]) for row in plan]}, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"安装操作中止：{exc}\n")
