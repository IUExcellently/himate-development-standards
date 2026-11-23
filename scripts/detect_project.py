"""先查私有登记，再验证真实 Git 根和公开结构指纹。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

if __name__ == "__main__":
    sys.dont_write_bytecode = True

from git_access import git_root
from local_state import Local, ROOT

MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def verify_root(root):
    if git_root(root) != root:
        return "different-git-root"
    for name, markers in MANIFEST["project"]["signatures"].items():
        path = (root / name).resolve(strict=True)
        if root not in path.parents or not path.is_file():
            return "signature-outside-root"
        with path.open(encoding="utf-8") as stream:
            body = stream.read(256 * 1024)
        if not all(marker in body for marker in markers):
            return f"signature-mismatch:{name}"
    return None


def detect(cwd, local=None):
    result = {"active": False, "root": None}
    try:
        here = Path(cwd).expanduser().resolve(strict=True)
        if not here.is_dir():
            return dict(result, reason="cwd-not-directory")
        roots = [Path(p) for p in (local or Local()).registrations()["roots"]]
        candidates = [p for p in roots if p == here or p in here.parents]
        if not candidates:
            return dict(result, reason="unregistered-location")
        registered = max(candidates, key=lambda p: len(p.parts))
        if git_root(here) != registered:
            return dict(result, reason="different-git-root")
        problem = verify_root(registered)
        if problem:
            return dict(result, reason=problem)
        return {"active": True, "root": str(registered), "reason": "git-root-and-signatures"}
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        return dict(result, reason="workspace-unavailable")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--home", help="独立的测试用户目录")
    args = parser.parse_args()
    print(json.dumps(detect(args.cwd, Local(args.home))))
