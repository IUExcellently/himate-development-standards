"""合成 Git 仓库和独立用户目录。"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from git_access import SOURCE_URL
from detect_project import MANIFEST
from release import allowed


def git(cwd, *args):
    return subprocess.check_output(
        ["git", "-c", "core.hooksPath=" + os.devnull, "-C", str(cwd), *args],
        stderr=subprocess.PIPE, timeout=10,
    ).decode().strip()


def init(repo):
    repo.mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Test Author")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "core.autocrlf", "false")


def commit(repo):
    git(repo, "add", "--all")
    git(repo, "commit", "-qm", "test fixture")
    return git(repo, "rev-parse", "HEAD")


def project(repo, signatures=True):
    init(repo)
    for name, markers in MANIFEST["project"]["signatures"].items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(markers if signatures else ["other"]), encoding="utf-8")
    (repo / ".trellis").mkdir()
    (repo / ".trellis" / "workflow.md").write_text("untouched", encoding="utf-8")
    commit(repo)
    return repo


def source(repo):
    init(repo)
    git(repo, "remote", "add", "origin", SOURCE_URL)
    for folder in ("standards", "references", "scripts", "integrations"):
        for path in (ROOT / folder).rglob("*"):
            name = path.relative_to(ROOT).as_posix()
            if path.is_file() and allowed(name):
                target = repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
    for name in ("manifest.json", "SKILL.md"):
        (repo / name).write_bytes((ROOT / name).read_bytes())
    return commit(repo)


def bump(repo, version):
    p = repo / "manifest.json"
    obj = json.loads(p.read_bytes())
    obj["version"] = version
    p.write_text(json.dumps(obj), encoding="utf-8")
    return commit(repo)
