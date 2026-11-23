"""只读记录 Git 状态和工作树内容，包含忽略文件。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess


def git(root, *args):
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"}
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        env.pop(key, None)
    return subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false",
         "-C", str(root), *args], env=env, timeout=20,
    )


def digest_file(path):
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def capture(root):
    root = Path(root).resolve(strict=True)
    if Path(os.fsdecode(git(root, "rev-parse", "--show-toplevel")).rstrip("\n")) != root:
        raise ValueError("快照路径必须是工作树根")
    tracked = set(os.fsdecode(git(root, "ls-files", "-z")).rstrip("\0").split("\0"))
    ai = {".codex", ".claude", ".kiro", ".qoder", ".trellis", ".cairn",
          ".cursor", ".agents", ".github", "AGENTS.md", "CLAUDE.md", "KIRO.md"}
    entries = {}
    stack = [root]
    while stack:
        for path in stack.pop().iterdir():
            rel = path.relative_to(root).as_posix()
            if path.name == ".git":
                continue
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                value = ["link", os.readlink(path)]
            elif stat.S_ISDIR(info.st_mode):
                stack.append(path)
                value = ["dir"]
            elif stat.S_ISREG(info.st_mode):
                value = ["file", digest_file(path)]
            else:
                value = ["special"]
            group = "tracked" if rel in tracked else "untracked_or_ignored"
            entries[rel] = [group, rel.split("/")[0] in ai, stat.S_IMODE(info.st_mode), *value]
    git_dir = Path(os.fsdecode(git(root, "rev-parse", "--absolute-git-dir")).rstrip("\n"))
    metadata = {}
    for name in ("HEAD", "index", "config", "config.worktree"):
        path = git_dir / name
        if path.is_file():
            metadata[name] = digest_file(path)
    return {
        "root": str(root),
        "head": git(root, "rev-parse", "HEAD").decode().strip(),
        "status": os.fsdecode(git(root, "status", "--porcelain=v2", "--branch", "-z", "--untracked-files=all")),
        "git_metadata": metadata,
        "entries": entries,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()
    print(json.dumps(capture(args.root), ensure_ascii=True, sort_keys=True))
